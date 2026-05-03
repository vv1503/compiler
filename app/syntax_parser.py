from __future__ import annotations

import re


class SyntaxParser:
    SYNC_KINDS = frozenset({"SEMI"})

    def __init__(self, tokens, lex_errors=None, source_text: str = ""):
        filtered = [t for t in tokens if t.get("kind") != "WS"]
        self.tokens = filtered
        self.pos = 0
        self.errors = []
        self.source_text = source_text or ""
        self._source_lines = self.source_text.splitlines()
        self._lex_error_cols = {}
        for err in (lex_errors or []):
            if len(err) < 2:
                continue
            line, col = int(err[0]), int(err[1])
            self._lex_error_cols.setdefault(line, []).append(col)
        for line in self._lex_error_cols:
            self._lex_error_cols[line].sort()

        if not self.tokens:
            self._eof = {"kind": "EOF", "lexeme": "", "line": 1, "col": 1, "end_col": 1}
        else:
            last = self.tokens[-1]
            el = last.get("line", 1)
            ec = last.get("end_col", last.get("col", 1)) + 1
            self._eof = {"kind": "EOF", "lexeme": "", "line": el, "col": ec, "end_col": ec}
        self.tokens.append(self._eof)
        self._for_loop_var_stack: list[str | None] = []
        self._lex_errors_ref: list | None = lex_errors if isinstance(lex_errors, list) else None
        self._suppressed_lex_cols: set[tuple[int, int]] = set()
        self._for_missing_open_brace_reported: bool = False

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
        self._apply_lex_suppressions()
        return self.errors

    def _apply_lex_suppressions(self):
        if not self._lex_errors_ref or not self._suppressed_lex_cols:
            return

        def keep(err):
            if len(err) < 3:
                return True
            key = err[2]
            if key != "lex_err_bad_char":
                return True
            line, col = int(err[0]), int(err[1])
            return (line, col) not in self._suppressed_lex_cols

        self._lex_errors_ref[:] = [e for e in self._lex_errors_ref if keep(e)]
        for line, col in list(self._suppressed_lex_cols):
            cols = self._lex_error_cols.get(line)
            if cols and col in cols:
                cols.remove(col)
            if not cols:
                del self._lex_error_cols[line]

    def _suppress_lex_errors_between(self, left_tok, right_tok) -> None:
        left_line = int(left_tok.get("line", 1))
        if int(right_tok.get("line", 1)) != left_line:
            return
        left_end = int(left_tok.get("end_col", left_tok.get("col", 1)))
        right_col = int(right_tok.get("col", 1))
        for col in list(self._lex_error_cols.get(left_line, [])):
            if left_end < col < right_col:
                self._suppressed_lex_cols.add((left_line, col))

    def _source_between_tokens(self, left_tok, right_tok) -> str:
        ln = int(left_tok.get("line", 1))
        if int(right_tok.get("line", 1)) != ln or ln < 1 or ln > len(self._source_lines):
            return ""
        line_text = self._source_lines[ln - 1]
        s1 = int(left_tok.get("end_col", left_tok.get("col", 1))) + 1
        e1 = int(right_tok.get("col", 1)) - 1
        if e1 < s1:
            return ""
        return line_text[s1 - 1 : e1]

    def _first_lex_col_between(self, left_tok, right_tok) -> int | None:
        left_line = int(left_tok.get("line", 1))
        if int(right_tok.get("line", 1)) != left_line:
            return None
        left_end = int(left_tok.get("end_col", left_tok.get("col", 1)))
        right_col = int(right_tok.get("col", 1))
        for col in self._lex_error_cols.get(left_line, []):
            if left_end < col < right_col:
                return col
        return None

    def _parse_statement(self):
        k = self._kind()
        if k == "KW_CONST":
            self._for_missing_open_brace_reported = False
            self._parse_const_decl()
        elif k == "KW_VAR":
            self._for_missing_open_brace_reported = False
            self._parse_var_decl()
        elif k == "KW_FOR":
            self._for_missing_open_brace_reported = False
            self._parse_for_stmt(require_trailing_semi=True)
        elif k == "SEMI":
            self._for_missing_open_brace_reported = False
            t = self._current()
            self._add_error(
                int(t.get("line", 1)),
                int(t.get("col", 1)),
                "syn_err_for_illegal_semicolon",
                (),
                ";",
                1,
            )
            self.pos += 1
        elif k == "ID" and self._consume_near_keyword("for"):
            self._for_missing_open_brace_reported = False
            self._parse_for_stmt_core(require_trailing_semi=True, typo_recovered=True)
        elif k == "LPAREN":
            self._for_missing_open_brace_reported = False
            # Восстановление: пропущено ключевое слово for перед заголовком "(...)"
            self._expect_failed("for", "")
            self._parse_for_stmt_core(
                require_trailing_semi=True,
                typo_recovered=True,
                suppress_in_without_loop_var=True,
            )
        else:
            if self._for_missing_open_brace_reported and k == "RBRACE":
                self.pos += 1
                if self._kind() == "SEMI":
                    self.pos += 1
                self._for_missing_open_brace_reported = False
                return
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
        self._parse_for_stmt_core(require_trailing_semi=require_trailing_semi, typo_recovered=False)

    def _consume_illegal_semicolons_in_for_header_before_rparen(self) -> None:
        """«;» допустима только после «}» завершения for; в заголовке перед «)» — одна ошибка и снятие всех «;»."""
        if self._kind() != "SEMI":
            return
        first = self._current()
        while self._kind() == "SEMI":
            self.pos += 1
        self._add_error(
            int(first.get("line", 1)),
            int(first.get("col", 1)),
            "syn_err_for_illegal_semicolon",
            (),
            ";",
            1,
        )

    def _consume_junk_until_lbrace_after_for_header(self) -> None:
        """После «)» заголовка for сразу ожидается «{»; лишние токены до «{» — по одной ошибке на токен."""
        while self._kind() not in ("LBRACE", "EOF", "RBRACE"):
            if self._looks_like_block_stmt_start():
                break
            t = self._current()
            k = t.get("kind")
            if k in ("KW_FOR", "KW_PRINT"):
                break
            if k == "SEMI":
                self._add_error(
                    int(t.get("line", 1)),
                    int(t.get("col", 1)),
                    "syn_err_for_illegal_semicolon",
                    (),
                    ";",
                    1,
                )
                self.pos += 1
                continue
            if k == "EOF":
                break
            disp = (t.get("lexeme", "") or "").strip()[:48] or k
            self._add_error(
                int(t.get("line", 1)),
                int(t.get("col", 1)),
                "syn_err_for_junk_before_lbrace",
                (disp[:64],),
                disp[:32],
                max(len(disp[:32]), 1),
            )
            self.pos += 1

    def _skip_consecutive_duplicate_kw_after(self, keyword: str) -> None:
        """Подряд повторённое ключевое слово (например «in in») — одна ошибка, лишние токены снимаются."""
        kw_kind = "KW_IN" if keyword == "in" else f"KW_{keyword.upper()}"
        low = keyword.lower()
        if self._kind() != kw_kind:
            return
        if (self._current().get("lexeme") or "").lower() != low:
            return
        if self.pos <= 0:
            return
        prev = self._at(self.pos - 1)
        if prev.get("kind") != kw_kind or (prev.get("lexeme") or "").lower() != low:
            return
        t = self._current()
        self._add_error(
            int(t.get("line", 1)),
            int(t.get("col", 1)),
            "syn_err_duplicate_kw_consecutive",
            (keyword,),
            keyword,
            len(keyword),
        )
        while self._kind() == kw_kind and (self._current().get("lexeme") or "").lower() == low:
            self.pos += 1

    def _recover_junk_before_for_lparen(self) -> None:
        """После «for» ожидается «(». Только если «(» есть до ключевого «in», снимаем один лишний фрагмент до неё.

        Не используем syn_err_for_junk_before_lparen, если «(» нет вообще (разбор пошаговый) или если до первой «(»
        уже встретилось «in» — иначе первая «(» может быть от print( и т.п., а не от заголовка for."""
        start = self.pos
        if self._kind() == "LPAREN":
            return
        j = start
        saw_in_before_paren = False
        while j < len(self.tokens):
            kt = self._at(j).get("kind")
            if kt == "LPAREN":
                break
            if kt == "EOF":
                break
            if kt == "KW_IN" and (self._at(j).get("lexeme") or "").lower() == "in":
                saw_in_before_paren = True
            j += 1
        # Если «(» вообще нет до конца ввода, не склеиваем «i in 1 10 …» в один syn_err_for_junk_before_lparen —
        # дальше разбор заголовка for сам выдаст цепочку ожидаемых «(», «:», «)», «{» и т.д.
        if self._at(j).get("kind") != "LPAREN":
            return
        # Если до первой «(» уже прошли «in», это заголовок вида «for i in …» без открывающей «(» — первая «(»
        # дальше по тексту почти наверняка от print( и т.п.; не используем syn_err_for_junk_before_lparen.
        if saw_in_before_paren:
            return
        last_junk = j - 1
        if last_junk < start:
            return
        first = self._at(start)
        last = self._at(last_junk)
        shown = self._extract_source_fragment(first, last)
        if not shown:
            parts: list[str] = []
            for idx in range(start, j):
                tok = self._at(idx)
                if tok.get("kind") == "EOF":
                    break
                lx = (tok.get("lexeme", "") or "").strip()
                if lx:
                    parts.append(lx)
            shown = " ".join(parts) if parts else "?"
        frag = shown[:48]
        self._add_error(
            int(first.get("line", 1)),
            int(first.get("col", 1)),
            "syn_err_for_junk_before_lparen",
            (shown[:64],),
            frag,
            max(len(frag), 1),
        )
        self.pos = j

    def _parse_for_stmt_core(
        self,
        require_trailing_semi: bool = False,
        typo_recovered: bool = False,
        suppress_in_without_loop_var: bool = False,
    ):
        self._skip_duplicated_keyword_after_lex_error("for")
        self._consume_duplicate_keyword_tokens("for")
        if not self._match("LPAREN"):
            if self._kind() == "EOF":
                self._expect_failed("(", "ctx_after_for")
                return
            self._recover_junk_before_for_lparen()
            if not self._match("LPAREN"):
                self._expect_failed("(", "ctx_after_for")
                if self._kind() == "EOF":
                    return
        id_ok = self._match("ID")
        loop_var: str | None = None
        if id_ok:
            loop_var = (self._at(self.pos - 1).get("lexeme") or "") or None
        in_ok = False
        if not id_ok:
            # Сразу «in» без имени переменной (например после пропуска «i» в «fr i in …»)
            if self._kind() == "KW_IN" and (self._current().get("lexeme") or "").lower() == "in":
                if not suppress_in_without_loop_var:
                    t = self._current()
                    err_line = int(t.get("line", 1))
                    err_col = int(t.get("col", 1))
                    if self.pos > 0:
                        prev = self._at(self.pos - 1)
                        if int(prev.get("line", 1)) == err_line:
                            err_col = int(prev.get("end_col", prev.get("col", 1))) + 1
                    self._add_error(
                        err_line,
                        err_col,
                        "syn_err_in_without_loop_var",
                        (),
                        "",
                        0,
                    )
                self.pos += 1
                in_ok = True
            else:
                self._expect_failed("sym_identifier", "ctx_header_for")
                if self._kind() == "ID":
                    self.pos += 1
                    id_ok = self._match("ID")

        if id_ok and not in_ok:
            # «for (i i%n …)»: переменная «i», затем повреждённое «in» как «i»+«%»+«n» (два ID «i» и «n»).
            # Иначе вторая «i» ошибочно даёт syn_err_for_duplicate_loop_var, а «n» — отдельный syn_err_keyword_in_typo.
            merged_damaged_in = False
            if (
                loop_var == "i"
                and self._kind() == "ID"
                and (self._current().get("lexeme") or "") == "i"
            ):
                nxt = self._at(self.pos + 1)
                mid = self._source_between_tokens(self._current(), nxt)
                # «i i n» даёт тот же зазор, что «i i%n»; отличаем по тексту между токенами или lex_err.
                noisy_between = bool(mid.strip()) or self._has_lex_error_between(
                    self._current(), nxt
                )
                if (
                    nxt.get("kind") == "ID"
                    and (nxt.get("lexeme") or "") == "n"
                    and int(self._current().get("line", 1)) == int(nxt.get("line", 1))
                    and noisy_between
                ):
                    t0 = self._current()
                    shown = self._extract_source_fragment(t0, nxt) or "i%n"
                    self._add_keyword_typo_error("in", shown)
                    self.pos += 2
                    in_ok = True
                    merged_damaged_in = True
            if not merged_damaged_in and loop_var and self._kind() == "ID" and (self._current().get("lexeme") or "") == loop_var:
                t = self._current()
                self._add_error(
                    int(t.get("line", 1)),
                    int(t.get("col", 1)),
                    "syn_err_for_duplicate_loop_var",
                    (loop_var,),
                    loop_var,
                    max(len(loop_var), 1),
                )
                while self._kind() == "ID" and (self._current().get("lexeme") or "") == loop_var:
                    self.pos += 1
            if not merged_damaged_in:
                in_ok = in_ok or (
                    self._match("KW_IN")
                    or self._consume_damaged_in_splits()
                    or self._consume_near_keyword("in")
                )

        if not in_ok:
            self._expect_failed("in", "ctx_after_loop_var")
            # Если вместо in пришел идентификатор (обычно хвост после
            # недопустимого символа), сдвигаемся на него один раз,
            # чтобы не вызывать каскад ошибок по заголовку for.
            if self._kind() == "ID":
                self.pos += 1

        self._skip_consecutive_duplicate_kw_after("in")

        start_num, end_num, skip_bounds_order = self._parse_for_range_bounds()
        self._consume_illegal_semicolons_in_for_header_before_rparen()
        if (
            not skip_bounds_order
            and start_num is not None
            and end_num is not None
            and start_num >= end_num
        ):
            t = self._at(self.pos - 1)
            self._add_error(
                int(t.get("line", 1)),
                int(t.get("col", 1)),
                "syn_err_range_bounds_order",
                (str(start_num), str(end_num)),
                t.get("lexeme", "") or str(end_num),
                max(len(t.get("lexeme", "") or str(end_num)), 1),
            )
        self._expect_or_report("RPAREN", ")", "ctx_after_range", consume_if_stuck=False)
        header_rparen = self._at(self.pos - 1)

        self._for_loop_var_stack.append(loop_var)
        skip_trailing_semi = False
        try:
            self._consume_junk_until_lbrace_after_for_header()
            if self._match("LBRACE"):
                self._parse_block_stmt_list()
                self._expect_or_report("RBRACE", "}", "ctx_end_loop_body")
            else:

                def _finish_missing_lbrace_block() -> None:
                    if header_rparen.get("kind") == "RPAREN":
                        ln = int(header_rparen.get("line", 1))
                        cl = int(header_rparen.get("end_col", header_rparen.get("col", 1))) + 1
                        self._add_error(ln, cl, "syn_err_missing_lbrace_for", (), "", 0)
                        self._for_missing_open_brace_reported = True
                    else:
                        self._expect_failed("{", "ctx_before_loop_body")
                        self._for_missing_open_brace_reported = True
                    self._parse_block_stmt_list()
                    self._expect_or_report("RBRACE", "}", "ctx_end_loop_body")

                if header_rparen.get("kind") == "RPAREN" and self._kind() != "LBRACE":
                    if self._kind() == "EOF":
                        _finish_missing_lbrace_block()
                    else:
                        first_tok = self._current()
                        parts: list[str] = []
                        while self._kind() not in ("LBRACE", "EOF", "RBRACE"):
                            k = self._kind()
                            if k in ("KW_FOR", "KW_PRINT"):
                                break
                            if self._looks_like_block_stmt_start():
                                break
                            t = self._current()
                            lx = (t.get("lexeme") or "").strip()
                            if not lx:
                                lx = {"RBRACE": "}", "RPAREN": ")", "LPAREN": "("}.get(k, "") or str(k)
                            parts.append(str(lx)[:48])
                            self.pos += 1
                        got = "".join(parts)
                        if got:
                            disp = got[:64]
                            self._add_error(
                                int(first_tok.get("line", 1)),
                                int(first_tok.get("col", 1)),
                                "syn_err_for_expected_lbrace_got",
                                (got,),
                                disp,
                                max(len(disp), 1),
                            )
                            self._for_missing_open_brace_reported = True
                            skip_trailing_semi = True
                            self._recover_orphan_for_body_after_wrong_rbrace()
                        elif self._kind() in ("KW_FOR", "KW_PRINT") or self._looks_like_block_stmt_start():
                            _finish_missing_lbrace_block()
                        else:
                            _finish_missing_lbrace_block()
                else:
                    _finish_missing_lbrace_block()
            if require_trailing_semi and not skip_trailing_semi:
                if not self._match("SEMI"):
                    self._expect_failed(";", "ctx_after_for_brace")
                    if self._kind() == "COLON":
                        self.pos += 1
                    elif self._kind() in ("KW_FOR", "KW_PRINT"):
                        # Иначе следующий for разберётся как «for ; for …» и даст лишние syn_err_for_junk_before_lparen.
                        self.pos += 1
            elif self._kind() == "SEMI":
                self.pos += 1
        finally:
            self._for_loop_var_stack.pop()

    def _recover_orphan_for_body_after_wrong_rbrace(self) -> None:
        """После «) }» вместо «) {» следующие операторы как у тела for разбираются без дополнительных сообщений."""
        while self._kind() != "EOF":
            if not self._looks_like_block_stmt_start():
                break
            if self._kind() == "KW_PRINT":
                self._parse_print_stmt()
            elif self._kind() == "KW_FOR":
                self._parse_for_stmt(require_trailing_semi=False)
            elif self._kind() == "ID" and self._consume_near_keyword("print"):
                self._parse_print_stmt_core()
            elif self._kind() == "ID" and self._at(self.pos + 1).get("kind") == "LPAREN":
                self._add_keyword_typo_error(
                    "print", self._current().get("lexeme", "") or ""
                )
                self.pos += 1
                self._parse_print_stmt_core()
            else:
                break

    def _parse_block_stmt_list(self):
        while self._kind() not in ("RBRACE", "EOF"):
            if self._kind() == "SEMI":
                t = self._current()
                self._add_error(
                    int(t.get("line", 1)),
                    int(t.get("col", 1)),
                    "syn_err_for_illegal_semicolon",
                    (),
                    ";",
                    1,
                )
                self.pos += 1
                continue
            if self._kind() == "LBRACE":
                t = self._current()
                frag = t.get("lexeme", "") or "{"
                self._add_error(
                    t.get("line", 1),
                    t.get("col", 1),
                    "syn_err_duplicate_fragment",
                    (frag,),
                    frag,
                    max(len(frag), 1),
                )
                self.pos += 1
                continue
            if self._kind() == "KW_PRINT":
                self._parse_print_stmt()
            elif self._kind() == "KW_FOR":
                self._parse_for_stmt(require_trailing_semi=False)
            elif self._kind() == "ID" and self._consume_near_keyword("print"):
                self._parse_print_stmt_core()
            elif self._kind() == "ID" and self._at(self.pos + 1).get("kind") == "LPAREN":
                # В теле блока grammar допускает только print(...) и for(...).
                # Конструкция вида ID(...) трактуется как испорченный print(...),
                # чтобы не порождать каскад лишних ошибок по каждому токену внутри.
                self._add_keyword_typo_error(
                    "print", self._current().get("lexeme", "") or ""
                )
                self.pos += 1
                self._parse_print_stmt_core()
            elif (
                self._kind() in ("ID", "INT", "FLOAT")
                and not self._looks_like_block_stmt_start()
            ):
                t = self._current()
                disp = ((t.get("lexeme", "") or "").strip()[:48]) or self._kind()
                self._add_error(
                    int(t.get("line", 1)),
                    int(t.get("col", 1)),
                    "syn_err_block_extra_token",
                    (disp[:64],),
                    disp[:32],
                    max(len(disp[:32]), 1),
                )
                self.pos += 1
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
        self._parse_print_stmt_core()

    def _parse_print_stmt_core(self):
        self._consume_duplicate_keyword_tokens("print")
        self._expect_or_report("LPAREN", "(", "ctx_after_print")
        if self._match("ID"):
            arg_tok = self._at(self.pos - 1)
            arg_lex = (arg_tok.get("lexeme") or "") or ""
            exp = self._for_loop_var_stack[-1] if self._for_loop_var_stack else None
            if exp and arg_lex and arg_lex != exp:
                self._add_error(
                    int(arg_tok.get("line", 1)),
                    int(arg_tok.get("col", 1)),
                    "sem_err_print_arg_not_loop_var",
                    (exp, arg_lex),
                    arg_lex,
                    max(len(arg_lex), 1),
                )
        else:
            self._expect_failed("sym_identifier", "ctx_in_print")
        self._expect_or_report("RPAREN", ")", "ctx_after_print_arg")
        # «;» в теле for не съедаем — допустим только после «}» цикла (обрабатывает _parse_block_stmt_list).

    def _expect_or_report(self, kind: str, exp: str, ctx_key: str, consume_if_stuck: bool = False) -> bool:
        if self._match(kind):
            return True
        t = self._current()
        line = t.get("line", 1)
        col = t.get("col", 1)
        self._expect_failed(exp, ctx_key)
        if consume_if_stuck and self._kind() != "EOF":
            t_after = self._current()
            if t_after.get("line", 1) == line and t_after.get("col", 1) == col:
                self.pos += 1
        return False

    def _peek_joined_ids_near_keyword(self, keyword: str) -> bool:
        """Без сдвига pos: соседние ID в одной строке (между ними — лексический шум вроде «@») дают почти «{0}»."""
        if self._kind() != "ID":
            return False
        t = self._current()
        lex = (t.get("lexeme") or "") or ""
        if self._is_near_keyword(lex, keyword):
            return True
        joined = lex
        consumed = 1
        line = t.get("line")
        prev = t
        max_parts = min(len(keyword) + 1, 6)
        while consumed < max_parts:
            nxt = self._at(self.pos + consumed)
            if nxt.get("kind") != "ID" or nxt.get("line") != line:
                break
            gap = int(nxt.get("col", 0)) - int(prev.get("end_col", prev.get("col", 0)))
            if gap < 1 or gap > 4:
                break
            joined += (nxt.get("lexeme") or "") or ""
            consumed += 1
            prev = nxt
            if self._is_near_keyword(joined, keyword):
                return True
        return False

    def _looks_like_block_stmt_start(self) -> bool:
        k = self._kind()
        if k in ("KW_PRINT", "KW_FOR"):
            return True
        if k != "ID":
            return False
        lex = self._current().get("lexeme", "") or ""
        if self._at(self.pos + 1).get("kind") == "LPAREN":
            return True
        if self._is_near_keyword(lex, "print") or self._is_near_keyword(lex, "for"):
            return True
        return self._peek_joined_ids_near_keyword("print") or self._peek_joined_ids_near_keyword("for")

    def _skip_split_range_tail(self):
        # Пример: 1:5@0 -> после лексера это INT(5), INT(0), RPAREN.
        # В таком случае "0" — хвост поврежденного числа, уже покрытый
        # лексической ошибкой по недопустимому символу, поэтому не создаем
        # каскад синтаксических ошибок в заголовке for.
        if self._kind() != "INT":
            return
        if self._at(self.pos + 1).get("kind") == "RPAREN":
            self.pos += 1

    def _add_syn_range_expected_int(self, tok, shown: str) -> None:
        frag = (shown or "?")[:32]
        self._add_error(
            int(tok.get("line", 1)),
            int(tok.get("col", 1)),
            "syn_err_range_expected_int",
            (frag,),
            frag,
            max(len(frag), 1),
        )

    def _parse_range_end_integer(self, anchor_tok) -> int | None:
        if self._kind() == "INT":
            end_tok = self._current()
            end_lex = end_tok.get("lexeme", "") or ""
            self.pos += 1
            return int(end_lex) if end_lex.isdigit() else None
        if self._kind() == "FLOAT":
            t = self._current()
            lex = (t.get("lexeme", "") or "").strip()
            self._add_syn_range_expected_int(t, lex or "?")
            self.pos += 1
            return None
        if self._kind() in ("KW_FOR", "KW_PRINT", "KW_IN", "ID", "SEMI"):
            t = self._current()
            shown = (t.get("lexeme") or "").strip() or self._kind()
            self._add_syn_range_expected_int(t, shown[:32])
            self.pos += 1
            return None
        if self._kind() in ("RPAREN", "EOF"):
            cl = int(anchor_tok.get("end_col", anchor_tok.get("col", 1))) + 1
            self._add_error(
                int(anchor_tok.get("line", 1)),
                cl,
                "syn_err_range_missing_end",
                (),
                "",
                0,
            )
        return None

    def _parse_for_range_bounds(self) -> tuple[int | None, int | None, bool]:
        """Возвращает (нижняя граница, верхняя, пропустить проверку m < n)."""
        start_num: int | None = None
        end_num: int | None = None
        skip_bounds_order = False

        # for (i in :10) / for (i in :)
        if self._kind() == "COLON":
            t = self._current()
            self._add_error(
                int(t.get("line", 1)),
                int(t.get("col", 1)),
                "syn_err_range_missing_start",
                (),
                "",
                0,
            )
            self.pos += 1
            end_num = self._parse_range_end_integer(t)
            self._skip_split_range_tail()
            return start_num, end_num, skip_bounds_order

        # for (i in 1.1:10) — вещественная нижняя граница
        if self._kind() == "FLOAT":
            t = self._current()
            lex = (t.get("lexeme", "") or "").strip()
            self._add_syn_range_expected_int(t, lex or "?")
            self.pos += 1
            skip_bounds_order = True
            if self._match("COLON"):
                prev = self._at(self.pos - 1)
                end_num = self._parse_range_end_integer(prev)
                self._skip_split_range_tail()
            return start_num, end_num, skip_bounds_order

        if self._kind() != "INT":
            self._expect_failed("sym_integer", "ctx_range_start")
            if self._kind() not in ("RPAREN", "EOF"):
                self.pos += 1
            return start_num, end_num, skip_bounds_order

        start_tok = self._current()
        start_lex = start_tok.get("lexeme", "") or ""
        if start_lex.isdigit():
            start_num = int(start_lex)
        self.pos += 1

        if self._match("COLON"):
            prev = self._at(self.pos - 1)
            end_num = self._parse_range_end_integer(prev)
            self._skip_split_range_tail()
            return start_num, end_num, skip_bounds_order

        line_no = int(start_tok.get("line", 1))

        # «1з10»: лексер даёт ID «з10» — одна ошибка «ожидалось :», верхняя граница из суффикса цифр.
        if self._kind() == "ID":
            tid = self._current()
            raw = (tid.get("lexeme") or "").strip()
            m = re.fullmatch(r"(\D+)(\d+)", raw)
            if m and int(tid.get("line", 1)) == line_no:
                bad_part = m.group(1) or raw
                disp = bad_part[:32]
                self._add_error(
                    int(tid.get("line", 1)),
                    int(tid.get("col", 1)),
                    "syn_err_range_expected_colon_got",
                    (disp,),
                    disp,
                    max(len(disp), 1),
                )
                self.pos += 1
                end_num = int(m.group(2))
                self._skip_split_range_tail()
                return start_num, end_num, skip_bounds_order

        # Между нижней INT и верхней INT на той же строке не «:», а любой набор токенов — одна ошибка «ожидалось :».
        j = self.pos
        gather: list[str] = []
        while j < len(self.tokens):
            tj = self._at(j)
            if int(tj.get("line", 1)) != line_no:
                break
            if tj.get("kind") == "INT":
                break
            k = tj.get("kind")
            if k in ("RPAREN", "EOF"):
                break
            if k == "LBRACE":
                break
            lx = (tj.get("lexeme") or "").strip()
            if not lx:
                lx = {
                    "SEMI": ";",
                    "ASSIGN": "=",
                    "COLON": ":",
                    "LPAREN": "(",
                    "RPAREN": ")",
                    "RBRACE": "}",
                    "LBRACE": "{",
                }.get(k, k or "?")
            gather.append(str(lx)[:32])
            j += 1
        if j < len(self.tokens) and self._at(j).get("kind") == "INT" and j > self.pos:
            up_tok = self._at(j)
            if int(up_tok.get("line", 1)) == line_no:
                first_bad = self._at(self.pos)
                disp = ("".join(gather))[:64] if gather else "?"
                disp_show = disp[:32]
                self._add_error(
                    int(first_bad.get("line", 1)),
                    int(first_bad.get("col", 1)),
                    "syn_err_range_expected_colon_got",
                    (disp,),
                    disp_show,
                    max(len(disp_show), 1),
                )
                self.pos = j + 1
                elx = up_tok.get("lexeme") or ""
                end_num = int(elx) if elx.isdigit() else None
                self._skip_split_range_tail()
                return start_num, end_num, skip_bounds_order

        # «1:for)» — один токен вместо «:» и верхней границы, дальше не INT (например ключевое слово).
        if gather:
            ft = self._at(self.pos)
            if len(gather) == 1 and ft.get("kind") in ("KW_FOR", "KW_PRINT", "KW_IN"):
                disp = ((ft.get("lexeme") or "").strip() or ft.get("kind") or "?")[:32]
                self._add_syn_range_expected_int(ft, disp)
                self.pos += 1
                return start_num, None, True

        # Два целых подряд без «:»: «1 10» или «1,1»
        if self._kind() == "INT":
            next_tok = self._current()
            sep = self._source_between_tokens(start_tok, next_tok)
            same_line = int(next_tok.get("line", 1)) == int(start_tok.get("line", 1))
            has_noise = self._has_lex_error_between(start_tok, next_tok)
            bad_sep = bool(sep) and ("," in sep or "." in sep)
            if same_line and (has_noise or bad_sep):
                bad = (sep.strip() if sep.strip() else ",")[:24]
                err_col = self._first_lex_col_between(start_tok, next_tok) or (
                    int(start_tok.get("end_col", start_tok.get("col", 1))) + 1
                )
                self._add_error(
                    int(start_tok.get("line", 1)),
                    err_col,
                    "syn_err_range_expected_int",
                    (bad,),
                    bad,
                    max(len(bad), 1),
                )
                self._suppress_lex_errors_between(start_tok, next_tok)
                self.pos += 1
                skip_bounds_order = True
                if self._match("COLON"):
                    prev = self._at(self.pos - 1)
                    end_num = self._parse_range_end_integer(prev)
                    self._skip_split_range_tail()
                return None, end_num, skip_bounds_order

            self._add_error(
                int(start_tok.get("line", 1)),
                int(start_tok.get("end_col", start_tok.get("col", 1))) + 1,
                "syn_err_range_missing_colon_between",
                (),
                "",
                0,
            )
            end_tok = self._current()
            end_lex = end_tok.get("lexeme", "") or ""
            if end_lex.isdigit():
                end_num = int(end_lex)
            self.pos += 1
            return start_num, end_num, skip_bounds_order

        self._add_error(
            int(start_tok.get("line", 1)),
            int(start_tok.get("end_col", start_tok.get("col", 1))) + 1,
            "syn_err_range_missing_colon_in_literal",
            (start_lex,),
            "",
            0,
        )
        self._add_error(
            int(start_tok.get("line", 1)),
            int(start_tok.get("end_col", start_tok.get("col", 1))),
            "syn_err_range_missing_upper_bound",
            (start_lex,),
            "",
            0,
        )
        return start_num, end_num, skip_bounds_order

    def _consume_damaged_in_splits(self) -> bool:
        cur = self._current()
        if cur.get("kind") != "ID":
            return False
        cur_lex = (cur.get("lexeme", "") or "")
        if cur_lex == "in":
            self.pos += 1
            return True

        # Случай i@n / i"n: лексер часто разбивает на ID('i') и ID('n')
        # с лексической ошибкой между ними; считаем это восстановленным 'in'.
        if cur_lex == "i":
            nxt = self._at(self.pos + 1)
            if (
                nxt.get("kind") == "ID"
                and (nxt.get("lexeme", "") or "") == "n"
                and self._has_lex_error_between(cur, nxt)
            ):
                shown = self._extract_source_fragment(cur, nxt) or "i...n"
                self._add_keyword_typo_error("in", shown)
                self.pos += 2
                return True
        if cur_lex == "n":
            prev = self._at(self.pos - 1)
            if (
                prev.get("kind") == "ID"
                and (prev.get("lexeme", "") or "") == "i"
                and self._has_lex_error_between(prev, cur)
            ):
                shown = self._extract_source_fragment(prev, cur) or "i...n"
                self._add_keyword_typo_error("in", shown)
                self.pos += 1
                return True
        return False

    def _skip_duplicated_keyword_after_lex_error(self, keyword: str):
        if self.pos <= 0:
            return
        cur = self._current()
        prev = self._at(self.pos - 1)
        if not self._token_is_keyword_like(prev, keyword):
            return
        if not self._token_is_keyword_like(cur, keyword):
            return
        if self._has_lex_error_between(prev, cur):
            self.pos += 1

    @staticmethod
    def _token_is_keyword_like(tok, keyword: str) -> bool:
        kind = tok.get("kind")
        if kind == ("KW_" + keyword.upper()):
            return True
        return kind == "ID" and (tok.get("lexeme", "") or "") == keyword

    def _has_lex_error_between(self, left_tok, right_tok) -> bool:
        left_line = int(left_tok.get("line", 1))
        right_line = int(right_tok.get("line", 1))
        if left_line != right_line:
            return False
        left_end = int(left_tok.get("end_col", left_tok.get("col", 1)))
        right_col = int(right_tok.get("col", 1))
        for col in self._lex_error_cols.get(left_line, []):
            if left_end < col < right_col:
                return True
        return False

    def _consume_near_keyword(self, keyword: str) -> bool:
        t = self._current()
        if t.get("kind") != "ID":
            return False

        lex = t.get("lexeme", "") or ""
        if lex == keyword:
            self.pos += 1
            return True

        # Склейка из двух одинаковых ключевых слов: forfor, printprint.
        if lex == keyword * 2:
            self._add_duplicate_fragment_error(t, lex)
            self.pos += 1
            return True

        # Частичный дубль, например rintprint (почти "print" + "print").
        if len(lex) > len(keyword) and lex.endswith(keyword):
            head = lex[:-len(keyword)]
            if self._is_near_keyword(head, keyword):
                self._add_duplicate_fragment_error(t, lex)
                self.pos += 1
                return True

        joined = lex
        parts = [lex]
        consumed = 1
        line = t.get("line")
        prev = t
        had_lex_noise = False
        max_parts = min(len(keyword) + 1, 6)
        while consumed < max_parts:
            nxt = self._at(self.pos + consumed)
            if nxt.get("kind") != "ID" or nxt.get("line") != line:
                break
            gap = int(nxt.get("col", 0)) - int(prev.get("end_col", prev.get("col", 0)))
            # Между частями слова могут быть шумовые символы (например, '@', '#'),
            # поэтому допускаем небольшой разрыв по позиции.
            if gap < 1 or gap > 4:
                break
            joined += (nxt.get("lexeme", "") or "")
            parts.append(nxt.get("lexeme", "") or "")
            if gap > 1:
                had_lex_noise = True
            if self._has_lex_error_between(prev, nxt):
                had_lex_noise = True
            consumed += 1
            prev = nxt
            if self._is_near_keyword(joined, keyword):
                if joined != keyword or had_lex_noise:
                    shown = self._extract_source_fragment(t, nxt)
                    if not shown:
                        shown = joined if joined != keyword else ("...".join(parts))
                    self._add_keyword_typo_error(keyword, shown)
                self.pos += consumed
                return True

        # Если собрать ключевое слово из соседних ID не удалось, пробуем
        # одиночный почти-совпадающий токен (например, f@o -> fo).
        if self._is_near_keyword(lex, keyword):
            if lex != keyword:
                self._add_keyword_typo_error(keyword, lex)
            self.pos += 1
            return True

        # Поддержка склеенных ключевых слов вроде "forfor", "printprint":
        # считаем это одной ошибкой по ключевому слову и продолжаем разбор
        # по соответствующей грамматической ветке.
        if lex.startswith(keyword) and len(lex) > len(keyword):
            self._add_keyword_typo_error(keyword, lex)
            self.pos += 1
            return True

        return False

    @staticmethod
    def _is_near_keyword(word: str, keyword: str) -> bool:
        if not word:
            return False
        if word == keyword:
            return True
        if abs(len(word) - len(keyword)) > 1:
            return False
        i = j = edits = 0
        while i < len(word) and j < len(keyword):
            if word[i] == keyword[j]:
                i += 1
                j += 1
                continue
            edits += 1
            if edits > 1:
                return False
            if len(word) == len(keyword):
                i += 1
                j += 1
            elif len(word) > len(keyword):
                i += 1
            else:
                j += 1
        edits += (len(word) - i) + (len(keyword) - j)
        return edits <= 1

    def _synchronize_in_block(self):
        self._skip_error_token()
        while self._kind() not in ("RBRACE", "EOF", "SEMI", "KW_FOR", "KW_PRINT", "ID"):
            self.pos += 1
        if self._kind() == "SEMI":
            self.pos += 1

    def _synchronize_to_rbrace(self):
        while self._kind() not in ("RBRACE", "EOF"):
            self.pos += 1
        if self._kind() == "RBRACE":
            self.pos += 1
        if self._kind() == "SEMI":
            self.pos += 1

    def _synchronize_for_header(self):
        checkpoints = ("LBRACE", "SEMI", "RBRACE", "EOF", "KW_CONST", "KW_VAR", "KW_FOR")
        # Если уже стоим на чекпоинте (например, сразу на '{' после ошибки в ')'),
        # не пропускаем его — пытаемся восстановить структуру цикла дальше.
        if self._kind() not in checkpoints:
            self._skip_error_token()
        while self._kind() not in checkpoints:
            self.pos += 1
        if self._kind() == "SEMI":
            self.pos += 1

    def _try_parse_recovered_for_body(self, require_trailing_semi: bool):
        if not self._match("LBRACE"):
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
        if self.errors:
            p_line, p_col, p_key, p_args, *_ = self.errors[-1]
            if (p_line, p_col, p_key, p_args) == (line, col, key, args):
                return
        self.errors.append((line, col, key, args, fragment, frag_len))

    def _add_keyword_typo_error(self, keyword: str, shown_fragment: str):
        t = self._current()
        if keyword == "for":
            key = "syn_err_keyword_for_typo"
        elif keyword == "print":
            key = "syn_err_keyword_print_typo"
        else:
            key = "syn_err_keyword_in_typo"
        self._add_error(
            t.get("line", 1),
            t.get("col", 1),
            key,
            (shown_fragment,),
            shown_fragment[:48],
            max(len(shown_fragment), 1),
        )

    def _extract_source_fragment(self, start_tok, end_tok) -> str:
        line = int(start_tok.get("line", 1))
        if line != int(end_tok.get("line", 1)):
            return ""
        if line < 1 or line > len(self._source_lines):
            return ""
        start_col = int(start_tok.get("col", 1))
        end_col = int(end_tok.get("end_col", end_tok.get("col", 1)))
        if end_col < start_col:
            return ""
        line_text = self._source_lines[line - 1]
        # col -> 1-based, slice -> 0-based inclusive end
        return line_text[start_col - 1:end_col]

    def _add_duplicate_fragment_error(self, tok, fragment: str):
        self._add_error(
            tok.get("line", 1),
            tok.get("col", 1),
            "syn_err_duplicate_fragment",
            (fragment,),
            fragment[:48],
            max(len(fragment), 1),
        )

    def _consume_duplicate_keyword_tokens(self, keyword: str) -> None:
        if not self._token_is_keyword_like(self._current(), keyword):
            return
        t = self._current()
        self._add_error(
            int(t.get("line", 1)),
            int(t.get("col", 1)),
            "syn_err_duplicate_kw_consecutive",
            (keyword,),
            keyword,
            len(keyword),
        )
        while self._token_is_keyword_like(self._current(), keyword):
            self.pos += 1

    def _skip_error_token(self):
        # Сдвиг после фиксации ошибки предотвращает повтор одной и той же диагностики.
        if self._kind() != "EOF":
            self.pos += 1

    def _synchronize_irons(self):
        self._skip_error_token()
        while self._kind() not in ("SEMI", "EOF", "KW_CONST", "KW_VAR", "KW_FOR"):
            self.pos += 1
        if self._kind() == "SEMI":
            self.pos += 1
