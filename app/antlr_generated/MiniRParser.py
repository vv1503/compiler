# Generated from c:\Users\User\Desktop\compiler\app\grammar\MiniR.g4 by ANTLR 4.9.3
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\23")
        buf.write("`\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7\4\b")
        buf.write("\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\3\2\7\2\32\n\2")
        buf.write("\f\2\16\2\35\13\2\3\2\3\2\3\3\3\3\3\3\5\3$\n\3\3\4\3\4")
        buf.write("\3\4\3\4\3\4\3\4\3\5\3\5\3\5\3\5\3\5\3\5\3\6\3\6\3\6\3")
        buf.write("\6\3\6\3\6\3\6\3\6\3\6\3\6\3\6\3\7\3\7\3\7\3\7\3\b\7\b")
        buf.write("B\n\b\f\b\16\bE\13\b\3\t\3\t\5\tI\n\t\3\n\3\n\3\n\3\n")
        buf.write("\3\n\3\n\3\n\3\n\3\n\3\n\5\nU\n\n\3\13\3\13\3\13\3\13")
        buf.write("\3\13\5\13\\\n\13\3\f\3\f\3\f\2\2\r\2\4\6\b\n\f\16\20")
        buf.write("\22\24\26\2\3\3\2\17\20\2[\2\33\3\2\2\2\4#\3\2\2\2\6%")
        buf.write("\3\2\2\2\b+\3\2\2\2\n\61\3\2\2\2\f<\3\2\2\2\16C\3\2\2")
        buf.write("\2\20H\3\2\2\2\22J\3\2\2\2\24V\3\2\2\2\26]\3\2\2\2\30")
        buf.write("\32\5\4\3\2\31\30\3\2\2\2\32\35\3\2\2\2\33\31\3\2\2\2")
        buf.write("\33\34\3\2\2\2\34\36\3\2\2\2\35\33\3\2\2\2\36\37\7\2\2")
        buf.write("\3\37\3\3\2\2\2 $\5\6\4\2!$\5\b\5\2\"$\5\n\6\2# \3\2\2")
        buf.write("\2#!\3\2\2\2#\"\3\2\2\2$\5\3\2\2\2%&\7\6\2\2&\'\7\21\2")
        buf.write("\2\'(\7\b\2\2()\5\26\f\2)*\7\t\2\2*\7\3\2\2\2+,\7\7\2")
        buf.write("\2,-\7\21\2\2-.\7\b\2\2./\5\26\f\2/\60\7\t\2\2\60\t\3")
        buf.write("\2\2\2\61\62\7\3\2\2\62\63\7\n\2\2\63\64\7\21\2\2\64\65")
        buf.write("\7\4\2\2\65\66\5\f\7\2\66\67\7\13\2\2\678\7\f\2\289\5")
        buf.write("\16\b\29:\7\r\2\2:;\7\t\2\2;\13\3\2\2\2<=\7\20\2\2=>\7")
        buf.write("\16\2\2>?\7\20\2\2?\r\3\2\2\2@B\5\20\t\2A@\3\2\2\2BE\3")
        buf.write("\2\2\2CA\3\2\2\2CD\3\2\2\2D\17\3\2\2\2EC\3\2\2\2FI\5\24")
        buf.write("\13\2GI\5\22\n\2HF\3\2\2\2HG\3\2\2\2I\21\3\2\2\2JK\7\3")
        buf.write("\2\2KL\7\n\2\2LM\7\21\2\2MN\7\4\2\2NO\5\f\7\2OP\7\13\2")
        buf.write("\2PQ\7\f\2\2QR\5\16\b\2RT\7\r\2\2SU\7\t\2\2TS\3\2\2\2")
        buf.write("TU\3\2\2\2U\23\3\2\2\2VW\7\5\2\2WX\7\n\2\2XY\7\21\2\2")
        buf.write("Y[\7\13\2\2Z\\\7\t\2\2[Z\3\2\2\2[\\\3\2\2\2\\\25\3\2\2")
        buf.write("\2]^\t\2\2\2^\27\3\2\2\2\b\33#CHT[")
        return buf.getvalue()


