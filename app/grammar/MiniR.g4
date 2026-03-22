// Мини-язык (фрагмент R): const/var, цикл for (i in m:n) { … }, print(i)
// Генерация: java -jar antlr-4.13.1-complete.jar -Dlanguage=Python3 -visitor -listener -o ../antlr_generated MiniR.g4

grammar MiniR;

program
    : statement* EOF
    ;

statement
    : constDecl
    | varDecl
    | forStmt
    ;

constDecl
    : CONST ID ASSIGN literal SEMI
    ;

varDecl
    : VAR ID ASSIGN literal SEMI
    ;

forStmt
    : FOR LPAREN ID IN intRange RPAREN LBRACE blockBody RBRACE SEMI
    ;

intRange
    : INT COLON INT
    ;

blockBody
    : blockStmt*
    ;

blockStmt
    : printStmt
    | forStmtNested
    ;

forStmtNested
    : FOR LPAREN ID IN intRange RPAREN LBRACE blockBody RBRACE SEMI?
    ;

printStmt
    : PRINT LPAREN ID RPAREN SEMI?
    ;

literal
    : INT
    | FLOAT
    ;

// ——— Лексер: ключевые слова раньше ID ———
FOR   : 'for';
IN    : 'in';
PRINT : 'print';
CONST : 'const';
VAR   : 'var';

ASSIGN : '=';
SEMI   : ';';
LPAREN : '(';
RPAREN : ')';
LBRACE : '{';
RBRACE : '}';
COLON  : ':';

// Вещественное до целого (иначе 1.0 разберётся как INT + ошибка)
FLOAT
    : [0-9]+ '.' [0-9]*
    | '.' [0-9]+
    ;

INT : [0-9]+;

ID : [_a-zA-Z] [_a-zA-Z0-9]*;

WS : [ \t\r\n]+ -> skip;

LINE_COMMENT : '//' ~[\r\n]* -> skip;
