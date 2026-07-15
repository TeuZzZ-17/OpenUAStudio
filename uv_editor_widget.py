"""Mini UV editor V1: drag the OLPL points of one polygon over its texture.

Coordinate system: native amesh OLPL bytes, 0..255 on both axes (the runtime
divides by 256; for 256px textures one unit == one texel).  Dragging snaps
inherently to that byte grid.  Everything here is in-memory only — the widget
emits signals, it never touches disk.

Controls: left-drag moves the grabbed UV point; Ctrl constrains to one axis;
wheel zooms (1x..6x); middle/right-drag pans when zoomed; click selects a
point (for the numeric fields hosted by the window).
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

HANDLE_RADIUS = 6.0


class UVEditorWidget(QWidget):
    """Interactive texture overlay for a single polygon's UV points."""

    uvChanged = Signal(list)     # live during drag: [(u, v), ...]
    editFinished = Signal()      # drag released / numeric apply
    pointSelected = Signal(int)  # index of the active UV point (-1 = none)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(280, 280)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._image: QImage | None = None
        self._uvs: list[tuple[int, int]] = []
        self._message = "Select a mapped polygon to edit its UVs."
        self._editable = False
        self._active_point = -1
        self._dragging = False
        self._drag_axis: str | None = None
        self._drag_start_uv: tuple[int, int] | None = None
        self._zoom = 1.0
        self._pan = QPointF(0.0, 0.0)
        self._pan_last: QPoint | None = None

    # -- public API -----------------------------------------------------------

    def set_data(self, image: QImage | None, uvs: list[tuple[int, int]],
                 editable: bool, message: str = "") -> None:
        self._image = image
        self._uvs = [tuple(uv) for uv in uvs]
        self._editable = editable and bool(uvs)
        self._message = message
        self._active_point = -1 if not uvs else min(self._active_point, 0) \
            if self._active_point < 0 else min(self._active_point,
                                               len(uvs) - 1)
        self._dragging = False
        self.update()

    def uvs(self) -> list[tuple[int, int]]:
        return list(self._uvs)

    def active_point(self) -> int:
        return self._active_point

    def set_point(self, index: int, u: int, v: int,
                  notify: bool = True) -> None:
        if not (0 <= index < len(self._uvs)):
            return
        self._uvs[index] = (max(0, min(255, u)), max(0, min(255, v)))
        self.update()
        if notify:
            self.uvChanged.emit(self.uvs())

    def reset_view(self) -> None:
        self._zoom = 1.0
        self._pan = QPointF(0.0, 0.0)
        self.update()

    # -- geometry mapping -------------------------------------------------------

    def _canvas_rect(self) -> tuple[float, float, float]:
        """(origin_x, origin_y, size) of the square texture canvas."""

        size = min(self.width(), self.height()) - 8
        size = max(64, size) * self._zoom
        ox = (self.width() - size) / 2 + self._pan.x()
        oy = (self.height() - size) / 2 + self._pan.y()
        return ox, oy, size

    def _uv_to_screen(self, uv: tuple[int, int]) -> QPointF:
        ox, oy, size = self._canvas_rect()
        return QPointF(ox + uv[0] / 256.0 * size,
                       oy + uv[1] / 256.0 * size)

    def _screen_to_uv(self, point: QPointF) -> tuple[int, int]:
        ox, oy, size = self._canvas_rect()
        u = round((point.x() - ox) / size * 256.0)
        v = round((point.y() - oy) / size * 256.0)
        return max(0, min(255, u)), max(0, min(255, v))

    # -- painting ---------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(30, 32, 38))
        ox, oy, size = self._canvas_rect()

        # checkerboard backdrop (shows chroma-transparent texels)
        cell = size / 16
        for row in range(16):
            for col in range(16):
                light = (row + col) % 2 == 0
                painter.fillRect(
                    int(ox + col * cell), int(oy + row * cell),
                    int(cell) + 1, int(cell) + 1,
                    QColor(70, 72, 80) if light else QColor(54, 56, 62),
                )

        if self._image is not None and not self._image.isNull():
            painter.drawImage(
                int(ox), int(oy),
                self._image.scaled(int(size), int(size),
                                   Qt.AspectRatioMode.IgnoreAspectRatio,
                                   Qt.TransformationMode.FastTransformation),
            )

        if self._uvs:
            points = [self._uv_to_screen(uv) for uv in self._uvs]
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(255, 255, 90), 1.6))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPolygon(QPolygonF(points))
            for index, point in enumerate(points):
                active = index == self._active_point
                painter.setBrush(QColor(90, 230, 255) if active
                                 else QColor(255, 255, 90))
                painter.setPen(QPen(QColor(20, 20, 20), 1.0))
                painter.drawEllipse(point, HANDLE_RADIUS, HANDLE_RADIUS)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(point + QPointF(8, -6),
                                 f"{index} ({self._uvs[index][0]},"
                                 f"{self._uvs[index][1]})")

        if self._message:
            painter.setPen(QColor(255, 190, 120))
            painter.drawText(self.rect().adjusted(6, 4, -6, -4),
                             Qt.AlignmentFlag.AlignBottom
                             | Qt.AlignmentFlag.AlignLeft
                             | Qt.TextFlag.TextWordWrap,
                             self._message)
        if not self._editable and self._uvs:
            painter.setPen(QColor(200, 200, 200))
            painter.drawText(self.rect().adjusted(6, 4, -6, -4),
                             Qt.AlignmentFlag.AlignTop
                             | Qt.AlignmentFlag.AlignRight, "[READ-ONLY]")
        painter.end()

    # -- interaction --------------------------------------------------------------

    def _hit_point(self, pos: QPointF) -> int:
        for index, uv in enumerate(self._uvs):
            point = self._uv_to_screen(uv)
            if (point - pos).manhattanLength() <= HANDLE_RADIUS * 2:
                return index
        return -1

    def mousePressEvent(self, event) -> None:  # noqa: N802
        pos = event.position()
        if event.button() == Qt.MouseButton.LeftButton:
            hit = self._hit_point(pos)
            self._active_point = hit
            self.pointSelected.emit(hit)
            if hit >= 0 and self._editable:
                self._dragging = True
                self._drag_axis = None
                self._drag_start_uv = self._uvs[hit]
            self.update()
        elif event.button() in (Qt.MouseButton.MiddleButton,
                                Qt.MouseButton.RightButton):
            self._pan_last = event.position().toPoint()
        event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        pos = event.position()
        if self._dragging and self._active_point >= 0:
            u, v = self._screen_to_uv(pos)
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier \
                    and self._drag_start_uv is not None:
                du = abs(u - self._drag_start_uv[0])
                dv = abs(v - self._drag_start_uv[1])
                if self._drag_axis is None and (du > 2 or dv > 2):
                    self._drag_axis = "u" if du >= dv else "v"
                if self._drag_axis == "u":
                    v = self._drag_start_uv[1]
                elif self._drag_axis == "v":
                    u = self._drag_start_uv[0]
            self.set_point(self._active_point, u, v)
        elif self._pan_last is not None:
            delta = event.position().toPoint() - self._pan_last
            self._pan_last = event.position().toPoint()
            self._pan += QPointF(delta.x(), delta.y())
            self.update()
        event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self._dragging:
            self._dragging = False
            self._drag_axis = None
            self.editFinished.emit()
        self._pan_last = None
        event.accept()

    def wheelEvent(self, event) -> None:  # noqa: N802
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self._zoom = max(1.0, min(6.0, self._zoom * factor))
        if self._zoom == 1.0:
            self._pan = QPointF(0.0, 0.0)
        self.update()
        event.accept()
