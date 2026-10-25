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
    m_netPads.clear();
    m_panning=false;
    m_hitTester.setDocument(m_document);
    m_snapIndex.setDocument(m_document.get());
    m_measurementSnap = false;
    clearSnapPreview();
    setMouseTracking(false);
    clearSelection();
    m_measurementMode=false;
    setCursor(Qt::ArrowCursor);
    clearMeasurement();
    m_boardBounds = m_document ? m_document->bounds() : QRectF();
    resetView();
}

void BoardCanvas::setNetPads(const QList<qsizetype>& pads) {
    m_netPads.clear();QSet<qsizetype> seen;
    if (m_document) for (const auto index:pads) if (index>=0 && index<m_document->pads.size() && !seen.contains(index)) {
        seen.insert(index);m_netPads.append(index);
    }
    update();
}

bool BoardCanvas::focusPrimitive(PrimitiveId id) {
    if (!m_document || primitiveLayer(*m_document,id)==0) return false;
    const auto bounds=primitiveBounds(*m_document,id);
    if (!bounds.isValid()) return false;
    setMeasurementMode(false);clearSelection();
    centerOn(bounds.center());
    m_selection=id;update();emit selectionChanged();return true;
}

bool BoardCanvas::focusPad(qsizetype index) {
    return focusPrimitive({PrimitiveKind::Pad,index});
}

void BoardCanvas::setLayerVisible(int layer, bool visible) {
    clearSnapPreview();
    if (visible) m_visibleLayers.insert(layer); else m_visibleLayers.remove(layer);
    if (m_selection && m_document && !visible && primitiveLayer(*m_document,*m_selection)==layer) {
        clearSelection();
    } else {
        // 图层集合改变后，旧的重叠候选列表不再可靠。
        m_hits.clear(); m_hitPosition=-1; m_lastPickScreen.reset();
        emit selectionChanged();
    }
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

QPointF BoardCanvas::screenToBoard(const QPointF& point) const {
    const qreal scale=baseScale()*m_zoom;
    const QPointF delta=point-QPointF(rect().center())-m_pan;
    return (m_document?m_boardBounds.center():QPointF())+QPointF(delta.x()/scale,-delta.y()/scale);
}

void BoardCanvas::clearSelection() {
    m_selection.reset(); m_hits.clear(); m_hitPosition=-1; m_lastPickScreen.reset();
    m_focusedComponent.reset(); m_componentBox={};
    update();
    emit selectionChanged();
}

void BoardCanvas::selectNextOverlap() {
    if (!m_document || m_hits.isEmpty()) return;
    m_hitPosition=(m_hitPosition+1)%m_hits.size();
    m_selection=m_hits[m_hitPosition];
    update(); emit selectionChanged();
}

void BoardCanvas::centerOn(const QPointF& position) {
    clearSnapPreview();
    if (!std::isfinite(position.x()) || !std::isfinite(position.y())) return;
    const auto center=m_document?m_boardBounds.center():QPointF();
    const qreal scale=baseScale()*m_zoom;
    m_pan=QPointF((center.x()-position.x())*scale,(position.y()-center.y())*scale);
    m_lastPickScreen.reset();
    update(); emit viewChanged();
}

bool BoardCanvas::focusComponent(qsizetype index) {
    if (!m_document || index<0 || index>=m_document->components.size()) return false;
    setMeasurementMode(false);
    clearSelection();
    m_componentBox=componentBounds(*m_document,index);
    m_focusedComponent=index;
    const qreal fit=qMin(qMax(1,width()-100)/qMax(1.0,m_componentBox.width()),
                        qMax(1,height()-100)/qMax(1.0,m_componentBox.height()));
    m_zoom=std::clamp(fit/baseScale(),0.125,16.0);
    centerOn(m_componentBox.center());
    emit selectionChanged();
    return true;
}

void BoardCanvas::setMeasurementMode(bool enabled) {
    m_measurementMode=enabled && m_document!=nullptr;
    m_measurementStart.reset();
    m_startAnchor.reset();
    clearSnapPreview();
    setMouseTracking(m_measurementMode && m_measurementSnap);
    if (m_measurementMode) clearSelection();
    setCursor(m_measurementMode?Qt::CrossCursor:Qt::ArrowCursor);
    update(); emit measurementChanged();
}

void BoardCanvas::clearMeasurement() {
    m_measurementStart.reset(); m_measurement.reset(); m_startAnchor.reset();
    clearSnapPreview();
    update(); emit measurementChanged();
}

void BoardCanvas::setMeasurementSnapEnabled(bool enabled) {
    m_measurementSnap = enabled && m_document != nullptr;
    clearSnapPreview();
    setMouseTracking(m_measurementMode && m_measurementSnap);
    update(); emit measurementChanged();
}

std::optional<SnapPoint> BoardCanvas::measurementSnapAt(const QPointF& screen) const {
    if (!m_measurementMode || !m_measurementSnap || !m_document) return {};
    // 捕捉半径保持为10个逻辑像素，不随缩放改变屏幕操作距离。
    return m_snapIndex.nearest(screenToBoard(screen), 10.0 / (baseScale() * m_zoom), m_visibleLayers);
}

void BoardCanvas::clearSnapPreview() {
    if (m_snapPreview) { m_snapPreview.reset(); update(); }
}

void BoardCanvas::leaveEvent(QEvent* event) {
    clearSnapPreview();
    QWidget::leaveEvent(event);
}

void BoardCanvas::resizeEvent(QResizeEvent* event) {
    clearSnapPreview();
    if (m_document && event->oldSize().isValid()) {
        const qreal previous=qMin(qMax(1,event->oldSize().width()-80)/qMax(1.0,m_boardBounds.width()),
                                  qMax(1,event->oldSize().height()-100)/qMax(1.0,m_boardBounds.height()));
        if (previous>0) m_pan*=baseScale()/previous;
    }
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
    clearSnapPreview();
    m_pan = {};
    update();
    emit viewChanged();
}

void BoardCanvas::resetView() {
    m_zoom = 1.0;
    centerView();
}

void BoardCanvas::zoomAt(qreal factor, const QPointF& anchor) {
    clearSnapPreview();
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
        if (!m_netPads.isEmpty()) {
            QPen netPen(QColor(100,240,220));netPen.setCosmetic(true);netPen.setWidthF(2);
            painter.setPen(netPen);painter.setBrush(Qt::NoBrush);
            for (const auto index:m_netPads) if (m_visibleLayers.contains(m_document->pads[index].layer)) painter.drawPath(padOutline(m_document->pads[index]));
        }
        if (m_selection && m_visibleLayers.contains(primitiveLayer(*m_document,*m_selection))) {
            painter.setBrush(Qt::NoBrush);
            QPen pen(QColor(250,250,250)); pen.setWidthF(2); pen.setCosmetic(true); pen.setStyle(Qt::DashLine);
            painter.setPen(pen);
            painter.drawPath(primitiveOutline(*m_document,*m_selection));
        }
        if (m_focusedComponent) {
            QPen pen(QColor(250,250,250)); pen.setCosmetic(true); pen.setWidthF(2); pen.setStyle(Qt::DashLine);
            painter.setPen(pen); painter.setBrush(Qt::NoBrush); painter.drawRect(m_componentBox);
        }
        painter.restore();
        // 测量覆盖层在屏幕坐标中绘制，线宽和端点标记不随缩放增粗。
        if (m_measurement) {
            painter.setPen(QPen(QColor(120,235,215),2,Qt::DashLine));
            const QPointF a=boardToScreen(m_measurement->start), b=boardToScreen(m_measurement->end);
            painter.drawLine(a,b);
            for (const auto& p : {a,b}) {
                painter.drawLine(p-QPointF(5,0),p+QPointF(5,0));
                painter.drawLine(p-QPointF(0,5),p+QPointF(0,5));
            }
        }
        if (m_measurementStart) {
            painter.setPen(QPen(QColor(120,235,215),2));
            const auto p=boardToScreen(*m_measurementStart);
            painter.drawEllipse(p,5,5);
        }
        if (m_snapPreview) {
            painter.setPen(QPen(QColor(255, 218, 90), 2));
            painter.setBrush(Qt::NoBrush);
            const auto point = boardToScreen(m_snapPreview->position);
            painter.drawRect(QRectF(point - QPointF(6, 6), QSizeF(12, 12)));
        }
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
        QStringLiteral("第十阶段：只读测量与几何端点捕捉\n"
                       "Ctrl+O 板图；网络菜单载入 NET，再运行几何分析。不是完整 DRC 或制造验收。\n"
                       "画布内按 F/P/N 等唤出菜单；滚轮缩放，中键拖动，Esc 返回工作区。"));
}

