grammar OPLang;

@lexer::header {
from lexererr import *
}

@lexer::members {
def emit(self):
    tk = self.type
    if tk == self.UNCLOSE_STRING:
        result = super().emit();
        raise UncloseString(result.text);
    elif tk == self.ILLEGAL_ESCAPE:
        result = super().emit();
        raise IllegalEscape(result.text);
    elif tk == self.ERROR_CHAR:
        result = super().emit();
        raise ErrorToken(result.text);
    else:
        return super().emit();
}

options{
	language=Python3;
}

program: classdecllist EOF;

classdecllist: classdecl classdecllist | classdecl;
/////////////////////////////////////////////////////////
//////// Parser /////////////////////////////////////////
/////////////////////////////////////////////////////////

// class declaration
classdecl: CLASS ID memberprime LBRACE memberlist RBRACE;
memberprime: EXTENDS ID |;
memberlist: member memberlist | ;
member: attridecl | methoddecl | constructor | destructor;
staticfinal: STATIC | FINAL | STATIC FINAL| FINAL STATIC |;

// constructor declaration
constructor: defaultconstructor | copyconstructor | userdefinedconstructor ;

// -- default constructor
defaultconstructor: ID LB RB body;

// -- copy constructor
copyconstructor: ID LB ID ID RB body;

// -- user-defined constructor
userdefinedconstructor: ID LB paramlist RB body;

// destructor declaration
destructor: DESTRUCTOR ID LB RB body;

// method declaration
methoddecl: staticfinal returntype ID LB paramlist RB body;
body: LBRACE stmtlist RBRACE;
paramlist: paramprime |;
paramprime: param SEMI paramprime | param;
param: (attritype | objectarrtype) (AMP | ) idlist;
idlist: ID COMMA idlist | ID;

stmtlist: stmt stmtlist |;
stmt: vardef | returnstmt | ifstmt | forstmt | continuestmt | breakstmt | reftype | assignstmt | attritype AMP ID SEMI | callexpr SEMI | body;

// definition all possible format of calling method, accessing to attributes,...
callexpr: ID
        | (ID | THIS) callmethods              // a.foo().goo(a,b), this.foo();
        | (ID | THIS) DOT ID callexpr
        | ID DOT ID ASSIGN expr       // a.length := expr, this.length := expr;
        | THIS DOT ID ASSIGN expr
        | (ID | THIS) DOT arrtype;

// attribute declaration outside method, inside a class
attridecl: staticfinal attritype attrilist SEMI;
attrilist: attrilistprime |;
attrilistprime: attribute COMMA attrilistprime | attribute;
attribute: (AMP | ) ID ASSIGN expr | (AMP | ) ID ;                     // this.length := lenght;

// variable declaration in a method
vardef: (FINAL |) attritype varlist SEMI;
varlist: varlistprime |;
varlistprime: var COMMA varlistprime | var;
var: (AMP | ) ID (ASSIGN expr | );

// attribute type
attritype: (INT | FLOAT | BOOLEAN | STRING) (AMP |) | arrtype | classtype;

returntype: attritype (AMP | ) | VOID;
// return statement
returnstmt: RETURN (expr | ) SEMI;

// assign statement
// vốn dĩ ban đầu lhs là postfix
// nhưng do có xuất hiện trường hợp a.foo() := ...
// nghĩa là không được gán sau khi gọi hàm nên mới viết rule riêng cho lhs :))
assignstmt: lhs ASSIGN expr SEMI;
lhs: ID
    | (ID | THIS) DOT arrayaccess
    | ID DOT ID
    | (ID | THIS) DOT lhs
    | arrayaccess
    | (ID | THIS) callmethods DOT lhs
    | LBRACE exprlist RBRACE DOT lhs;

// if statment
// ifstmt: IF (expr | LB expr RB) THEN (stmt | LBRACE stmtlist RBRACE | continuestmt | breakstmt)  elselist;
ifstmt: IF (expr | LB expr RB) THEN (LBRACE stmtlist RBRACE | stmt) elselist;
elselist: ELSE (LBRACE stmtlist RBRACE | stmt) elselist |;

// for statement
forstmt: FOR ID ASSIGN expr (TO | DOWNTO) expr DO (LBRACE stmtlist RBRACE | stmt) ;

// continue statement
continuestmt: CONTINUE SEMI;

// break statement
breakstmt: BREAK SEMI;

// type
type: premitivetype | arrtype | classtype;
premitivetype: INT | FLOAT | BOOLEAN | STRING | VOID;

arrtype: (INT | FLOAT | BOOLEAN | STRING | classtype) LBRACK INTEGER_LITERAL RBRACK (AMP | );

classtype: ID;

// object[5],...
objectarrtype: classtype LBRACK INTEGER_LITERAL RBRACK (AMP | );
reftype: attritype (AMP | ) ID ASSIGN expr SEMI;

// expression
expr: relationexpr;

// <, >, <=, >=, ==, != none
// ==, != có ưu tiên cao hơn <, >, <=, >=
// ! và == không được đi cùng với nhau
// != và == chỉ 1 lần

relationexpr: equalityexpr (LESS | GREATER | LESSEQ | GREATEREQ) equalityexpr | equalityexpr;

// equality
equalityexpr: equalchain | nequalexpr| andorexpr;

// == không thể chain
equalchain: andorexpr EQUAL andorexpr;

