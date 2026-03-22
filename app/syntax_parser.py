from __future__ import annotations


class SyntaxParser:
    SYNC_KINDS = frozenset({"SEMI"})

    def __init__(self, tokens):
        filtered = [t for t in tokens if t.get("kind") != "WS"]
        self.tokens = filtered
        self.pos = 0
        self.errors = []

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
        }
        return m.get(kind, kind)

    def parse(self):
        while self._kind() != "EOF":
            self._parse_statement()
        return self.errors

    def _parse_statement(self):
        k = self._kind()
        if k == "KW_CONST":
            self._parse_const_decl()
        elif k == "KW_VAR":
            self._parse_var_decl()
        elif k == "KW_FOR":
            self._parse_for_stmt(require_trailing_semi=True)
        else:
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

    def _parse_for_stmt(self, require_trailing_semi: bool = False):
        self._consume("KW_FOR")
        if not self._match("LPAREN"):
            self._expect_failed("(", "ctx_after_for")
            self._synchronize_irons()
            return
        if not self._match("ID"):
            self._expect_failed("sym_identifier", "ctx_header_for")
            self._synchronize_irons()
            return
        if not self._match("KW_IN"):
            self._expect_failed("in", "ctx_after_loop_var")
            self._synchronize_irons()
            return
        if not self._match("INT"):
            self._expect_failed("sym_integer", "ctx_range_start")
            self._synchronize_irons()
            return
        if not self._match("COLON"):
            self._expect_failed(":", "ctx_in_range")
            self._synchronize_irons()
            return
        if not self._match("INT"):
            self._expect_failed("sym_integer", "ctx_range_end")
            self._synchronize_irons()
            return
        if not self._match("RPAREN"):
            self._expect_failed(")", "ctx_after_range")
            self._synchronize_irons()
            return
        if not self._match("LBRACE"):
            self._expect_failed("{", "ctx_before_loop_body")
            self._synchronize_irons()
            return
        self._parse_block_stmt_list()
        if not self._match("RBRACE"):
            self._expect_failed("}", "ctx_end_loop_body")
            self._synchronize_to_rbrace()
            return
        if require_trailing_semi:
            if not self._match("SEMI"):
                self._expect_failed(";", "ctx_after_for_brace")
                self._synchronize_irons()
        elif self._kind() == "SEMI":
            self.pos += 1

    def _parse_block_stmt_list(self):
        while self._kind() not in ("RBRACE", "EOF"):
            if self._kind() == "KW_PRINT":
                self._parse_print_stmt()
            elif self._kind() == "KW_FOR":
                self._parse_for_stmt(require_trailing_semi=False)
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

    def _parse_print_stmt(self):
        self._consume("KW_PRINT")
        if not self._match("LPAREN"):
            self._expect_failed("(", "ctx_after_print")
            self._synchronize_in_block()
            return
        if not self._match("ID"):
            self._expect_failed("sym_identifier", "ctx_in_print")
            self._synchronize_in_block()
            return
        if not self._match("RPAREN"):
            self._expect_failed(")", "ctx_after_print_arg")
            self._synchronize_in_block()
            return
        if self._kind() == "SEMI":
            self.pos += 1

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

    def _parse_const_decl(self):
        self._consume("KW_CONST")
        if not self._match("ID"):
            self._expect_failed("sym_identifier", "ctx_after_const")
            self._synchronize_irons()
            return
        if not self._match("ASSIGN"):
            self._expect_failed("=", "ctx_after_const_name")
            self._synchronize_irons()
            return
        if not self._parse_literal_expr():
            self._synchronize_irons()
            return
        if not self._match("SEMI"):
            self._expect_failed(";", "ctx_after_expr")
            self._synchronize_irons()

    def _parse_var_decl(self):
        self._consume("KW_VAR")
        if not self._match("ID"):
            self._expect_failed("sym_identifier", "ctx_after_var")
            self._synchronize_irons()
            return
        if not self._match("ASSIGN"):
            self._expect_failed("=", "ctx_after_var_name")
            self._synchronize_irons()
            return
        if not self._parse_literal_expr():
            self._synchronize_irons()
            return
        if not self._match("SEMI"):
            self._expect_failed(";", "ctx_after_expr")
            self._synchronize_irons()

    def _parse_literal_expr(self) -> bool:
        k = self._kind()
        if k in ("INT", "FLOAT"):
            self.pos += 1
            return True
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
