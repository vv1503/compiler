class LexicalAnalyzer:
    
    def __init__(self):
        self.keywords = {
            "for": "ключевое слово",
            "in": "ключевое слово",
            "print": "ключевое слово",
            "const": "ключевое слово",
            "var": "ключевое слово",
        }
        self.operators = {
            ":": "оператор диапазона",
            "=": "оператор присваивания",
        }
        self.separators = {
            "(": "разделитель",
            ")": "разделитель",
            "{": "разделитель",
            "}": "разделитель",
            ";": "конец оператора",
        }

    def analyze(self, text: str):
        tokens = []
        errors = []
        i = 0
        n = len(text)
        line_num = 1
        char_pos = 1

        def append_token(code, token_type, lexeme, kind, start_line, start_col, end_col=None):
            loc_end = end_col if end_col is not None else start_col + max(len(lexeme) - 1, 0)
            tokens.append({
                "code": code,
                "type": token_type,
                "lexeme": lexeme,
                "location": f"строка {start_line},{start_col}-{loc_end}",
                "kind": kind,
                "line": start_line,
                "col": start_col,
                "end_col": loc_end,
            })

        while i < n:
            ch = text[i]
            start_line = line_num
            start_pos = char_pos

            if ch.isspace():
                code = 11
                if ch == " ":
                    lexeme = "(пробел)"
                    token_type = "разделитель (пробел)"
                elif ch == "\n":
                    lexeme = "(перевод строки)"
                    token_type = "разделитель (перевод строки)"
                    line_num += 1
                    char_pos = 0
                elif ch == "\t":
                    lexeme = "(табуляция)"
                    token_type = "разделитель (табуляция)"
                else:
                    lexeme = "(пробел)"
                    token_type = "разделитель (пробел)"

                append_token(code, token_type, lexeme, "WS", start_line, start_pos, start_pos)
                i += 1
                char_pos += 1
                continue

            if ch.isalpha() or ch == "_":
                lexeme = ""
                while i < n and (text[i].isalnum() or text[i] == "_"):
                    lexeme += text[i]
                    i += 1
                    char_pos += 1
                token_type = self.keywords.get(lexeme, "идентификатор")
                code = 14 if lexeme in self.keywords else 2
                kind = "KW_" + lexeme.upper() if lexeme in self.keywords else "ID"
                append_token(code, token_type, lexeme, kind, start_line, start_pos, char_pos - 1)
                continue

            if ch.isdigit():
                lexeme = ""
                while i < n and text[i].isdigit():
                    lexeme += text[i]
                    i += 1
                    char_pos += 1
                if i < n and text[i] == ".":
                    lexeme += text[i]
                    i += 1
                    char_pos += 1
                    while i < n and text[i].isdigit():
                        lexeme += text[i]
                        i += 1
                        char_pos += 1
                    append_token(3, "вещественное без знака", lexeme, "FLOAT", start_line, start_pos, char_pos - 1)
                else:
                    append_token(1, "целое без знака", lexeme, "INT", start_line, start_pos, char_pos - 1)
                continue

            if ch == ".":
                dot_line, dot_col = line_num, char_pos
                if i + 1 < n and text[i + 1].isdigit():
                    prev_is_digit = i > 0 and text[i - 1].isdigit()
                    if not prev_is_digit:
                        errors.append((
                            dot_line,
                            dot_col,
                            "lex_err_digit_before_dot",
                            (),
                            ".",
                            1,
                        ))
                    j = i + 1
                    frac = ""
                    while j < n and text[j].isdigit():
                        frac += text[j]
                        j += 1
                    synthetic = "0." + frac
                    end_col = char_pos + (j - i) - 1
                    append_token(3, "вещественное без знака", synthetic, "FLOAT", start_line, start_pos, end_col)
                    char_pos = end_col + 1
                    i = j
                    continue
                errors.append((
                    dot_line,
                    dot_col,
                    "lex_err_lonely_dot",
                    (),
                    ".",
                    1,
                ))
                append_token(3, "вещественное без знака", "0.0", "FLOAT", start_line, start_pos, start_pos)
                i += 1
                char_pos += 1
                continue

            if ch in self.operators:
                kind = "ASSIGN" if ch == "=" else "COLON"
                append_token(10, self.operators[ch], ch, kind, start_line, start_pos, start_pos)
                i += 1
                char_pos += 1
                continue

            if ch in self.separators:
                sep_kind = {
                    "(": "LPAREN",
                    ")": "RPAREN",
                    "{": "LBRACE",
                    "}": "RBRACE",
                    ";": "SEMI",
                }[ch]
                append_token(16, self.separators[ch], ch, sep_kind, start_line, start_pos, start_pos)
                i += 1
                char_pos += 1
                continue

            errors.append((line_num, char_pos, "lex_err_bad_char", (ch,), ch, 1))
            i += 1
            char_pos += 1

        return tokens, self._merge_keyword_noise_lexical_errors(text, tokens, errors)

    @staticmethod
    def _merge_keyword_noise_lexical_errors(text, tokens, errors):
        """Объединяет отдельные lex_err_bad_char в более понятные сообщения (for@for, i@n)."""
        if not text or not errors:
            return errors
        lines = text.splitlines()
        nt = [t for t in tokens if t.get("kind") != "WS"]
        merged = []
        used = set()
        for ei, err in enumerate(errors):
            if ei in used:
                continue
            if len(err) < 6:
                merged.append(err)
                continue
            line, col, key, args, frag, flen = err
            if key != "lex_err_bad_char" or not args:
                merged.append(err)
                continue
            ch = args[0]
            L = int(line)
            C = int(col)
            if L < 1 or L > len(lines):
                merged.append(err)
                continue
            line_text = lines[L - 1]
            prev_tok = None
            next_tok = None
            for t in nt:
                tl = int(t.get("line", 1))
                if tl != L:
                    continue
                te = int(t.get("end_col", t.get("col", 1)))
                tc = int(t.get("col", 1))
                if te < C:
                    prev_tok = t
                elif tc > C and next_tok is None:
                    next_tok = t
                    break
            if prev_tok is not None and next_tok is not None:
                pk = prev_tok.get("kind")
                nk = next_tok.get("kind")
                ple = int(prev_tok.get("end_col", prev_tok.get("col", 1)))
                nsc = int(next_tok.get("col", 1))
                nen = int(next_tok.get("end_col", next_tok.get("col", 1)))
                if (
                    pk == "KW_FOR"
                    and nk == "KW_FOR"
                    and (prev_tok.get("lexeme") or "") == "for"
                    and (next_tok.get("lexeme") or "") == "for"
                    and ple < C < nsc
                ):
                    frag_span = line_text[ple:nen] if nen > ple else "@for"
                    fs = frag_span if frag_span.strip() else "@for"
                    merged.append(
                        (
                            L,
                            C,
                            "lex_err_noise_duplicate_kw",
                            (fs, "for"),
                            fs,
                            max(len(fs), 1),
                        )
                    )
                    used.add(ei)
                    continue
                if (
                    pk == "ID"
                    and nk == "ID"
                    and (prev_tok.get("lexeme") or "") == "i"
                    and (next_tok.get("lexeme") or "") == "n"
                    and ple < C < nsc
                ):
                    merged.append(
                        (
                            L,
                            C,
                            "lex_err_noise_inside_in",
                            (ch,),
                            ch,
                            1,
                        )
                    )
                    used.add(ei)
                    continue
            merged.append(err)
        return merged