// != chỉ 1 lần thôi
nequalexpr: andorexpr NEQUAL andorexpr;

// &&, ||
andorexpr: andorexpr (AND | OR) addsubexpr | addsubexpr;

// binary +,- left
addsubexpr: addsubexpr (ADDOP | SUBOP) muldivexpr | muldivexpr;

// *, /, \, % left
muldivexpr: muldivexpr (MULOP | DIVOP | BACKSLASH | MODOP) concatexpr | concatexpr;

// ^ left
concatexpr: concatexpr EXP unaryexpr | unaryexpr;

// unary +, -, ! right
unaryexpr: addsub postfix | NOT unaryexpr | postfix;

// postfix
postfix: primary postfixoplist | arrayaccess;
addsub: (ADDOP | SUBOP) addsub | (ADDOP | SUBOP );
postfixoplist: postfixop postfixoplist | ;
postfixop:  callmethods | DOT ID | DOT arrayaccess;

// ID + [...]
// ID + [..][..]... -> hỗ trợ mảng đa chiều
arrayaccess: ID arr;
arr: LBRACK expr RBRACK arr | LBRACK expr RBRACK;

// callmethods: for calling one or some method: .foo(...), or call chain .foo().goo(),...

callmethods: DOT ID LB optionalarglist RB (callmethods | ) (arr |);


// a, b, c, ... OPTIONAL
optionalarglist: arglist |;
arglist: expr arglisttail;
arglisttail: COMMA expr arglisttail|;

primary:  INTEGER_LITERAL | FLOAT_LITERAL | STRING_LITERAL | BOOLEAN_LITERAL | ID
        | THIS
        | NIL
        | NEW ID LB optionalarglist RB
        | LB expr RB
        | LBRACE exprlist RBRACE
        | LBRACE exprlist RBRACE LBRACK exprlist RBRACK //{1,2,3}[0]
        | (ID | THIS) crazy
        | LBRACE RBRACE
        | (THIS | LB expr RB) LBRACK expr RBRACK; // ArrayLiteral

crazy: (DOT ID | arrtype) crazy | (DOT ID | arrtype);

//literal: INTEGER_LITERAL | FLOAT_LITERAL | STRING_LITERAL | BOOLEAN_LITERAL;
// literal:;
// unvalid thing like arr[0].something

exprlist: expr COMMA exprlist | expr;
//////////////////////////////////////////////
//////// Lexer //////////////////////////////
/////////////////////////////////////////////
BOOLEAN     : 'boolean' ;
BOOLEAN_LITERAL: 'true' | 'false';
BREAK       : 'break' ;
CLASS       : 'class' ;
CONTINUE    : 'continue' ;
DO          : 'do' ;
ELSE        : 'else' ;
EXTENDS     : 'extends' ;
FLOAT       : 'float' ;
IF          : 'if' ;
INT         : 'int' ;
NEW         : 'new' ;
STRING      : 'string' ;
THEN        : 'then' ;
FOR         : 'for' ;
RETURN      : 'return' ;
VOID        : 'void' ;
NIL         : 'nil' ;
THIS        : 'this' ;
FINAL       : 'final' ;
STATIC      : 'static' ;
TO          : 'to' ;
DOWNTO      : 'downto' ;

DESTRUCTOR: '~';
AMP: '&';

// brackets
LBRACE: '{';
RBRACE: '}';
LBRACK: '[';
RBRACK: ']';
LB: '(';
RB: ')';
SEMI: ';';
COLON: ':';
DOT: '.';
COMMA: ',';

// comment
LINE_COMMENT: '#' ~[\r\n]* -> skip;
BLOCK_COMMENT: '/*' (. | '\r' | '\n')*? '*/' -> skip;

ID: [a-zA-Z_] [a-zA-Z0-9_]*;

// operators
BACKSLASH: '\\';
EQUAL: '==';
NEQUAL: '!=';
LESS: '<';
GREATER: '>';
LESSEQ: '<=';
GREATEREQ: '>=';
ASSIGN: ':=';
EQUAL_SIGN: '=';
ADDOP: '+';
SUBOP: '-';
MULOP: '*';
DIVOP: '/';
MODOP: '%';
EXP: '^';
AND: '&&';
OR: '||';
NOT: '!';

// literals
INTEGER_LITERAL: [0-9]+;

FLOAT_LITERAL: DIGIT '.' DEC EXPONENT? | DIGIT EXPONENT;
fragment DIGIT: [0-9]+;
fragment DEC: [0-9]*;
fragment EXPONENT: [Ee] [+-]? [0-9]+;

STRING_LITERAL: '"' (ESC_SEQ | ~["\\\r\n])* '"'
{
    self.text = self.text[1:-1]
};

UNCLOSE_STRING: '"' (ESC_SEQ | ~["\\\r\n])* (EOF | '\r' | '\n' | '\\' EOF)
{
    self.text = self.text[1:]
};

ILLEGAL_ESCAPE: '"' (ESC_SEQ | ~["\\\r\n])* '\\' ~[btnfr"\\]
{
    self.text = self.text[1:]
};


fragment ESC_SEQ: '\\b' | '\\f' | '\\r' | '\\n' | '\\t' | '\\"' | '\\\\';



WS : [ \t\r\n]+ -> skip ; // skip spaces, tabs

ERROR_CHAR: .;
