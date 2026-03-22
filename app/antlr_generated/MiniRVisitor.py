# Generated from c:\Users\User\Desktop\compiler\app\grammar\MiniR.g4 by ANTLR 4.9.3
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .MiniRParser import MiniRParser
else:
    from MiniRParser import MiniRParser

# This class defines a complete generic visitor for a parse tree produced by MiniRParser.

class MiniRVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by MiniRParser#program.
    def visitProgram(self, ctx:MiniRParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MiniRParser#statement.
    def visitStatement(self, ctx:MiniRParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MiniRParser#constDecl.
    def visitConstDecl(self, ctx:MiniRParser.ConstDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MiniRParser#varDecl.
    def visitVarDecl(self, ctx:MiniRParser.VarDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MiniRParser#forStmt.
    def visitForStmt(self, ctx:MiniRParser.ForStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MiniRParser#intRange.
    def visitIntRange(self, ctx:MiniRParser.IntRangeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MiniRParser#blockBody.
    def visitBlockBody(self, ctx:MiniRParser.BlockBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MiniRParser#blockStmt.
    def visitBlockStmt(self, ctx:MiniRParser.BlockStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MiniRParser#forStmtNested.
    def visitForStmtNested(self, ctx:MiniRParser.ForStmtNestedContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MiniRParser#printStmt.
    def visitPrintStmt(self, ctx:MiniRParser.PrintStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MiniRParser#literal.
    def visitLiteral(self, ctx:MiniRParser.LiteralContext):
        return self.visitChildren(ctx)



del MiniRParser