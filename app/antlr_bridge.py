from __future__ import annotations

from antlr4 import InputStream, CommonTokenStream, Token
from antlr4.error.ErrorListener import ErrorListener

from antlr_generated.MiniRLexer import MiniRLexer
from antlr_generated.MiniRParser import MiniRParser


def _type_name(lex: MiniRLexer, t: int) -> str:
    m = {
        lex.FOR: "ключевое слово",
        lex.IN: "ключевое слово",
        lex.PRINT: "ключевое слово",
        lex.CONST: "ключевое слово",
        lex.VAR: "ключевое слово",
        lex.ASSIGN: "оператор присваивания",
        lex.SEMI: "конец оператора",
        lex.LPAREN: "разделитель",
        lex.RPAREN: "разделитель",
        lex.LBRACE: "разделитель",
        lex.RBRACE: "разделитель",
        lex.COLON: "оператор диапазона",
        lex.FLOAT: "вещественное без знака",
        lex.INT: "целое без знака",
        lex.ID: "идентификатор",
    }
    return m.get(t, "лексема")


class _CollectLexerErrors(ErrorListener):
    def __init__(self):
        self.items: list[tuple[int, int, str, tuple, str, int]] = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        col = column + 1 if column is not None else 1
        frag = ""
        if offendingSymbol is not None and hasattr(offendingSymbol, "text"):
            frag = offendingSymbol.text or ""
        elif offendingSymbol is not None:
            frag = str(offendingSymbol)
        flen = max(len(frag), 1) if frag else 1
        self.items.append((line, col, "antlr_lexer_err", (msg,), frag[:32] if frag else "?", flen))


class _CollectParserErrors(ErrorListener):
    def __init__(self):
        self.items: list[tuple[int, int, str, tuple, str, int]] = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        col = column + 1 if column is not None else 1
        frag = ""
        if offendingSymbol is not None and hasattr(offendingSymbol, "text"):
            frag = offendingSymbol.text or ""
        flen = max(len(frag), 1) if frag else 1
        self.items.append((line, col, "antlr_parse_err", (msg,), frag[:32] if frag else "?", flen))


def antlr_analyze(text: str):
    inp = InputStream(text)
    lexer = MiniRLexer(inp)
    lexer.removeErrorListeners()
    lex_listener = _CollectLexerErrors()
    lexer.addErrorListener(lex_listener)

    stream = CommonTokenStream(lexer)
    stream.fill()

    tokens_out = []
    for tok in stream.tokens:
        if tok.type == Token.EOF:
            continue
        if tok.channel != Token.DEFAULT_CHANNEL:
            continue
        if tok.type in (MiniRLexer.WS, MiniRLexer.LINE_COMMENT):
            continue

        lexeme = tok.text or ""
        line = tok.line
        col = tok.column + 1
        end_col = col + len(lexeme) - 1 if lexeme else col

        tokens_out.append({
            "code": tok.type,
            "type": _type_name(lexer, tok.type),
            "lexeme": lexeme,
            "line": line,
            "col": col,
            "end_col": end_col,
        })

    stream.seek(0)

    parser = MiniRParser(stream)
    parser.removeErrorListeners()
    par_listener = _CollectParserErrors()
    parser.addErrorListener(par_listener)

    parser.program()

    return tokens_out, lex_listener.items, par_listener.items
