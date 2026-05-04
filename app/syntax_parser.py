from __future__ import annotations

import math
from typing import List, Optional, Tuple

from ast_nodes import (
    AstNode,
    ConstDeclNode,
    FloatLiteralNode,
    ForStmtNode,
    IdentifierNode,
    IntLiteralNode,
    LiteralNode,
    PrintStmtNode,
    ProgramNode,
    SimpleTypeNode,
    VarDeclNode,
)
from symbol_table import SymbolTable

MAX_INT32 = 2**31 - 1


class SyntaxParser:
    SYNC_KINDS = frozenset({"SEMI"})

    def __init__(self, tokens):
        filtered = [t for t in tokens if t.get("kind") != "WS"]
        self.tokens = filtered
        self.pos = 0
        self.errors: list = []
        self.program = ProgramNode()
        self.global_sym = SymbolTable()
        self.sym: SymbolTable = self.global_sym

        if not self.tokens:
            self._eof = {"kind": "EOF", "lexeme": "", "line": 1, "col": 1, "end_col": 1}
        else:
            last = self.tokens[-1]
            el = last.get("line", 1)
            ec = last.get("end_col", last.get("col", 1)) + 1
            self._eof = {"kind": "EOF", "lexeme": "", "line": el, "col": ec, "end_col": ec}
        self.tokens.append(self._eof)

    def _at(self, idx):
        if 0 <= idx < len(self.tokens):
            return self.tokens[idx]
        return self._eof

    def _current(self):
        return self._at(self.pos)

    def _kind(self):
        return self._current()["kind"]

    @staticmethod
    def _exp_for_failed_kind(kind: str) -> str:
        m = {
            "LPAREN": "(",
            "RPAREN": ")",
            "LBRACE": "{",
            "RBRACE": "}",
            "SEMI": ";",
            "COLON": ":",
            "ASSIGN": "=",
            "KW_IN": "in",
            "ID": "sym_identifier",
            "INT": "sym_integer",
            "KW_CONST": "const",
            "KW_VAR": "var",
            "KW_FOR": "for",
            "KW_PRINT": "print",
            "KW_INT": "int",
            "KW_FLOAT": "float",
        }
        return m.get(kind, kind)

    def parse(self):
        while self._kind() != "EOF":
            stmt = self._parse_statement()
            if stmt is not None:
                self.program.body.append(stmt)
        return self.errors, self.program

    def _parse_statement(self) -> Optional[AstNode]:
        k = self._kind()
        if k == "KW_CONST":
            return self._parse_const_decl()
        if k == "KW_VAR":
            return self._parse_var_decl()
        if k == "KW_FOR":
            return self._parse_for_stmt(require_trailing_semi=True)
        t = self._current()
        frag = t.get("lexeme", "") or ""
        self._add_error(
            t.get("line", 1),
            t.get("col", 1),
            "syn_err_stmt_got",
            (frag,),
            frag[:32] if frag else "?",
            max(len(frag), 1),
        )
        self._synchronize_irons()
        return None

    def _parse_for_stmt(self, require_trailing_semi: bool = False) -> Optional[ForStmtNode]:
        kw = self._current()
        self._consume("KW_FOR")
        if not self._match("LPAREN"):
            self._expect_failed("(", "ctx_after_for")
            self._synchronize_irons()
            return None
        if not self._match("ID"):
            self._expect_failed("sym_identifier", "ctx_header_for")
            self._synchronize_irons()
            return None
        loop_tok = self._at(self.pos - 1)
        loop_name = loop_tok.get("lexeme", "")
        loop_line = loop_tok.get("line", 1)
        loop_col = loop_tok.get("col", 1)
        if not self._match("KW_IN"):
            self._expect_failed("in", "ctx_after_loop_var")
            self._synchronize_irons()
            return None
        if not self._match("INT"):
            self._expect_failed("sym_integer", "ctx_range_start")
            self._synchronize_irons()
            return None
        start_tok = self._at(self.pos - 1)
        start_node = self._int_literal_from_token(start_tok)
        if not self._match("COLON"):
            self._expect_failed(":", "ctx_in_range")
            self._synchronize_irons()
            return None
        if not self._match("INT"):
            self._expect_failed("sym_integer", "ctx_range_end")
            self._synchronize_irons()
            return None
        end_tok = self._at(self.pos - 1)
        end_node = self._int_literal_from_token(end_tok)
        if not self._match("RPAREN"):
            self._expect_failed(")", "ctx_after_range")
            self._synchronize_irons()
            return None
        if not self._match("LBRACE"):
            self._expect_failed("{", "ctx_before_loop_body")
            self._synchronize_irons()
            return None

        range_ok = self._check_range_literals(start_node, end_node, start_tok, end_tok)

        outer = self.sym
        inner = SymbolTable(parent=outer)
        inner.declare(loop_name, "loop", "int", loop_line)
        self.sym = inner
        body_nodes = self._parse_block_stmt_list()
        self.sym = outer

        if not self._match("RBRACE"):
            self._expect_failed("}", "ctx_end_loop_body")
            self._synchronize_to_rbrace()
            return None
        if require_trailing_semi:
            if not self._match("SEMI"):
                self._expect_failed(";", "ctx_after_for_brace")
                self._synchronize_irons()
        elif self._kind() == "SEMI":
            self.pos += 1

        if not range_ok:
            return None

        node = ForStmtNode(
            line=kw.get("line", 1),
            col=kw.get("col", 1),
            loop_var=loop_name,
            loop_var_line=loop_line,
            loop_var_col=loop_col,
            range_start=start_node,
            range_end=end_node,
            body=body_nodes,
        )
        return node

    def _check_range_literals(
        self,
        start_node: IntLiteralNode,
        end_node: IntLiteralNode,
        start_tok: dict,
        end_tok: dict,
    ) -> bool:
        ok = True
        if not self._int_in_range(start_node.value):
            self._add_error(
                start_tok.get("line", 1),
                start_tok.get("col", 1),
                "sem_int_out_of_range",
                (start_node.value, MAX_INT32),
                start_tok.get("lexeme", ""),
                max(len(start_tok.get("lexeme", "")), 1),
            )
            ok = False
        if not self._int_in_range(end_node.value):
            self._add_error(
                end_tok.get("line", 1),
                end_tok.get("col", 1),
                "sem_int_out_of_range",
                (end_node.value, MAX_INT32),
                end_tok.get("lexeme", ""),
                max(len(end_tok.get("lexeme", "")), 1),
            )
            ok = False
        if ok and start_node.value > end_node.value:
            self._add_error(
                end_tok.get("line", 1),
                end_tok.get("col", 1),
                "sem_range_order",
                (start_node.value, end_node.value),
                end_tok.get("lexeme", ""),
                max(len(end_tok.get("lexeme", "")), 1),
            )
            ok = False
        return ok

    def _parse_block_stmt_list(self) -> List[AstNode]:
        items: List[AstNode] = []
        while self._kind() not in ("RBRACE", "EOF"):
            if self._kind() == "KW_PRINT":
                n = self._parse_print_stmt()
                if n is not None:
                    items.append(n)
            elif self._kind() == "KW_FOR":
                n = self._parse_for_stmt(require_trailing_semi=False)
                if n is not None:
                    items.append(n)
            else:
                t = self._current()
                frag = t.get("lexeme", "") or ""
                self._add_error(
                    t.get("line", 1),
                    t.get("col", 1),
                    "syn_err_block_for_print",
                    (frag,),
                    frag[:32] if frag else "?",
                    max(len(frag), 1),
                )
                self._synchronize_in_block()
        return items

    def _parse_print_stmt(self) -> Optional[PrintStmtNode]:
        kw = self._current()
        self._consume("KW_PRINT")
        if not self._match("LPAREN"):
            self._expect_failed("(", "ctx_after_print")
            self._synchronize_in_block()
            return None
        if not self._match("ID"):
            self._expect_failed("sym_identifier", "ctx_in_print")
            self._synchronize_in_block()
            return None
        id_tok = self._at(self.pos - 1)
        name = id_tok.get("lexeme", "")
        info = self.sym.lookup(name)
        if info is None:
            self._add_error(
                id_tok.get("line", 1),
                id_tok.get("col", 1),
                "sem_undeclared",
                (name,),
                name,
                max(len(name), 1),
            )
            if not self._match("RPAREN"):
                self._expect_failed(")", "ctx_after_print_arg")
                self._synchronize_in_block()
                return None
            if self._kind() == "SEMI":
                self.pos += 1
            return None

        if not self._match("RPAREN"):
            self._expect_failed(")", "ctx_after_print_arg")
            self._synchronize_in_block()
            return None
        if self._kind() == "SEMI":
            self.pos += 1

        arg = IdentifierNode(
            line=id_tok.get("line", 1),
            col=id_tok.get("col", 1),
            name=name,
        )
        return PrintStmtNode(line=kw.get("line", 1), col=kw.get("col", 1), argument=arg)

    def _synchronize_in_block(self):
        while self._kind() not in ("RBRACE", "EOF", "KW_FOR", "KW_PRINT"):
            self.pos += 1

    def _synchronize_to_rbrace(self):
        while self._kind() not in ("RBRACE", "EOF"):
            self.pos += 1
        if self._kind() == "RBRACE":
            self.pos += 1
        if self._kind() == "SEMI":
            self.pos += 1

    def _parse_optional_type(self) -> Tuple[Optional[str], Optional[SimpleTypeNode], bool]:
        """Возвращает (аннотация, узел типа, признак фатальной ошибки после ':')."""
        if self._kind() != "COLON":
            return None, None, False
        self.pos += 1
        k = self._kind()
        if k == "KW_INT":
            t = self._current()
            self.pos += 1
            return "int", SimpleTypeNode(line=t.get("line", 1), col=t.get("col", 1), name="int"), False
        if k == "KW_FLOAT":
            t = self._current()
            self.pos += 1
            return "float", SimpleTypeNode(line=t.get("line", 1), col=t.get("col", 1), name="float"), False
        bad = self._current()
        self._add_error(
            bad.get("line", 1),
            bad.get("col", 1),
            "syn_err_expected_int_float",
            (),
            bad.get("lexeme", "")[:32] if bad.get("lexeme") else "?",
            max(len(bad.get("lexeme", "")), 1) if bad.get("lexeme") else 1,
        )
        self._synchronize_irons()
        return None, None, True

    def _parse_const_decl(self) -> Optional[ConstDeclNode]:
        kw = self._current()
        self._consume("KW_CONST")
        if not self._match("ID"):
            self._expect_failed("sym_identifier", "ctx_after_const")
            self._synchronize_irons()
            return None
        name_tok = self._at(self.pos - 1)
        name = name_tok.get("lexeme", "")
        n_line = name_tok.get("line", 1)
        n_col = name_tok.get("col", 1)

        type_ann, type_node, type_bad = self._parse_optional_type()
        if type_bad:
            return None

        if not self._match("ASSIGN"):
            self._expect_failed("=", "ctx_after_const_name")
            self._synchronize_irons()
            return None
        lit = self._parse_literal_expr()
        if lit is None:
            self._synchronize_irons()
            return None
        value_node, lit_ty = lit
        if not self._match("SEMI"):
            self._expect_failed(";", "ctx_after_expr")
            self._synchronize_irons()

        resolved = type_ann if type_ann is not None else lit_ty
        if type_ann is not None and not self._types_compatible(type_ann, lit_ty):
            self._add_error(
                value_node.line,
                value_node.col,
                "sem_type_mismatch",
                (type_ann, lit_ty),
                self._literal_fragment(value_node),
                self._literal_len(value_node),
            )
            return None

        if isinstance(value_node, IntLiteralNode) and not self._int_in_range(value_node.value):
            self._add_error(
                value_node.line,
                value_node.col,
                "sem_int_out_of_range",
                (value_node.value, MAX_INT32),
                str(value_node.value),
                max(len(str(value_node.value)), 1),
            )
            return None
        if isinstance(value_node, FloatLiteralNode) and not self._float_ok(value_node.value):
            self._add_error(
                value_node.line,
                value_node.col,
                "sem_float_invalid",
                (),
                self._literal_fragment(value_node),
                self._literal_len(value_node),
            )
            return None

        ok, prev_line = self.sym.declare(name, "const", resolved, n_line)
        if not ok:
            self._add_error(
                n_line,
                n_col,
                "sem_dup_ident",
                (name, prev_line),
                name,
                max(len(name), 1),
            )
            return None

        return ConstDeclNode(
            line=kw.get("line", 1),
            col=kw.get("col", 1),
            name=name,
            name_line=n_line,
            name_col=n_col,
            modifiers=["const"],
            declared_type=type_ann,
            resolved_type=resolved,
            type_node=type_node,
            value=value_node,
        )

    def _parse_var_decl(self) -> Optional[VarDeclNode]:
        kw = self._current()
        self._consume("KW_VAR")
        if not self._match("ID"):
            self._expect_failed("sym_identifier", "ctx_after_var")
            self._synchronize_irons()
            return None
        name_tok = self._at(self.pos - 1)
        name = name_tok.get("lexeme", "")
        n_line = name_tok.get("line", 1)
        n_col = name_tok.get("col", 1)

        type_ann, type_node, type_bad = self._parse_optional_type()
        if type_bad:
            return None

        if not self._match("ASSIGN"):
            self._expect_failed("=", "ctx_after_var_name")
            self._synchronize_irons()
            return None
        lit = self._parse_literal_expr()
        if lit is None:
            self._synchronize_irons()
            return None
        value_node, lit_ty = lit
        if not self._match("SEMI"):
            self._expect_failed(";", "ctx_after_expr")
            self._synchronize_irons()

        resolved = type_ann if type_ann is not None else lit_ty
        if type_ann is not None and not self._types_compatible(type_ann, lit_ty):
            self._add_error(
                value_node.line,
                value_node.col,
                "sem_type_mismatch",
                (type_ann, lit_ty),
                self._literal_fragment(value_node),
                self._literal_len(value_node),
            )
            return None

        if isinstance(value_node, IntLiteralNode) and not self._int_in_range(value_node.value):
            self._add_error(
                value_node.line,
                value_node.col,
                "sem_int_out_of_range",
                (value_node.value, MAX_INT32),
                str(value_node.value),
                max(len(str(value_node.value)), 1),
            )
            return None
        if isinstance(value_node, FloatLiteralNode) and not self._float_ok(value_node.value):
            self._add_error(
                value_node.line,
                value_node.col,
                "sem_float_invalid",
                (),
                self._literal_fragment(value_node),
                self._literal_len(value_node),
            )
            return None

        ok, prev_line = self.sym.declare(name, "var", resolved, n_line)
        if not ok:
            self._add_error(
                n_line,
                n_col,
                "sem_dup_ident",
                (name, prev_line),
                name,
                max(len(name), 1),
            )
            return None

        return VarDeclNode(
            line=kw.get("line", 1),
            col=kw.get("col", 1),
            name=name,
            name_line=n_line,
            name_col=n_col,
            modifiers=["var"],
            declared_type=type_ann,
            resolved_type=resolved,
            type_node=type_node,
            value=value_node,
        )

    @staticmethod
    def _literal_fragment(node: LiteralNode) -> str:
        if isinstance(node, IntLiteralNode):
            return str(node.value)
        return str(node.value)

    @staticmethod
    def _literal_len(node: LiteralNode) -> int:
        return max(len(SyntaxParser._literal_fragment(node)), 1)

    def _parse_literal_expr(self) -> Optional[Tuple[LiteralNode, str]]:
        k = self._kind()
        if k == "INT":
            t = self._current()
            self.pos += 1
            v = int(t["lexeme"])
            node = IntLiteralNode(value=v, line=t.get("line", 1), col=t.get("col", 1))
            return node, "int"
        if k == "FLOAT":
            t = self._current()
            self.pos += 1
            v = float(t["lexeme"])
            node = FloatLiteralNode(value=v, line=t.get("line", 1), col=t.get("col", 1))
            return node, "float"
        t = self._current()
        frag = t.get("lexeme", "") or ""
        self._add_error(
            t.get("line", 1),
            t.get("col", 1),
            "syn_err_numeric_literal",
            (),
            frag[:32] if frag else "?",
            max(len(frag), 1),
        )
        return None

    def _int_literal_from_token(self, t: dict) -> IntLiteralNode:
        return IntLiteralNode(
            value=int(t["lexeme"]),
            line=t.get("line", 1),
            col=t.get("col", 1),
        )

    @staticmethod
    def _int_in_range(v: int) -> bool:
        return 0 <= v <= MAX_INT32

    @staticmethod
    def _float_ok(v: float) -> bool:
        return math.isfinite(v) and abs(v) <= 1e308

    @staticmethod
    def _types_compatible(declared: str, literal_type: str) -> bool:
        if declared == literal_type:
            return True
        if declared == "float" and literal_type == "int":
            return True
        return False

    def _consume(self, kind):
        if self._kind() == kind:
            self.pos += 1
        else:
            self._expect_failed(self._exp_for_failed_kind(kind), "")

    def _match(self, kind):
        if self._kind() == kind:
            self.pos += 1
            return True
        return False

    def _expect_failed(self, exp, ctx_key):
        t = self._current()
        got = t.get("lexeme", "") or ""
        if got == "" and self._kind() == "EOF":
            got_display = "sym_eof"
            frag = "EOF"
            flen = 1
        else:
            got_display = got
            frag = got[:32] if got else "?"
            flen = max(len(got), 1) if got else 1

        self._add_error(
            t.get("line", 1),
            t.get("col", 1),
            "syn_expect_failed",
            (exp, ctx_key or "", got_display),
            frag,
            flen,
        )

    def _add_error(self, line, col, key, args, fragment, frag_len):
        self.errors.append((line, col, key, args, fragment, frag_len))

    def _synchronize_irons(self):
        while self._kind() not in ("SEMI", "EOF"):
            self.pos += 1
        if self._kind() == "SEMI":
            self.pos += 1
