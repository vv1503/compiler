from __future__ import annotations

import json
from typing import Union


class AstNode:
    def __init__(self, line=1, col=1):
        self.line = line
        self.col = col


class ProgramNode(AstNode):
    def __init__(self, line=1, col=1):
        super().__init__(line, col)
        self.body = []


class SimpleTypeNode(AstNode):
    def __init__(self, name="", line=1, col=1):
        super().__init__(line, col)
        self.name = name


class IntLiteralNode(AstNode):
    def __init__(self, value=0, line=1, col=1):
        super().__init__(line, col)
        self.value = value


class FloatLiteralNode(AstNode):
    def __init__(self, value=0.0, line=1, col=1):
        super().__init__(line, col)
        self.value = value


LiteralNode = Union[IntLiteralNode, FloatLiteralNode]


class IdentifierNode(AstNode):
    def __init__(self, name="", line=1, col=1):
        super().__init__(line, col)
        self.name = name


class ConstDeclNode(AstNode):
    def __init__(
        self,
        line=1,
        col=1,
        name="",
        name_line=1,
        name_col=1,
        modifiers=None,
        declared_type=None,
        resolved_type="",
        type_node=None,
        value=None,
    ):
        super().__init__(line, col)
        self.name = name
        self.name_line = name_line
        self.name_col = name_col
        self.modifiers = ["const"] if modifiers is None else list(modifiers)
        self.declared_type = declared_type
        self.resolved_type = resolved_type
        self.type_node = type_node
        self.value = value


class VarDeclNode(AstNode):
    def __init__(
        self,
        line=1,
        col=1,
        name="",
        name_line=1,
        name_col=1,
        modifiers=None,
        declared_type=None,
        resolved_type="",
        type_node=None,
        value=None,
    ):
        super().__init__(line, col)
        self.name = name
        self.name_line = name_line
        self.name_col = name_col
        self.modifiers = ["var"] if modifiers is None else list(modifiers)
        self.declared_type = declared_type
        self.resolved_type = resolved_type
        self.type_node = type_node
        self.value = value


class ForStmtNode(AstNode):
    def __init__(
        self,
        line=1,
        col=1,
        loop_var="",
        loop_var_line=1,
        loop_var_col=1,
        range_start=None,
        range_end=None,
        body=None,
    ):
        super().__init__(line, col)
        self.loop_var = loop_var
        self.loop_var_line = loop_var_line
        self.loop_var_col = loop_var_col
        self.range_start = range_start
        self.range_end = range_end
        self.body = [] if body is None else body


class PrintStmtNode(AstNode):
    def __init__(self, line=1, col=1, argument=None):
        super().__init__(line, col)
        self.argument = argument


def _fmt_modifiers(mods):
    return json.dumps(mods, ensure_ascii=False)


def format_ast_tree(root):
    if root is None:
        return ""
    lines = []

    def line(prefix, is_last, text):
        br = "└── " if is_last else "├── "
        lines.append(f"{prefix}{br}{text}")

    def rec(node, prefix, is_last):
        if isinstance(node, ProgramNode):
            lines.append("ProgramNode")
            for i, ch in enumerate(node.body):
                rec(ch, "", i == len(node.body) - 1)
            return

        line(prefix, is_last, node.__class__.__name__)
        ext = prefix + ("    " if is_last else "│   ")

        if isinstance(node, ForStmtNode):
            parts = []
            parts.append(("scalar", "loop_var", json.dumps(node.loop_var, ensure_ascii=False)))
            if node.range_start is not None:
                parts.append(("sub", "range_start", node.range_start))
            if node.range_end is not None:
                parts.append(("sub", "range_end", node.range_end))
            for st in node.body:
                parts.append(("stmt", "", st))
            for i, p in enumerate(parts):
                last_p = i == len(parts) - 1
                if p[0] == "scalar":
                    line(ext, last_p, f"{p[1]}: {p[2]}")
                elif p[0] == "sub":
                    _, label, subn = p
                    line(ext, last_p, f"{label}: {subn.__class__.__name__}")
                    rec(subn, ext + ("    " if last_p else "│   "), True)
                else:
                    _, __, st = p
                    rec(st, ext, last_p)
            return

        kids = _children_slots(node)
        for i, (label, val) in enumerate(kids):
            last_k = i == len(kids) - 1
            if isinstance(val, AstNode):
                line(ext, last_k, f"{label}: {val.__class__.__name__}")
                rec(val, ext + ("    " if last_k else "│   "), True)
            else:
                line(ext, last_k, f"{label}: {val}")

    rec(root, "", True)
    return "\n".join(lines)


