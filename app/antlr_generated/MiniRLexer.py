from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
    from typing import TextIO
else:
    from typing.io import TextIO



def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2\23")
        buf.write("|\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7")
        buf.write("\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r\4\16")
        buf.write("\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t\22\3\2\3\2")
        buf.write("\3\2\3\2\3\3\3\3\3\3\3\4\3\4\3\4\3\4\3\4\3\4\3\5\3\5\3")
        buf.write("\5\3\5\3\5\3\5\3\6\3\6\3\6\3\6\3\7\3\7\3\b\3\b\3\t\3\t")
        buf.write("\3\n\3\n\3\13\3\13\3\f\3\f\3\r\3\r\3\16\6\16L\n\16\r\16")
        buf.write("\16\16M\3\16\3\16\7\16R\n\16\f\16\16\16U\13\16\3\16\3")
        buf.write("\16\6\16Y\n\16\r\16\16\16Z\5\16]\n\16\3\17\6\17`\n\17")
        buf.write("\r\17\16\17a\3\20\3\20\7\20f\n\20\f\20\16\20i\13\20\3")
        buf.write("\21\6\21l\n\21\r\21\16\21m\3\21\3\21\3\22\3\22\3\22\3")
        buf.write("\22\7\22v\n\22\f\22\16\22y\13\22\3\22\3\22\2\2\23\3\3")
        buf.write("\5\4\7\5\t\6\13\7\r\b\17\t\21\n\23\13\25\f\27\r\31\16")
        buf.write("\33\17\35\20\37\21!\22#\23\3\2\7\3\2\62;\5\2C\\aac|\6")
        buf.write("\2\62;C\\aac|\5\2\13\f\17\17\"\"\4\2\f\f\17\17\2\u0083")
        buf.write("\2\3\3\2\2\2\2\5\3\2\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13")
        buf.write("\3\2\2\2\2\r\3\2\2\2\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3")
        buf.write("\2\2\2\2\25\3\2\2\2\2\27\3\2\2\2\2\31\3\2\2\2\2\33\3\2")
        buf.write("\2\2\2\35\3\2\2\2\2\37\3\2\2\2\2!\3\2\2\2\2#\3\2\2\2\3")
        buf.write("%\3\2\2\2\5)\3\2\2\2\7,\3\2\2\2\t\62\3\2\2\2\138\3\2\2")
        buf.write("\2\r<\3\2\2\2\17>\3\2\2\2\21@\3\2\2\2\23B\3\2\2\2\25D")
        buf.write("\3\2\2\2\27F\3\2\2\2\31H\3\2\2\2\33\\\3\2\2\2\35_\3\2")
        buf.write("\2\2\37c\3\2\2\2!k\3\2\2\2#q\3\2\2\2%&\7h\2\2&\'\7q\2")
        buf.write("\2\'(\7t\2\2(\4\3\2\2\2)*\7k\2\2*+\7p\2\2+\6\3\2\2\2,")
        buf.write("-\7r\2\2-.\7t\2\2./\7k\2\2/\60\7p\2\2\60\61\7v\2\2\61")
        buf.write("\b\3\2\2\2\62\63\7e\2\2\63\64\7q\2\2\64\65\7p\2\2\65\66")
        buf.write("\7u\2\2\66\67\7v\2\2\67\n\3\2\2\289\7x\2\29:\7c\2\2:;")
        buf.write("\7t\2\2;\f\3\2\2\2<=\7?\2\2=\16\3\2\2\2>?\7=\2\2?\20\3")
        buf.write("\2\2\2@A\7*\2\2A\22\3\2\2\2BC\7+\2\2C\24\3\2\2\2DE\7}")
        buf.write("\2\2E\26\3\2\2\2FG\7\177\2\2G\30\3\2\2\2HI\7<\2\2I\32")
        buf.write("\3\2\2\2JL\t\2\2\2KJ\3\2\2\2LM\3\2\2\2MK\3\2\2\2MN\3\2")
        buf.write("\2\2NO\3\2\2\2OS\7\60\2\2PR\t\2\2\2QP\3\2\2\2RU\3\2\2")
        buf.write("\2SQ\3\2\2\2ST\3\2\2\2T]\3\2\2\2US\3\2\2\2VX\7\60\2\2")
        buf.write("WY\t\2\2\2XW\3\2\2\2YZ\3\2\2\2ZX\3\2\2\2Z[\3\2\2\2[]\3")
        buf.write("\2\2\2\\K\3\2\2\2\\V\3\2\2\2]\34\3\2\2\2^`\t\2\2\2_^\3")
        buf.write("\2\2\2`a\3\2\2\2a_\3\2\2\2ab\3\2\2\2b\36\3\2\2\2cg\t\3")
        buf.write("\2\2df\t\4\2\2ed\3\2\2\2fi\3\2\2\2ge\3\2\2\2gh\3\2\2\2")
        buf.write("h \3\2\2\2ig\3\2\2\2jl\t\5\2\2kj\3\2\2\2lm\3\2\2\2mk\3")
        buf.write("\2\2\2mn\3\2\2\2no\3\2\2\2op\b\21\2\2p\"\3\2\2\2qr\7\61")
        buf.write("\2\2rs\7\61\2\2sw\3\2\2\2tv\n\6\2\2ut\3\2\2\2vy\3\2\2")
        buf.write("\2wu\3\2\2\2wx\3\2\2\2xz\3\2\2\2yw\3\2\2\2z{\b\22\2\2")
        buf.write("{$\3\2\2\2\13\2MSZ\\agmw\3\b\2\2")
        return buf.getvalue()


class MiniRLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    FOR = 1
    IN = 2
    PRINT = 3
    CONST = 4
    VAR = 5
    ASSIGN = 6
    SEMI = 7
    LPAREN = 8
    RPAREN = 9
    LBRACE = 10
    RBRACE = 11
    COLON = 12
    FLOAT = 13
    INT = 14
    ID = 15
    WS = 16
    LINE_COMMENT = 17

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ "DEFAULT_MODE" ]

    literalNames = [ "<INVALID>",
            "'for'", "'in'", "'print'", "'const'", "'var'", "'='", "';'", 
            "'('", "')'", "'{'", "'}'", "':'" ]

    symbolicNames = [ "<INVALID>",
            "FOR", "IN", "PRINT", "CONST", "VAR", "ASSIGN", "SEMI", "LPAREN", 
            "RPAREN", "LBRACE", "RBRACE", "COLON", "FLOAT", "INT", "ID", 
            "WS", "LINE_COMMENT" ]

    ruleNames = [ "FOR", "IN", "PRINT", "CONST", "VAR", "ASSIGN", "SEMI", 
                  "LPAREN", "RPAREN", "LBRACE", "RBRACE", "COLON", "FLOAT", 
                  "INT", "ID", "WS", "LINE_COMMENT" ]

    grammarFileName = "MiniR.g4"

    def __init__(self, input=None, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.9.3")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


