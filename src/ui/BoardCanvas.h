#pragma once

#include "domain/BoardDocument.h"
#include <QPointF>
#include <QSet>
#include <QWidget>

namespace pt {

class BoardCanvas final : public QWidget {
    Q_OBJECT
public:
    explicit BoardCanvas(QWidget* parent = nullptr);
    bool gridVisible() const { return m_gridVisible; }
    qreal zoom() const { return m_zoom; }
    void setGridVisible(bool visible);
    void zoomIn();
    void zoomOut();
    void centerView();
    void resetView();
    void setDocument(std::shared_ptr<const BoardDocument> document);
    const BoardDocument* document() const { return m_document.get(); }
    void setLayerVisible(int layer, bool visible);
    bool layerVisible(int layer) const { return m_visibleLayers.contains(layer); }
    QPointF boardToScreen(const QPointF& point) const;

signals:
    void legacyMenuRequested(const QString& key);
    void viewChanged();

protected:
    void paintEvent(QPaintEvent* event) override;
    void keyPressEvent(QKeyEvent* event) override;
    void wheelEvent(QWheelEvent* event) override;
    void mousePressEvent(QMouseEvent* event) override;
    void mouseMoveEvent(QMouseEvent* event) override;
    void mouseReleaseEvent(QMouseEvent* event) override;
    void resizeEvent(QResizeEvent* event) override;

private:
    qreal baseScale() const;
    void zoomAt(qreal factor, const QPointF& anchor);
    bool m_gridVisible = true;
    bool m_panning = false;
    qreal m_zoom = 1.0;
    QPointF m_pan;
    QPointF m_lastMouse;
    std::shared_ptr<const BoardDocument> m_document;
    QSet<int> m_visibleLayers;
    QRectF m_boardBounds;
};

}
