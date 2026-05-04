from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Token:
    kind: str  # NUM, ID, PLUS, MINUS, MUL, DIV, LPAREN, RPAREN, EOF
    lexeme: str
    line: int
    col: int


def tokenize(text: str) -> Tuple[List[Token], List[Tuple[int, int, str, str]]]:
    """
    Лексический анализ. Ошибки: (line, col, code, message).
    id: letter {letter | digit | _ | .}
    num: digit {digit}
    """
    errors: List[Tuple[int, int, str, str]] = []
    tokens: List[Token] = []
    i = 0
    n = len(text)
    line = 1
    col = 1

    def eat_one():
        nonlocal i, line, col
        if i >= n:
            return
        if text[i] == "\n":
            line += 1
            col = 1
        else:
            col += 1
        i += 1

    while i < n:
        ch = text[i]
        if ch.isspace():
            eat_one()
            continue

        start_line, start_col = line, col

        if ch.isdigit():
            num_start = i
            while i < n and text[i].isdigit():
                eat_one()
            lex = text[num_start:i]
            nxt = text[i] if i < n else ""
            if nxt.isalpha() or nxt == "_" or nxt == ".":
                bad_tail = lex
                while i < n and (text[i].isalnum() or text[i] in "._"):
                    bad_tail += text[i]
                    eat_one()
                errors.append(
                    (
                        start_line,
                        start_col,
                        "lex_bad_id_start",
                        f"идентификатор не может начинаться с цифры (фрагмент «{bad_tail}»)",
                    )
                )
                continue
            tokens.append(Token("NUM", lex, start_line, start_col))
            continue

        if ch.isalpha():
            id_start = i
            while i < n and (text[i].isalnum() or text[i] in "._"):
                eat_one()
            lex = text[id_start:i]
            tokens.append(Token("ID", lex, start_line, start_col))
            continue

        if ch == "(":
            eat_one()
            tokens.append(Token("LPAREN", "(", start_line, start_col))
            continue
        if ch == ")":
            eat_one()
            tokens.append(Token("RPAREN", ")", start_line, start_col))
            continue
        if ch == "+":
            eat_one()
            tokens.append(Token("PLUS", "+", start_line, start_col))
            continue
        if ch == "-":
            eat_one()
            tokens.append(Token("MINUS", "-", start_line, start_col))
            continue
        if ch == "*":
            eat_one()
            tokens.append(Token("MUL", "*", start_line, start_col))
            continue
        if ch == "/":
            eat_one()
            tokens.append(Token("DIV", "/", start_line, start_col))
            continue

        errors.append(
            (line, col, "lex_bad_char", f"недопустимый символ «{ch}»"),
        )
        eat_one()

    tokens.append(Token("EOF", "", line, col))
    return tokens, errors


def _prec(op: str) -> int:
    if op in ("*", "/"):
        return 2
    if op in ("+", "-"):
        return 1
    return 0


def infix_to_rpn(tokens: List[Token]) -> List[str]:
    """Алгоритм Дейкстры (сортировочная станция), только лексемы выражения без EOF."""
    out: List[str] = []
    stack: List[str] = []
    for t in tokens:
        if t.kind == "NUM":
            out.append(t.lexeme)
        elif t.kind == "ID":
            out.append(t.lexeme)
        elif t.kind in ("PLUS", "MINUS", "MUL", "DIV"):
            op = t.lexeme
            while stack and stack[-1] != "(" and _prec(stack[-1]) >= _prec(op):
                out.append(stack.pop())
            stack.append(op)
        elif t.kind == "LPAREN":
            stack.append("(")
        elif t.kind == "RPAREN":
            while stack and stack[-1] != "(":
                out.append(stack.pop())
            if stack and stack[-1] == "(":
                stack.pop()
    while stack:
        out.append(stack.pop())
    return out