def _children_slots(node):
    if isinstance(node, ProgramNode):
        return []
    if isinstance(node, SimpleTypeNode):
        return [("name", json.dumps(node.name, ensure_ascii=False))]
    if isinstance(node, IntLiteralNode):
        return [("value", str(node.value))]
    if isinstance(node, FloatLiteralNode):
        s = str(node.value)
        if s.endswith(".0") and node.value == int(node.value):
            s = str(int(node.value))
        return [("value", s)]
    if isinstance(node, IdentifierNode):
        return [("name", json.dumps(node.name, ensure_ascii=False))]
    if isinstance(node, ConstDeclNode):
        tnode = node.type_node
        slots = [
            ("name", json.dumps(node.name, ensure_ascii=False)),
            ("modifiers", _fmt_modifiers(node.modifiers)),
        ]
        if tnode is not None:
            slots.append(("type", tnode))
        else:
            slots.append(("type (выведен)", json.dumps(node.resolved_type, ensure_ascii=False)))
        if node.value is not None:
            slots.append(("value", node.value))
        return slots
    if isinstance(node, VarDeclNode):
        tnode = node.type_node
        slots = [
            ("name", json.dumps(node.name, ensure_ascii=False)),
            ("modifiers", _fmt_modifiers(node.modifiers)),
        ]
        if tnode is not None:
            slots.append(("type", tnode))
        else:
            slots.append(("type (выведен)", json.dumps(node.resolved_type, ensure_ascii=False)))
        if node.value is not None:
            slots.append(("value", node.value))
        return slots
    if isinstance(node, ForStmtNode):
        return []
    if isinstance(node, PrintStmtNode):
        if node.argument:
            return [("argument", node.argument)]
        return [("argument", "null")]
    return []


def ast_to_dict(node):
    if node is None:
        return None
    if isinstance(node, ProgramNode):
        return {"kind": "ProgramNode", "body": [ast_to_dict(x) for x in node.body]}
    if isinstance(node, SimpleTypeNode):
        return {"kind": "SimpleTypeNode", "name": node.name, "line": node.line, "col": node.col}
    if isinstance(node, IntLiteralNode):
        return {"kind": "IntLiteralNode", "value": node.value, "line": node.line, "col": node.col}
    if isinstance(node, FloatLiteralNode):
        return {"kind": "FloatLiteralNode", "value": node.value, "line": node.line, "col": node.col}
    if isinstance(node, IdentifierNode):
        return {"kind": "IdentifierNode", "name": node.name, "line": node.line, "col": node.col}
    if isinstance(node, ConstDeclNode):
        return {
            "kind": "ConstDeclNode",
            "name": node.name,
            "modifiers": list(node.modifiers),
            "declared_type": node.declared_type,
            "resolved_type": node.resolved_type,
            "type": ast_to_dict(node.type_node) if node.type_node else {"inferred": node.resolved_type},
            "value": ast_to_dict(node.value),
            "line": node.line,
            "col": node.col,
        }
    if isinstance(node, VarDeclNode):
        return {
            "kind": "VarDeclNode",
            "name": node.name,
            "modifiers": list(node.modifiers),
            "declared_type": node.declared_type,
            "resolved_type": node.resolved_type,
            "type": ast_to_dict(node.type_node) if node.type_node else {"inferred": node.resolved_type},
            "value": ast_to_dict(node.value),
            "line": node.line,
            "col": node.col,
        }
    if isinstance(node, ForStmtNode):
        return {
            "kind": "ForStmtNode",
            "loop_var": node.loop_var,
            "range_start": ast_to_dict(node.range_start),
            "range_end": ast_to_dict(node.range_end),
            "body": [ast_to_dict(x) for x in node.body],
            "line": node.line,
            "col": node.col,
        }
    if isinstance(node, PrintStmtNode):
        return {
            "kind": "PrintStmtNode",
            "argument": ast_to_dict(node.argument),
            "line": node.line,
            "col": node.col,
        }
    return {"kind": node.__class__.__name__}


def ast_to_json(root):
    return json.dumps(ast_to_dict(root), ensure_ascii=False, indent=2)
