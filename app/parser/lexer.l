%{
#include "parser.tab.h"
#include "globals.h"
#include <stdio.h>
#include <stdlib.h>

extern int line_num;
extern int col_num;
%}

%%

[ \t]     { 
    printf("11\tразделитель (пробел)\t(пробел)\tстрока %d,%d-%d\n", 
           line_num, col_num, col_num); 
    col_num += yyleng; 
}

\n        { 
    printf("11\tразделитель (перевод строки)\t(перевод строки)\tстрока %d,%d-%d\n", 
           line_num, col_num, col_num); 
    line_num++; 
    col_num = 1; 
}

"for"     { 
    printf("14\tключевое слово\tfor\tстрока %d,%d-%d\n", line_num, col_num, col_num+2); 
    col_num += 3; return FOR; 
}

"in"      { 
    printf("14\tключевое слово\tin\tстрока %d,%d-%d\n", line_num, col_num, col_num+1); 
    col_num += 2; return IN; 
}

"print"   { 
    printf("14\tключевое слово\tprint\tстрока %d,%d-%d\n", line_num, col_num, col_num+4); 
    col_num += 5; return PRINT; 
}

[0-9]+    { 
    printf("1\tцелое без знака\t%s\tстрока %d,%d-%d\n", yytext, line_num, col_num, col_num+yyleng-1); 
    col_num += yyleng; yylval.num = atoi(yytext); return NUM; 
}

[a-zA-Z_][a-zA-Z0-9_]* { 
    printf("2\tидентификатор\t%s\tстрока %d,%d-%d\n", yytext, line_num, col_num, col_num+yyleng-1); 
    col_num += yyleng; yylval.id = strdup(yytext); return ID; 
}

"("       { printf("16\tразделитель\t(\tстрока %d,%d-%d\n", line_num, col_num, col_num); col_num++; return LPAREN; }
")"       { printf("16\tразделитель\t)\tстрока %d,%d-%d\n", line_num, col_num, col_num); col_num++; return RPAREN; }
"{"       { printf("16\tразделитель\t{\tстрока %d,%d-%d\n", line_num, col_num, col_num); col_num++; return LBRACE; }
"}"       { printf("16\tразделитель\t}\tстрока %d,%d-%d\n", line_num, col_num, col_num); col_num++; return RBRACE; }
":"       { printf("10\tоператор диапазона\t:\tстрока %d,%d-%d\n", line_num, col_num, col_num); col_num++; return COLON; }
";"       { printf("16\tконец оператора\t;\tстрока %d,%d-%d\n", line_num, col_num, col_num); col_num++; return SEMI; }

.         { 
    fprintf(stderr, "Недопустимый символ '%c' на строке %d, позиции %d\n", 
            yytext[0], line_num, col_num); 
    col_num++; 
    return ERROR_TOKEN; 
}

%%

int yywrap() { return 1; }