void BoardCanvas::keyPressEvent(QKeyEvent* event) {
    if (m_measurementMode && event->key()==Qt::Key_Escape && event->modifiers()==Qt::NoModifier) {
        setMeasurementMode(false); event->accept(); return;
    }
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
    if (event->button()==Qt::LeftButton && m_document) {
        if (m_measurementMode) {
            const auto snap = measurementSnapAt(event->position());
            const auto position = snap ? snap->position : screenToBoard(event->position());
            const auto anchor = snap ? std::optional<PrimitiveId>(snap->primitive) : std::nullopt;
            clearSnapPreview();
            if (m_measurementStart) {
                m_measurement=Measurement{*m_measurementStart,position,m_startAnchor,anchor};
                m_measurementStart.reset(); m_startAnchor.reset();
            } else {
                m_measurement.reset(); m_measurementStart=position; m_startAnchor=anchor;
            }
            update(); emit measurementChanged(); event->accept(); return;
        }
        m_focusedComponent.reset(); m_componentBox={};
        const auto hits=m_hitTester.hitTest(screenToBoard(event->position()),6.0/(baseScale()*m_zoom),m_visibleLayers);
        const bool samePlace=m_lastPickScreen && (event->position()-*m_lastPickScreen).manhattanLength()<=4;
        const bool cycle=samePlace && hits==m_hits && !hits.isEmpty() && m_hitPosition>=0;
        m_hits=hits;
        m_lastPickScreen=event->position();
        if (m_hits.isEmpty()) { clearSelection(); }
        else {
            m_hitPosition=cycle?(m_hitPosition+1)%m_hits.size():0;
            m_selection=m_hits[m_hitPosition];
            update(); emit selectionChanged();
        }
        event->accept(); return;
    }
    if (event->button() == Qt::MiddleButton) {
        clearSnapPreview();
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
    if (m_measurementMode && m_measurementSnap) {
        m_snapPreview = measurementSnapAt(event->position());
        update();
        event->accept();
        return;
    }
    QWidget::mouseMoveEvent(event);
}

void BoardCanvas::mouseReleaseEvent(QMouseEvent* event) {
    if (event->button() == Qt::MiddleButton && m_panning) {
        m_panning = false;
        setCursor(m_measurementMode?Qt::CrossCursor:Qt::ArrowCursor);
        event->accept();
        return;
    }
    QWidget::mouseReleaseEvent(event);
}

}
