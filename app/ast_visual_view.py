"""Графическое представление AST (PyQt6 QGraphicsScene / QGraphicsView)."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt6.QtWidgets import (
    QDialog,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QVBoxLayout,
    QWidget,
)

from ast_nodes import (
    AstNode,
    ConstDeclNode,
    FloatLiteralNode,
    ForStmtNode,
    IdentifierNode,
    IntLiteralNode,
    PrintStmtNode,
    ProgramNode,
    SimpleTypeNode,
    VarDeclNode,
)


class _AstGraphicsView(QGraphicsView):
    """Масштаб колёсиком мыши."""

    def wheelEvent(self, event):
        if event.angleDelta().y() == 0:
            super().wheelEvent(event)
            return
        factor = 1.12 if event.angleDelta().y() > 0 else 1 / 1.12
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.scale(factor, factor)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)


def _ast_children_ordered(node: AstNode) -> List[AstNode]:
    if isinstance(node, ProgramNode):
        return list(node.body)
    if isinstance(node, (ConstDeclNode, VarDeclNode)):
        out: List[AstNode] = []
        if node.type_node is not None:
            out.append(node.type_node)
        if node.value is not None:
            out.append(node.value)
        return out
    if isinstance(node, ForStmtNode):
        out = []
        if node.range_start is not None:
            out.append(node.range_start)
        if node.range_end is not None:
            out.append(node.range_end)
        out.extend(node.body)
        return out
    if isinstance(node, PrintStmtNode):
        if node.argument is not None:
            return [node.argument]
        return []
    return []


def _node_caption_lines(node: AstNode) -> List[str]:
    """Первая строка - тип узла далее атрибуты в виде key=valuе."""
    kind = node.__class__.__name__
    if isinstance(node, ProgramNode):
        return [kind, f"body_count={len(node.body)}"]
    if isinstance(node, ConstDeclNode):
        lines = [kind, f"name={node.name}", f"modifiers={list(node.modifiers)}"]
        if node.type_node is not None:
            lines.append(f"declared_type={node.declared_type}")
            lines.append(f"resolved_type={node.resolved_type}")
        else:
            lines.append(f"resolved_type={node.resolved_type}")
        return lines
    if isinstance(node, VarDeclNode):
        lines = [kind, f"name={node.name}", f"modifiers={list(node.modifiers)}"]
        if node.type_node is not None:
            lines.append(f"declared_type={node.declared_type}")
            lines.append(f"resolved_type={node.resolved_type}")
        else:
            lines.append(f"resolved_type={node.resolved_type}")
        return lines
    if isinstance(node, ForStmtNode):
        return [kind, f"loop_var={node.loop_var}"]
    if isinstance(node, PrintStmtNode):
        arg = node.argument
        if isinstance(arg, IdentifierNode):
            return [kind, f"argument={arg.name}"]
        return [kind, "argument=<none>"]
    if isinstance(node, IntLiteralNode):
        return [kind, f"value={node.value}"]
    if isinstance(node, FloatLiteralNode):
        return [kind, f"value={node.value}"]
    if isinstance(node, IdentifierNode):
        return [kind, f"name={node.name}"]
    if isinstance(node, SimpleTypeNode):
        return [kind, f"name={node.name}"]
    return [kind]


def _measure_box(lines: List[str], font: QFont, bold: QFont, pad_x: int, pad_y: int) -> Tuple[int, int]:
    tw = 0
    th = 0
    for i, line in enumerate(lines):
        f = bold if i == 0 else font
        m = QFontMetrics(f)
        tw = max(tw, m.horizontalAdvance(line))
        th += m.height() + 2
    w = max(tw + 2 * pad_x, 100)
    h = th + 2 * pad_y
    return w, h


def _collect_nodes(root: AstNode) -> List[AstNode]:
    out: List[AstNode] = []

    def walk(n: AstNode) -> None:
        out.append(n)
        for ch in _ast_children_ordered(n):
            walk(ch)

    walk(root)
    return out


def _hierarchical_layout(
    root: AstNode,
    sizes: Dict[AstNode, Tuple[int, int]],
    row_height: int,
    h_gap: int,
) -> Dict[AstNode, QRectF]:
    """Сверху вниз: уровень = глубина; потомки в ряд; родитель по центру над поддеревьями."""
    rects: Dict[AstNode, QRectF] = {}
    cursor_x = 0.0

    def layout_sub(n: AstNode, depth: int) -> Tuple[float, float]:
        nonlocal cursor_x
        w, h = sizes[n]
        y = float(depth * row_height)
        ch = _ast_children_ordered(n)
        if not ch:
            x = cursor_x
            cursor_x += w + h_gap
            rects[n] = QRectF(x, y, w, h)
            return x, x + w
        spans: List[Tuple[float, float]] = []
        for c in ch:
            spans.append(layout_sub(c, depth + 1))
        L = min(s[0] for s in spans)
        R = max(s[1] for s in spans)
        mid = (L + R) / 2.0
        px = mid - w / 2.0
        rects[n] = QRectF(px, y, w, h)
        return min(px, L), max(px + w, R)

    layout_sub(root, 0)
    return rects


def _collect_edges(root: AstNode) -> List[Tuple[AstNode, AstNode]]:
    edges: List[Tuple[AstNode, AstNode]] = []

    def walk(n: AstNode) -> None:
        for ch in _ast_children_ordered(n):
            edges.append((n, ch))
            walk(ch)

    walk(root)
    return edges


class AstGraphDialog(QDialog):
    """Иерархия AST: узлы - прямоугольники, рёбра - связь родитель—потомок"""

    def __init__(self, root: AstNode, tr: Callable[[str], str], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._tr = tr
        self.setWindowTitle(self._tr("ast_vis_window_title"))
        self.resize(960, 680)

        pad_x = 12
        pad_y = 10
        font = QFont("Segoe UI", 9)
        if not font.exactMatch():
            font = QFont("Arial", 9)
        bold = QFont(font)
        bold.setBold(True)

        nodes = _collect_nodes(root)
        sizes: Dict[AstNode, Tuple[int, int]] = {}
        max_h = 48
        for n in nodes:
            lines = _node_caption_lines(n)
            w, h = _measure_box(lines, font, bold, pad_x, pad_y)
            sizes[n] = (w, h)
            max_h = max(max_h, h)

        row_height = max_h + 28
        h_gap = 36
        node_rects = _hierarchical_layout(root, sizes, row_height, h_gap)
        edges = _collect_edges(root)

        min_x = min(r.left() for r in node_rects.values())
        min_y = min(r.top() for r in node_rects.values())
        shift_x = 32.0 - min_x
        shift_y = 32.0 - min_y
        for n in node_rects:
            node_rects[n] = node_rects[n].translated(shift_x, shift_y)

        scene = QGraphicsScene(self)
        scene.setBackgroundBrush(QBrush(QColor(250, 251, 253)))

        pen_node = QPen(QColor(55, 85, 130))
        pen_node.setWidth(1)
        brush_node = QBrush(QColor(255, 255, 255))
        pen_edge = QPen(QColor(70, 110, 170))
        pen_edge.setWidth(1)

        for parent, child in edges:
            pr = node_rects[parent]
            cr = node_rects[child]
            p1 = QPointF(pr.center().x(), pr.bottom())
            p2 = QPointF(cr.center().x(), cr.top())
            mid_y = (p1.y() + p2.y()) / 2.0
            segments = (
                (p1, QPointF(p1.x(), mid_y)),
                (QPointF(p1.x(), mid_y), QPointF(p2.x(), mid_y)),
                (QPointF(p2.x(), mid_y), p2),
            )
            for a, b in segments:
                ln = QGraphicsLineItem(a.x(), a.y(), b.x(), b.y())
                ln.setPen(pen_edge)
                scene.addItem(ln)

        for n in nodes:
            rect = node_rects[n]
            ritem = QGraphicsRectItem(rect)
            ritem.setPen(pen_node)
            ritem.setBrush(brush_node)
            scene.addItem(ritem)

            lines = _node_caption_lines(n)
            ty = rect.top() + pad_y
            for li, line in enumerate(lines):
                titem = QGraphicsTextItem(line)
                titem.setFont(bold if li == 0 else font)
                titem.setDefaultTextColor(QColor(28, 38, 62))
                titem.setPos(rect.left() + pad_x, ty)
                scene.addItem(titem)
                ty += titem.boundingRect().height() + 2

        scene.setSceneRect(scene.itemsBoundingRect().adjusted(-24, -24, 48, 48))

        view = _AstGraphicsView(scene)
        view.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing
        )
        view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(view)

        self._view = view
        self._scene = scene

    def showEvent(self, event):
        super().showEvent(event)

        def _fit():
            if self._view and self._scene:
                self._view.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

        QTimer.singleShot(0, _fit)