class MiniRParser ( Parser ):

    grammarFileName = "MiniR.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'for'", "'in'", "'print'", "'const'", 
                     "'var'", "'='", "';'", "'('", "')'", "'{'", "'}'", 
                     "':'" ]

    symbolicNames = [ "<INVALID>", "FOR", "IN", "PRINT", "CONST", "VAR", 
                      "ASSIGN", "SEMI", "LPAREN", "RPAREN", "LBRACE", "RBRACE", 
                      "COLON", "FLOAT", "INT", "ID", "WS", "LINE_COMMENT" ]

    RULE_program = 0
    RULE_statement = 1
    RULE_constDecl = 2
    RULE_varDecl = 3
    RULE_forStmt = 4
    RULE_intRange = 5
    RULE_blockBody = 6
    RULE_blockStmt = 7
    RULE_forStmtNested = 8
    RULE_printStmt = 9
    RULE_literal = 10

    ruleNames =  [ "program", "statement", "constDecl", "varDecl", "forStmt", 
                   "intRange", "blockBody", "blockStmt", "forStmtNested", 
                   "printStmt", "literal" ]

    EOF = Token.EOF
    FOR=1
    IN=2
    PRINT=3
    CONST=4
    VAR=5
    ASSIGN=6
    SEMI=7
    LPAREN=8
    RPAREN=9
    LBRACE=10
    RBRACE=11
    COLON=12
    FLOAT=13
    INT=14
    ID=15
    WS=16
    LINE_COMMENT=17

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.9.3")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class ProgramContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EOF(self):
            return self.getToken(MiniRParser.EOF, 0)

        def statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(MiniRParser.StatementContext)
            else:
                return self.getTypedRuleContext(MiniRParser.StatementContext,i)


        def getRuleIndex(self):
            return MiniRParser.RULE_program

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterProgram" ):
                listener.enterProgram(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitProgram" ):
                listener.exitProgram(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitProgram" ):
                return visitor.visitProgram(self)
            else:
                return visitor.visitChildren(self)




    def program(self):

        localctx = MiniRParser.ProgramContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_program)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 25
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << MiniRParser.FOR) | (1 << MiniRParser.CONST) | (1 << MiniRParser.VAR))) != 0):
                self.state = 22
                self.statement()
                self.state = 27
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 28
            self.match(MiniRParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def constDecl(self):
            return self.getTypedRuleContext(MiniRParser.ConstDeclContext,0)


        def varDecl(self):
            return self.getTypedRuleContext(MiniRParser.VarDeclContext,0)


        def forStmt(self):
            return self.getTypedRuleContext(MiniRParser.ForStmtContext,0)


        def getRuleIndex(self):
            return MiniRParser.RULE_statement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterStatement" ):
                listener.enterStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitStatement" ):
                listener.exitStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStatement" ):
                return visitor.visitStatement(self)
            else:
                return visitor.visitChildren(self)




    def statement(self):

        localctx = MiniRParser.StatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_statement)
        try:
            self.state = 33
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [MiniRParser.CONST]:
                self.enterOuterAlt(localctx, 1)
                self.state = 30
                self.constDecl()
                pass
            elif token in [MiniRParser.VAR]:
                self.enterOuterAlt(localctx, 2)
                self.state = 31
                self.varDecl()
                pass
            elif token in [MiniRParser.FOR]:
                self.enterOuterAlt(localctx, 3)
                self.state = 32
                self.forStmt()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ConstDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CONST(self):
            return self.getToken(MiniRParser.CONST, 0)

        def ID(self):
            return self.getToken(MiniRParser.ID, 0)

        def ASSIGN(self):
            return self.getToken(MiniRParser.ASSIGN, 0)

        def literal(self):
            return self.getTypedRuleContext(MiniRParser.LiteralContext,0)


        def SEMI(self):
            return self.getToken(MiniRParser.SEMI, 0)

        def getRuleIndex(self):
            return MiniRParser.RULE_constDecl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterConstDecl" ):
                listener.enterConstDecl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitConstDecl" ):
                listener.exitConstDecl(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConstDecl" ):
                return visitor.visitConstDecl(self)
            else:
                return visitor.visitChildren(self)




    def constDecl(self):

        localctx = MiniRParser.ConstDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_constDecl)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 35
            self.match(MiniRParser.CONST)
            self.state = 36
            self.match(MiniRParser.ID)
            self.state = 37
            self.match(MiniRParser.ASSIGN)
            self.state = 38
            self.literal()
            self.state = 39
            self.match(MiniRParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class VarDeclContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def VAR(self):
            return self.getToken(MiniRParser.VAR, 0)

        def ID(self):
            return self.getToken(MiniRParser.ID, 0)

        def ASSIGN(self):
            return self.getToken(MiniRParser.ASSIGN, 0)

        def literal(self):
            return self.getTypedRuleContext(MiniRParser.LiteralContext,0)


        def SEMI(self):
            return self.getToken(MiniRParser.SEMI, 0)

        def getRuleIndex(self):
            return MiniRParser.RULE_varDecl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterVarDecl" ):
                listener.enterVarDecl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitVarDecl" ):
                listener.exitVarDecl(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVarDecl" ):
                return visitor.visitVarDecl(self)
            else:
                return visitor.visitChildren(self)




    def varDecl(self):

        localctx = MiniRParser.VarDeclContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_varDecl)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 41
            self.match(MiniRParser.VAR)
            self.state = 42
            self.match(MiniRParser.ID)
            self.state = 43
            self.match(MiniRParser.ASSIGN)
            self.state = 44
            self.literal()
            self.state = 45
            self.match(MiniRParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ForStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def FOR(self):
            return self.getToken(MiniRParser.FOR, 0)

        def LPAREN(self):
            return self.getToken(MiniRParser.LPAREN, 0)

        def ID(self):
            return self.getToken(MiniRParser.ID, 0)

        def IN(self):
            return self.getToken(MiniRParser.IN, 0)

        def intRange(self):
            return self.getTypedRuleContext(MiniRParser.IntRangeContext,0)


        def RPAREN(self):
            return self.getToken(MiniRParser.RPAREN, 0)

        def LBRACE(self):
            return self.getToken(MiniRParser.LBRACE, 0)

        def blockBody(self):
            return self.getTypedRuleContext(MiniRParser.BlockBodyContext,0)


        def RBRACE(self):
            return self.getToken(MiniRParser.RBRACE, 0)

        def SEMI(self):
            return self.getToken(MiniRParser.SEMI, 0)

        def getRuleIndex(self):
            return MiniRParser.RULE_forStmt

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterForStmt" ):
                listener.enterForStmt(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitForStmt" ):
                listener.exitForStmt(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitForStmt" ):
                return visitor.visitForStmt(self)
            else:
                return visitor.visitChildren(self)




    def forStmt(self):

        localctx = MiniRParser.ForStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_forStmt)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 47
            self.match(MiniRParser.FOR)
            self.state = 48
            self.match(MiniRParser.LPAREN)
            self.state = 49
            self.match(MiniRParser.ID)
            self.state = 50
            self.match(MiniRParser.IN)
            self.state = 51
            self.intRange()
            self.state = 52
            self.match(MiniRParser.RPAREN)
            self.state = 53
            self.match(MiniRParser.LBRACE)
            self.state = 54
            self.blockBody()
            self.state = 55
            self.match(MiniRParser.RBRACE)
            self.state = 56
            self.match(MiniRParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IntRangeContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INT(self, i:int=None):
            if i is None:
                return self.getTokens(MiniRParser.INT)
            else:
                return self.getToken(MiniRParser.INT, i)

        def COLON(self):
            return self.getToken(MiniRParser.COLON, 0)

        def getRuleIndex(self):
            return MiniRParser.RULE_intRange

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIntRange" ):
                listener.enterIntRange(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIntRange" ):
                listener.exitIntRange(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIntRange" ):
                return visitor.visitIntRange(self)
            else:
                return visitor.visitChildren(self)




    def intRange(self):

        localctx = MiniRParser.IntRangeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_intRange)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 58
            self.match(MiniRParser.INT)
            self.state = 59
            self.match(MiniRParser.COLON)
            self.state = 60
            self.match(MiniRParser.INT)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BlockBodyContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def blockStmt(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(MiniRParser.BlockStmtContext)
            else:
                return self.getTypedRuleContext(MiniRParser.BlockStmtContext,i)


        def getRuleIndex(self):
            return MiniRParser.RULE_blockBody

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterBlockBody" ):
                listener.enterBlockBody(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitBlockBody" ):
                listener.exitBlockBody(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBlockBody" ):
                return visitor.visitBlockBody(self)
            else:
                return visitor.visitChildren(self)




    def blockBody(self):

        localctx = MiniRParser.BlockBodyContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_blockBody)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 65
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==MiniRParser.FOR or _la==MiniRParser.PRINT:
                self.state = 62
                self.blockStmt()
                self.state = 67
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BlockStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def printStmt(self):
            return self.getTypedRuleContext(MiniRParser.PrintStmtContext,0)


        def forStmtNested(self):
            return self.getTypedRuleContext(MiniRParser.ForStmtNestedContext,0)


        def getRuleIndex(self):
            return MiniRParser.RULE_blockStmt

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterBlockStmt" ):
                listener.enterBlockStmt(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitBlockStmt" ):
                listener.exitBlockStmt(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBlockStmt" ):
                return visitor.visitBlockStmt(self)
            else:
                return visitor.visitChildren(self)




    def blockStmt(self):

        localctx = MiniRParser.BlockStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_blockStmt)
        try:
            self.state = 70
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [MiniRParser.PRINT]:
                self.enterOuterAlt(localctx, 1)
                self.state = 68
                self.printStmt()
                pass
            elif token in [MiniRParser.FOR]:
                self.enterOuterAlt(localctx, 2)
                self.state = 69
                self.forStmtNested()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ForStmtNestedContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def FOR(self):
            return self.getToken(MiniRParser.FOR, 0)

        def LPAREN(self):
            return self.getToken(MiniRParser.LPAREN, 0)

        def ID(self):
            return self.getToken(MiniRParser.ID, 0)

        def IN(self):
            return self.getToken(MiniRParser.IN, 0)

        def intRange(self):
            return self.getTypedRuleContext(MiniRParser.IntRangeContext,0)


        def RPAREN(self):
            return self.getToken(MiniRParser.RPAREN, 0)

        def LBRACE(self):
            return self.getToken(MiniRParser.LBRACE, 0)

        def blockBody(self):
            return self.getTypedRuleContext(MiniRParser.BlockBodyContext,0)


        def RBRACE(self):
            return self.getToken(MiniRParser.RBRACE, 0)

        def SEMI(self):
            return self.getToken(MiniRParser.SEMI, 0)

        def getRuleIndex(self):
            return MiniRParser.RULE_forStmtNested

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterForStmtNested" ):
                listener.enterForStmtNested(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitForStmtNested" ):
                listener.exitForStmtNested(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitForStmtNested" ):
                return visitor.visitForStmtNested(self)
            else:
                return visitor.visitChildren(self)




    def forStmtNested(self):

        localctx = MiniRParser.ForStmtNestedContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_forStmtNested)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 72
            self.match(MiniRParser.FOR)
            self.state = 73
            self.match(MiniRParser.LPAREN)
            self.state = 74
            self.match(MiniRParser.ID)
            self.state = 75
            self.match(MiniRParser.IN)
            self.state = 76
            self.intRange()
            self.state = 77
            self.match(MiniRParser.RPAREN)
            self.state = 78
            self.match(MiniRParser.LBRACE)
            self.state = 79
            self.blockBody()
            self.state = 80
            self.match(MiniRParser.RBRACE)
            self.state = 82
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==MiniRParser.SEMI:
                self.state = 81
                self.match(MiniRParser.SEMI)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PrintStmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PRINT(self):
            return self.getToken(MiniRParser.PRINT, 0)

        def LPAREN(self):
            return self.getToken(MiniRParser.LPAREN, 0)

        def ID(self):
            return self.getToken(MiniRParser.ID, 0)

        def RPAREN(self):
            return self.getToken(MiniRParser.RPAREN, 0)

        def SEMI(self):
            return self.getToken(MiniRParser.SEMI, 0)

        def getRuleIndex(self):
            return MiniRParser.RULE_printStmt

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPrintStmt" ):
                listener.enterPrintStmt(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPrintStmt" ):
                listener.exitPrintStmt(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPrintStmt" ):
                return visitor.visitPrintStmt(self)
            else:
                return visitor.visitChildren(self)




    def printStmt(self):

        localctx = MiniRParser.PrintStmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_printStmt)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 84
            self.match(MiniRParser.PRINT)
            self.state = 85
            self.match(MiniRParser.LPAREN)
            self.state = 86
            self.match(MiniRParser.ID)
            self.state = 87
            self.match(MiniRParser.RPAREN)
            self.state = 89
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==MiniRParser.SEMI:
                self.state = 88
                self.match(MiniRParser.SEMI)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class LiteralContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INT(self):
            return self.getToken(MiniRParser.INT, 0)

        def FLOAT(self):
            return self.getToken(MiniRParser.FLOAT, 0)

        def getRuleIndex(self):
            return MiniRParser.RULE_literal

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLiteral" ):
                listener.enterLiteral(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLiteral" ):
                listener.exitLiteral(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitLiteral" ):
                return visitor.visitLiteral(self)
            else:
                return visitor.visitChildren(self)




    def literal(self):

        localctx = MiniRParser.LiteralContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_literal)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 91
            _la = self._input.LA(1)
            if not(_la==MiniRParser.FLOAT or _la==MiniRParser.INT):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





