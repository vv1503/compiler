from __future__ import annotations


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
        elif k == "ID" and self._consume_near_keyword("for"):
            self._parse_for_stmt_core(require_trailing_semi=True, typo_recovered=True)
        elif k == "LPAREN":
            # Восстановление: пропущено ключевое слово for перед заголовком "(...)"
            self._expect_failed("for", "")
            self._parse_for_stmt_core(
                require_trailing_semi=True,
                typo_recovered=True,
                suppress_in_without_loop_var=True,
            )
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
        self._parse_for_stmt_core(require_trailing_semi=require_trailing_semi, typo_recovered=False)

    def _parse_for_stmt_core(
        self,
        require_trailing_semi: bool = False,
        typo_recovered: bool = False,
        suppress_in_without_loop_var: bool = False,
    ):
        self._skip_duplicated_keyword_after_lex_error("for")
        self._consume_duplicate_keyword_tokens("for")
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
            in_ok = self._match("KW_IN") or self._consume_damaged_in_splits() or self._consume_near_keyword("in")

        if not in_ok:
            self._expect_failed("in", "ctx_after_loop_var")
            # Если вместо in пришел идентификатор (обычно хвост после
            # недопустимого символа), сдвигаемся на него один раз,
            # чтобы не вызывать каскад ошибок по заголовку for.
            if self._kind() == "ID":
                self.pos += 1

        start_num, end_num = self._parse_for_range_bounds()
        if start_num is not None and end_num is not None and start_num >= end_num:
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

        self._for_loop_var_stack.append(loop_var)
        try:
            if not self._match("LBRACE"):
                prev = self._at(self.pos - 1)
                if prev.get("kind") == "RPAREN" and not typo_recovered:
                    ln = int(prev.get("line", 1))
                    cl = int(prev.get("end_col", prev.get("col", 1))) + 1
                    self._add_error(ln, cl, "syn_err_missing_lbrace_for", (), "{", 1)
                else:
                    self._expect_failed("{", "ctx_before_loop_body")
            self._parse_block_stmt_list()
            self._expect_or_report("RBRACE", "}", "ctx_end_loop_body")
            if require_trailing_semi:
                if not self._match("SEMI"):
                    self._expect_failed(";", "ctx_after_for_brace")
                    if self._kind() == "COLON":
                        self.pos += 1
            elif self._kind() == "SEMI":
                self.pos += 1
        finally:
            self._for_loop_var_stack.pop()

    def _parse_block_stmt_list(self):
        while self._kind() not in ("RBRACE", "EOF"):
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
        if self._kind() == "SEMI":
            self.pos += 1

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

    def _looks_like_block_stmt_start(self) -> bool:
        k = self._kind()
        if k in ("KW_PRINT", "KW_FOR"):
            return True
        if k != "ID":
            return False
        lex = self._current().get("lexeme", "") or ""
        if self._at(self.pos + 1).get("kind") == "LPAREN":
            return True
        return self._is_near_keyword(lex, "print") or self._is_near_keyword(lex, "for")

    def _skip_split_range_tail(self):
        # Пример: 1:5@0 -> после лексера это INT(5), INT(0), RPAREN.
        # В таком случае "0" — хвост поврежденного числа, уже покрытый
        # лексической ошибкой по недопустимому символу, поэтому не создаем
        # каскад синтаксических ошибок в заголовке for.
        if self._kind() != "INT":
            return
        if self._at(self.pos + 1).get("kind") == "RPAREN":
            self.pos += 1

    def _parse_for_range_bounds(self):
        start_num = None
        end_num = None

        # Отсутствие начала диапазона: for (i in :10)
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
            if self._kind() == "INT":
                end_tok = self._current()
                end_lex = end_tok.get("lexeme", "") or ""
                if end_lex.isdigit():
                    end_num = int(end_lex)
                self.pos += 1
            else:
                self._add_error(
                    int(t.get("line", 1)),
                    int(t.get("col", 1)) + 1,
                    "syn_err_range_missing_end",
                    (),
                    "",
                    0,
                )
            return start_num, end_num

        if self._kind() != "INT":
            self._expect_failed("sym_integer", "ctx_range_start")
            if self._kind() not in ("RPAREN", "EOF"):
                self.pos += 1
            return start_num, end_num

        start_tok = self._current()
        start_lex = start_tok.get("lexeme", "") or ""
        if start_lex.isdigit():
            start_num = int(start_lex)
        self.pos += 1

        if self._match("COLON"):
            if self._kind() == "INT":
                end_tok = self._current()
                end_lex = end_tok.get("lexeme", "") or ""
                if end_lex.isdigit():
                    end_num = int(end_lex)
                self.pos += 1
                self._skip_split_range_tail()
                return start_num, end_num
            self._add_error(
                int(start_tok.get("line", 1)),
                int(start_tok.get("end_col", start_tok.get("col", 1))) + 1,
                "syn_err_range_missing_end",
                (),
                "",
                0,
            )
            return start_num, end_num

        # Отсутствие ':' между числами, включая случай с пробелом: "1 10"
        if self._kind() == "INT":
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
            return start_num, end_num

        # Один литерал без ':' и правой границы: "1)"
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
        return start_num, end_num

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

    def _consume_duplicate_keyword_tokens(self, keyword: str):
        while self._token_is_keyword_like(self._current(), keyword):
            tok = self._current()
            frag = (tok.get("lexeme", "") or keyword)
            self._add_duplicate_fragment_error(tok, frag)
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
