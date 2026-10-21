#pragma once

#include "geometry/BoardGeometry.h"
#include "domain/Measurement.h"
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
    QPointF screenToBoard(const QPointF& point) const;
    std::optional<PrimitiveId> selection() const { return m_selection; }
    qsizetype overlapCount() const { return m_hits.size(); }
    qsizetype overlapPosition() const { return m_hitPosition; }
    void clearSelection();
    void selectNextOverlap();
    bool focusComponent(qsizetype index);
    std::optional<qsizetype> focusedComponent() const { return m_focusedComponent; }
    void centerOn(const QPointF& position);
    void setMeasurementMode(bool enabled);
    bool measurementMode() const { return m_measurementMode; }
    std::optional<Measurement> measurement() const { return m_measurement; }
    std::optional<QPointF> measurementStart() const { return m_measurementStart; }
    void clearMeasurement();

signals:
    void legacyMenuRequested(const QString& key);
    void viewChanged();
    void selectionChanged();
    void measurementChanged();

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
    BoardHitTester m_hitTester;
    std::optional<PrimitiveId> m_selection;
    QList<PrimitiveId> m_hits;
    qsizetype m_hitPosition = -1;
    std::optional<QPointF> m_lastPickScreen;
    std::optional<qsizetype> m_focusedComponent;
    QRectF m_componentBox;
    bool m_measurementMode=false;
    std::optional<QPointF> m_measurementStart;
    std::optional<Measurement> m_measurement;
};

}
