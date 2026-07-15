"""Qt OpenGL wireframe widget for parsed SKLT models."""

from __future__ import annotations

import math

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QWheelEvent
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from sklt_parser import Point3D, SkltModel


class WireframeViewer(QOpenGLWidget):
    """Read-only 3D wireframe view with rotate, zoom, and pan controls."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._model: SkltModel | None = None
        self._vertices: list[Point3D] = []
        self._edges: list[tuple[int, int]] = []
        self._last_mouse_pos = QPoint()
        self._yaw = -35.0
        self._pitch = 20.0
        self._zoom = 1.0
        self._pan = QPointF(0.0, 0.0)
        self._show_vertex_indices = False
        self._selected_index = -1
        self.setMinimumSize(520, 420)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_model(self, model: SkltModel) -> None:
        self._model = model
        self._vertices = self._center_and_normalize(model.points)
        self._edges = self._build_edges(model.polygons)
        self.reset_view()

    def set_points(self, points: list[Point3D]) -> None:
        self._vertices = self._center_and_normalize(points)
        self.update()

    def set_edges(self, polygons: list[list[int]]) -> None:
        self._edges = self._build_edges(polygons)
        self.update()

    def set_show_vertex_indices(self, enabled: bool) -> None:
        self._show_vertex_indices = enabled
        self.update()

    def set_selected_index(self, index: int) -> None:
        self._selected_index = index if 0 <= index < len(self._vertices) else -1
        self.update()

    def reset_view(self) -> None:
        self._yaw = -35.0
        self._pitch = 20.0
        self._zoom = 1.0
        self._pan = QPointF(0.0, 0.0)
        self.update()

    def paintGL(self) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(22, 25, 30))

        if not self._vertices or not self._edges:
            painter.setPen(QColor(180, 185, 192))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Load an SKLT/SKL file to display its wireframe.",
            )
            painter.end()
            return

        projected = [self._project(vertex) for vertex in self._vertices]
        painter.setPen(QPen(QColor(112, 210, 255), 1.25))

        for first, second in self._edges:
            painter.drawLine(projected[first], projected[second])

        if self._show_vertex_indices:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(210, 215, 220))
            for index, point in enumerate(projected):
                if index == self._selected_index:
                    continue
                painter.drawEllipse(point, 3.0, 3.0)

            if 0 <= self._selected_index < len(projected):
                painter.setBrush(QColor(255, 204, 70))
                painter.drawEllipse(projected[self._selected_index], 6.0, 6.0)

            painter.setPen(QColor(230, 230, 210))
            for index, point in enumerate(projected):
                painter.drawText(point + QPointF(6.0, -6.0), str(index))

        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._last_mouse_pos = event.position().toPoint()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        current = event.position().toPoint()
        delta = current - self._last_mouse_pos
        self._last_mouse_pos = current

        if event.buttons() & Qt.MouseButton.LeftButton:
            self._yaw += delta.x() * 0.6
            self._pitch += delta.y() * 0.6
            self._pitch = max(-89.0, min(89.0, self._pitch))
            self.update()
        elif event.buttons() & (
            Qt.MouseButton.RightButton | Qt.MouseButton.MiddleButton
        ):
            self._pan += QPointF(delta.x(), delta.y())
            self.update()

        event.accept()

    def wheelEvent(self, event: QWheelEvent) -> None:
        zoom_factor = math.pow(1.0015, event.angleDelta().y())
        self._zoom = max(0.08, min(25.0, self._zoom * zoom_factor))
        self.update()
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self.reset_view()
        event.accept()

    def _project(self, vertex: Point3D) -> QPointF:
        x, y, z = vertex

        yaw = math.radians(self._yaw)
        pitch = math.radians(self._pitch)

        yaw_x = x * math.cos(yaw) + z * math.sin(yaw)
        yaw_z = -x * math.sin(yaw) + z * math.cos(yaw)
        pitch_y = y * math.cos(pitch) - yaw_z * math.sin(pitch)
        pitch_z = y * math.sin(pitch) + yaw_z * math.cos(pitch)

        camera_distance = 4.0
        denominator = max(0.2, camera_distance - pitch_z)
        focal_length = min(self.width(), self.height()) * 1.65 * self._zoom

        screen_x = self.width() * 0.5 + self._pan.x() + yaw_x * focal_length / denominator
        screen_y = self.height() * 0.5 + self._pan.y() - pitch_y * focal_length / denominator
        return QPointF(screen_x, screen_y)

    @staticmethod
    def _center_and_normalize(points: list[Point3D]) -> list[Point3D]:
        if not points:
            return []

        minimum = [min(point[axis] for point in points) for axis in range(3)]
        maximum = [max(point[axis] for point in points) for axis in range(3)]
        center = [(minimum[axis] + maximum[axis]) * 0.5 for axis in range(3)]
        largest_extent = max(maximum[axis] - minimum[axis] for axis in range(3))
        scale = 2.0 / largest_extent if largest_extent > 0.0 else 1.0

        return [
            (
                (point[0] - center[0]) * scale,
                # UA model space commonly uses negative Y as "up".
                # Flip only in the viewer so saved POO2 data stays untouched.
                -(point[1] - center[1]) * scale,
                (point[2] - center[2]) * scale,
            )
            for point in points
        ]

    @staticmethod
    def _build_edges(polygons: list[list[int]]) -> list[tuple[int, int]]:
        edges: list[tuple[int, int]] = []
        seen: set[tuple[int, int]] = set()

        for polygon in polygons:
            pairs = list(zip(polygon, polygon[1:]))
            if len(polygon) > 2:
                pairs.append((polygon[-1], polygon[0]))

            for first, second in pairs:
                edge_key = (min(first, second), max(first, second))
                if first != second and edge_key not in seen:
                    seen.add(edge_key)
                    edges.append((first, second))

        return edges