def eval_rpn(rpn: List[str]) -> int:
    st: List[int] = []
    for x in rpn:
        if x in ("+", "-", "*", "/"):
            b = st.pop()
            a = st.pop()
            if x == "+":
                st.append(a + b)
            elif x == "-":
                st.append(a - b)
            elif x == "*":
                st.append(a * b)
            else:
                if b == 0:
                    raise ZeroDivisionError("деление на ноль")
                st.append(a // b)
        else:
            st.append(int(x))
    if len(st) != 1:
        raise ValueError("некорректное ПОЛИЗ")
    return st[0]


class ExprParser:
    """
    E -> T A
    A -> ε | + T A | - T A
    T -> F B
    B -> ε | * F B | / F B
    F -> num | id | ( E )
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.errors: List[Tuple[int, int, str, str]] = []
        self.quads: List[Tuple[str, str, str, str]] = []
        self._tmp = 0

    def _cur(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def _adv(self):
        if self.pos < len(self.tokens) - 1:
            self.pos += 1

    def _new_temp(self) -> str:
        self._tmp += 1
        return f"t{self._tmp}"

    def _err(self, line: int, col: int, code: str, msg: str):
        self.errors.append((line, col, code, msg))

    def parse(self) -> Optional[str]:
        """Возвращает имя результата (операнд или tN) при успехе."""
        if self._cur().kind == "EOF":
            self._err(self._cur().line, self._cur().col, "syn_missing_operand", "пропущен операнд (ожидалось выражение)")
            return None
        v = self._parse_e()
        if v is None:
            return None
        t = self._cur()
        if t.kind != "EOF":
            if t.kind == "RPAREN":
                self._err(t.line, t.col, "syn_extra_paren", "лишняя закрывающая скобка или лишние символы")
            else:
                self._err(t.line, t.col, "syn_trailing", "лишние символы после корректного выражения")
            return None
        return v

    def _parse_e(self) -> Optional[str]:
        left = self._parse_t()
        if left is None:
            return None
        return self._parse_a(left)

    def _parse_a(self, left: str) -> Optional[str]:
        while True:
            t = self._cur()
            if t.kind == "PLUS":
                self._adv()
                r = self._parse_t()
                if r is None:
                    return None
                res = self._new_temp()
                self.quads.append(("+", left, r, res))
                left = res
                continue
            if t.kind == "MINUS":
                self._adv()
                r = self._parse_t()
                if r is None:
                    return None
                res = self._new_temp()
                self.quads.append(("-", left, r, res))
                left = res
                continue
            return left

    def _parse_t(self) -> Optional[str]:
        left = self._parse_f()
        if left is None:
            return None
        return self._parse_b(left)

    def _parse_b(self, left: str) -> Optional[str]:
        while True:
            t = self._cur()
            if t.kind == "MUL":
                self._adv()
                r = self._parse_f()
                if r is None:
                    return None
                res = self._new_temp()
                self.quads.append(("*", left, r, res))
                left = res
                continue
            if t.kind == "DIV":
                self._adv()
                r = self._parse_f()
                if r is None:
                    return None
                res = self._new_temp()
                self.quads.append(("/", left, r, res))
                left = res
                continue
            return left

    def _parse_f(self) -> Optional[str]:
        t = self._cur()
        if t.kind == "NUM":
            self._adv()
            return t.lexeme
        if t.kind == "ID":
            self._adv()
            return t.lexeme
        if t.kind == "LPAREN":
            self._adv()
            inner = self._parse_e()
            if inner is None:
                return None
            if self._cur().kind != "RPAREN":
                self._err(
                    self._cur().line,
                    self._cur().col,
                    "syn_missing_rparen",
                    "пропущена закрывающая скобка «)»",
                )
                return None
            self._adv()
            return inner
        if t.kind in ("PLUS", "MINUS", "MUL", "DIV", "RPAREN", "EOF"):
            self._err(t.line, t.col, "syn_missing_operand", "пропущен операнд")
            return None
        self._err(t.line, t.col, "syn_missing_operand", "пропущен операнд")
        return None


def _expr_tokens_no_eof(tokens: List[Token]) -> List[Token]:
    return [t for t in tokens if t.kind != "EOF"]


def expression_has_only_integers(tokens: List[Token]) -> bool:
    for t in tokens:
        if t.kind == "ID":
            return False
    return True


def analyze_expression(source: str) -> dict:
    """
    Полный цикл: лексика -> при ошибках предупреждение о тетрадах/ПОЛИЗ;
    синтаксис -> тетрады; ПОЛИЗ и значение только для цепочки из целых чисел.
    """
    src = source.rstrip("\n")
    tokens, lex_err = tokenize(src)
    result = {
        "source": source,
        "tokens": tokens,
        "lex_errors": lex_err,
        "syn_errors": [],
        "quads": [],
        "poliz": None,
        "poliz_str": None,
        "value": None,
        "value_error": None,
        "warnings": [],
    }

    if lex_err:
        result["warnings"].append(
            "При наличии лексических ошибок тетрады и ПОЛИЗ не строятся.",
        )
        return result

    parser = ExprParser(tokens)
    place = parser.parse()
    result["syn_errors"] = parser.errors

    if parser.errors:
        result["warnings"].append(
            "При наличии синтаксических ошибок тетрады и ПОЛИЗ не строятся.",
        )
        return result

    result["quads"] = list(parser.quads)
    expr_toks = _expr_tokens_no_eof(tokens)

    if not expression_has_only_integers(tokens):
        result["warnings"].append(
            "Выражение содержит идентификаторы: ПОЛИЗ и численное значение не формируются (только тетрады).",
        )
        return result

    rpn = infix_to_rpn(expr_toks)
    result["poliz"] = rpn
    result["poliz_str"] = " ".join(rpn)
    try:
        result["value"] = eval_rpn(rpn)
    except ZeroDivisionError as e:
        result["value_error"] = str(e)
    except Exception as e:
        result["value_error"] = str(e)

    return result


def format_report(r: dict) -> str:
    lines: List[str] = []
    lines.append("=== Лексемы ===")
    for t in r["tokens"]:
        if t.kind == "EOF":
            lines.append(f"EOF @ {t.line},{t.col}")
        else:
            lines.append(f"{t.kind:6} {t.lexeme!r} @ {t.line},{t.col}")

    if r["lex_errors"]:
        lines.append("\n=== Лексические ошибки ===")
        for line, col, code, msg in r["lex_errors"]:
            lines.append(f"строка {line}, позиция {col}: [{code}] {msg}")

    if r["syn_errors"]:
        lines.append("\n=== Синтаксические ошибки ===")
        for line, col, code, msg in r["syn_errors"]:
            lines.append(f"строка {line}, позиция {col}: [{code}] {msg}")

    for w in r["warnings"]:
        lines.append(f"\n>>> {w}")

    if r["quads"]:
        lines.append("\n=== Тетрады (op, arg1, arg2, result) ===")
        for i, q in enumerate(r["quads"], 1):
            lines.append(f"{i:3}  ({q[0]}, {q[1]}, {q[2]}, {q[3]})")

    if r.get("poliz_str"):
        lines.append("\n=== ПОЛИЗ ===")
        lines.append(r["poliz_str"])
    if r.get("value") is not None:
        lines.append(f"\nЗначение (целые): {r['value']}")
    if r.get("value_error"):
        lines.append(f"\nОшибка вычисления: {r['value_error']}")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    s = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else input("Выражение: ").strip()
    print(format_report(analyze_expression(s)))
