#include "ui/BoardCanvas.h"

#include "application/CommandCatalog.h"
#include "ui/BoardRenderer.h"
#include <QResizeEvent>
#include <QKeyEvent>
#include <QMouseEvent>
#include <QPainter>
#include <QWheelEvent>
#include <algorithm>
#include <cmath>

namespace pt {

BoardCanvas::BoardCanvas(QWidget* parent) : QWidget(parent) {
    setObjectName(QStringLiteral("boardCanvas"));
    setFocusPolicy(Qt::StrongFocus);
    setMinimumSize(360, 280);
    setAccessibleName(QStringLiteral("板图工作区"));
    for (int layer = 1; layer <= 13; ++layer) m_visibleLayers.insert(layer);
}

void BoardCanvas::setDocument(std::shared_ptr<const BoardDocument> document) {
    m_document = std::move(document);
    m_boardBounds = m_document ? m_document->bounds() : QRectF();
    resetView();
}

void BoardCanvas::setLayerVisible(int layer, bool visible) {
    if (visible) m_visibleLayers.insert(layer); else m_visibleLayers.remove(layer);
    update();
}

qreal BoardCanvas::baseScale() const {
    if (!m_document) return 1.0;
    return qMin(qMax(1, width()-80) / qMax(1.0, m_boardBounds.width()),
                qMax(1, height()-100) / qMax(1.0, m_boardBounds.height()));
}

QPointF BoardCanvas::boardToScreen(const QPointF& point) const {
    const QPointF delta = point - (m_document ? m_boardBounds.center() : QPointF());
    const qreal scale = baseScale() * m_zoom;
    return QPointF(rect().center()) + m_pan + QPointF(delta.x()*scale, -delta.y()*scale);
}

void BoardCanvas::resizeEvent(QResizeEvent* event) {
    QWidget::resizeEvent(event);
    update();
}

void BoardCanvas::setGridVisible(bool visible) {
    m_gridVisible = visible;
    update();
    emit viewChanged();
}

void BoardCanvas::zoomIn() { zoomAt(1.25, rect().center()); }
void BoardCanvas::zoomOut() { zoomAt(0.8, rect().center()); }

void BoardCanvas::centerView() {
    m_pan = {};
    update();
    emit viewChanged();
}

void BoardCanvas::resetView() {
    m_zoom = 1.0;
    centerView();
}

void BoardCanvas::zoomAt(qreal factor, const QPointF& anchor) {
    const qreal next = std::clamp(m_zoom * factor, 0.125, 16.0);
    const QPointF center = rect().center();
    const QPointF origin = center + m_pan;
    m_pan = anchor + (origin - anchor) * (next / m_zoom) - center;
    m_zoom = next;
    update();
    emit viewChanged();
}

void BoardCanvas::paintEvent(QPaintEvent*) {
    QPainter painter(this);
    painter.fillRect(rect(), QColor(26, 30, 35));
    const QPointF origin = QPointF(rect().center()) + m_pan;
    if (m_gridVisible) {
        qreal spacing = (m_document ? 100.0 * baseScale() : 24.0) * m_zoom;
        while (spacing < 8.0) spacing *= 2.0;
        while (spacing > 64.0) spacing /= 2.0;
        const QPointF gridOrigin = m_document ? boardToScreen(QPointF()) : origin;
        painter.setPen(QColor(65, 72, 81));
        for (qreal x = std::fmod(gridOrigin.x(), spacing); x < width(); x += spacing) {
            for (qreal y = std::fmod(gridOrigin.y(), spacing); y < height(); y += spacing) {
                painter.drawPoint(QPointF(x, y));
            }
        }
    }
    painter.setPen(QColor(163, 173, 185));
    painter.drawLine(origin + QPointF(-12, 0), origin + QPointF(12, 0));
    painter.drawLine(origin + QPointF(0, -12), origin + QPointF(0, 12));
    if (m_document) {
        painter.save();
        painter.translate(QPointF(rect().center()) + m_pan);
        const qreal scale = baseScale() * m_zoom;
        painter.scale(scale, -scale);
        painter.translate(-m_boardBounds.center());
        drawBoard(painter, *m_document, m_visibleLayers);
        painter.restore();
        painter.setPen(QColor(214,220,229));
        painter.fillRect(QRect(8, 6, width()-16, 28), QColor(26,30,35,230));
        painter.drawText(QRect(16,6,width()-32,28), Qt::AlignVCenter,
            QStringLiteral("只读预览 · %1 个图元 · 文字与部分焊盘轮廓为近似显示 · 不可用于生产输出").arg(m_document->primitiveCount()));
        return;
    }
    const QRect banner(20, 20, std::max(100, width() - 40), 100);
    painter.fillRect(banner, QColor(26, 30, 35, 235));
    painter.setPen(QColor(214, 220, 229));
    painter.drawText(banner.adjusted(12, 10, -12, -10), Qt::TextWordWrap,
        QStringLiteral("第二阶段：PCB 只读预览\n"
                       "Ctrl+O 打开板图；支持基本图元与元件，尚不支持编辑或保存。\n"
                       "画布内按 F/P/N 等唤出菜单；滚轮缩放，中键拖动，Esc 返回工作区。"));
}

void BoardCanvas::keyPressEvent(QKeyEvent* event) {
    // 兼容字母只在画布焦点内生效，不截获文件名或属性编辑框输入。
    if (event->modifiers() == Qt::NoModifier) {
        if (event->key() == Qt::Key_PageUp) { zoomIn(); event->accept(); return; }
        if (event->key() == Qt::Key_PageDown) { zoomOut(); event->accept(); return; }
        if (event->key() >= Qt::Key_A && event->key() <= Qt::Key_Z) {
            const QString key(QChar(event->key()));
            for (const auto& menu : commandCatalog()) {
                if (menu.key == key) {
                    emit legacyMenuRequested(key);
                    event->accept();
                    return;
                }
            }
        }
    }
    QWidget::keyPressEvent(event);
}

void BoardCanvas::wheelEvent(QWheelEvent* event) {
    if (event->angleDelta().y() == 0) { event->ignore(); return; }
    zoomAt(std::pow(1.25, event->angleDelta().y() / 120.0), event->position());
    event->accept();
}

void BoardCanvas::mousePressEvent(QMouseEvent* event) {
    setFocus(Qt::MouseFocusReason);
    if (event->button() == Qt::MiddleButton) {
        m_panning = true;
        m_lastMouse = event->position();
        setCursor(Qt::ClosedHandCursor);
        event->accept();
        return;
    }
    QWidget::mousePressEvent(event);
}

void BoardCanvas::mouseMoveEvent(QMouseEvent* event) {
    if (m_panning) {
        m_pan += event->position() - m_lastMouse;
        m_lastMouse = event->position();
        update();
        event->accept();
        return;
    }
    QWidget::mouseMoveEvent(event);
}

void BoardCanvas::mouseReleaseEvent(QMouseEvent* event) {
    if (event->button() == Qt::MiddleButton && m_panning) {
        m_panning = false;
        unsetCursor();
        event->accept();
        return;
    }
    QWidget::mouseReleaseEvent(event);
}

}
