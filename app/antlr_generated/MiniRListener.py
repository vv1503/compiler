# Generated from c:\Users\User\Desktop\compiler\app\grammar\MiniR.g4 by ANTLR 4.9.3
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .MiniRParser import MiniRParser
else:
    from MiniRParser import MiniRParser

# This class defines a complete listener for a parse tree produced by MiniRParser.
class MiniRListener(ParseTreeListener):

    # Enter a parse tree produced by MiniRParser#program.
    def enterProgram(self, ctx:MiniRParser.ProgramContext):
        pass

    # Exit a parse tree produced by MiniRParser#program.
    def exitProgram(self, ctx:MiniRParser.ProgramContext):
        pass


    # Enter a parse tree produced by MiniRParser#statement.
    def enterStatement(self, ctx:MiniRParser.StatementContext):
        pass

    # Exit a parse tree produced by MiniRParser#statement.
    def exitStatement(self, ctx:MiniRParser.StatementContext):
        pass


    # Enter a parse tree produced by MiniRParser#constDecl.
    def enterConstDecl(self, ctx:MiniRParser.ConstDeclContext):
        pass

    # Exit a parse tree produced by MiniRParser#constDecl.
    def exitConstDecl(self, ctx:MiniRParser.ConstDeclContext):
        pass


    # Enter a parse tree produced by MiniRParser#varDecl.
    def enterVarDecl(self, ctx:MiniRParser.VarDeclContext):
        pass

    # Exit a parse tree produced by MiniRParser#varDecl.
    def exitVarDecl(self, ctx:MiniRParser.VarDeclContext):
        pass


    # Enter a parse tree produced by MiniRParser#forStmt.
    def enterForStmt(self, ctx:MiniRParser.ForStmtContext):
        pass

    # Exit a parse tree produced by MiniRParser#forStmt.
    def exitForStmt(self, ctx:MiniRParser.ForStmtContext):
        pass


    # Enter a parse tree produced by MiniRParser#intRange.
    def enterIntRange(self, ctx:MiniRParser.IntRangeContext):
        pass

    # Exit a parse tree produced by MiniRParser#intRange.
    def exitIntRange(self, ctx:MiniRParser.IntRangeContext):
        pass


    # Enter a parse tree produced by MiniRParser#blockBody.
    def enterBlockBody(self, ctx:MiniRParser.BlockBodyContext):
        pass

    # Exit a parse tree produced by MiniRParser#blockBody.
    def exitBlockBody(self, ctx:MiniRParser.BlockBodyContext):
        pass


    # Enter a parse tree produced by MiniRParser#blockStmt.
    def enterBlockStmt(self, ctx:MiniRParser.BlockStmtContext):
        pass

    # Exit a parse tree produced by MiniRParser#blockStmt.
    def exitBlockStmt(self, ctx:MiniRParser.BlockStmtContext):
        pass


    # Enter a parse tree produced by MiniRParser#forStmtNested.
    def enterForStmtNested(self, ctx:MiniRParser.ForStmtNestedContext):
        pass

    # Exit a parse tree produced by MiniRParser#forStmtNested.
    def exitForStmtNested(self, ctx:MiniRParser.ForStmtNestedContext):
        pass


    # Enter a parse tree produced by MiniRParser#printStmt.
    def enterPrintStmt(self, ctx:MiniRParser.PrintStmtContext):
        pass

    # Exit a parse tree produced by MiniRParser#printStmt.
    def exitPrintStmt(self, ctx:MiniRParser.PrintStmtContext):
        pass


    # Enter a parse tree produced by MiniRParser#literal.
    def enterLiteral(self, ctx:MiniRParser.LiteralContext):
        pass

    # Exit a parse tree produced by MiniRParser#literal.
    def exitLiteral(self, ctx:MiniRParser.LiteralContext):
        pass



del MiniRParser