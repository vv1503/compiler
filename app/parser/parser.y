%{
#include <stdio.h>
#include <stdlib.h>
#include "globals.h"
extern int line_num;
extern int col_num;
int yylex();
void yyerror(const char *s);
%}

%token FOR IN PRINT ID NUM LPAREN RPAREN LBRACE RBRACE COLON SEMI ERROR_TOKEN
%union { int num; char *id; }
%type <id> ID
%type <num> NUM

%%

program : for_stmt SEMI { printf("Parse successful!\n"); return 0; }
        | error         { yyerror("Синтаксическая ошибка"); }
        ;

for_stmt : FOR LPAREN ID IN range RPAREN LBRACE stmts RBRACE
         ;

range : NUM COLON NUM | ID COLON ID
      ;

stmts : stmt stmts | stmt
      ;

stmt : PRINT LPAREN ID RPAREN SEMI
     ;

%%

void yyerror(const char *s) {
    fprintf(stderr, "Syntax error at line %d, column %d: %s\n", line_num, col_num, s);
}

int main() {
    line_num = 1;
    col_num = 1;
    yyparse();
    return 0;
}