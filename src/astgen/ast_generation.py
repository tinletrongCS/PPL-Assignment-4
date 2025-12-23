"""
AST Generation module for OPLang programming language.
This module contains the ASTGeneration class that converts parse trees
into Abstract Syntax Trees using the visitor pattern.
"""
# ASSIGNMENT 3 ---------------------- *************** ----------------------

# Faculity of Computer Science and Engineering
# Author: Le Trong Tin
# ID: 2313452
# Date: October 27th, 2025


from functools import reduce
from build.OPLangVisitor import OPLangVisitor
from build.OPLangParser import OPLangParser
from src.utils.nodes import *


class ASTGeneration(OPLangVisitor):
    # program: classdecllist EOF;
    def visitProgram(self, ctx: OPLangParser.ProgramContext):
        return Program(self.visit(ctx.classdecllist()))

    # classdecllist: classdecl classdecllist | classdecl;
    def visitClassdecllist(self, ctx: OPLangParser.ClassdecllistContext):
        if ctx.classdecllist():
            return [self.visit(ctx.classdecl())] + self.visit(ctx.classdecllist())
        else:
            return [self.visit(ctx.classdecl())]

    # classdecl: CLASS ID memberprime LBRACE memberlist RBRACE;
    def visitClassdecl(self, ctx: OPLangParser.ClassdeclContext):
        classname = ctx.ID().getText()
        superclass = self.visit(ctx.memberprime()) if ctx.memberprime() else None
        members = self.visit(ctx.memberlist()) if ctx.memberlist() else []
        return ClassDecl(classname, superclass, members)

    # memberprime: EXTENDS ID |;
    def visitMemberprime(self, ctx: OPLangParser.MemberprimeContext):
        if ctx.EXTENDS():
            superclass_name = ctx.ID().getText()
            return superclass_name
        return None

        # memberlist: member memberlist | ;

    def visitMemberlist(self, ctx: OPLangParser.MemberlistContext):
        if ctx.getChildCount() == 0:
            return []
        else:
            return [self.visit(ctx.member())] + self.visit(ctx.memberlist())

    # member: attridecl | methoddecl | constructor | destructor;
    def visitMember(self, ctx: OPLangParser.MemberContext):
        if ctx.attridecl():
            return self.visit(ctx.attridecl())
        elif ctx.methoddecl():
            return self.visit(ctx.methoddecl())
        elif ctx.constructor():
            return self.visit(ctx.constructor())
        elif ctx.destructor():
            return self.visit(ctx.destructor())

    # staticfinal: STATIC | FINAL | STATIC FINAL| FINAL STATIC |;
    def visitStaticfinal(self, ctx: OPLangParser.StaticfinalContext):
        is_static = ctx.STATIC() is not None
        is_final = ctx.FINAL() is not None
        return is_static, is_final

    # constructor: defaultconstructor | copyconstructor | userdefinedconstructor ;
    def visitConstructor(self, ctx: OPLangParser.ConstructorContext):
        if ctx.defaultconstructor():
            return self.visit(ctx.defaultconstructor())
        elif ctx.copyconstructor():
            return self.visit(ctx.copyconstructor())
        elif ctx.userdefinedconstructor():
            return self.visit(ctx.userdefinedconstructor())

    # defaultconstructor: ID LB RB body;
    def visitDefaultconstructor(self, ctx: OPLangParser.DefaultconstructorContext):
        name = ctx.ID().getText()
        params = []
        body = self.visit(ctx.body())
        return ConstructorDecl(name, params, body)

    # copyconstructor: ID LB ID ID RB body;
    def visitCopyconstructor(self, ctx: OPLangParser.CopyconstructorContext):
        name = ctx.ID(0).getText()
        param_name = ctx.ID(2).getText()
        param_type_name = ctx.ID(1).getText()
        param_type = ClassType(param_type_name)
        param = Parameter(param_type, param_name)
        params = [param]
        body = self.visit(ctx.body())
        return ConstructorDecl(name, params, body)

    # userdefinedconstructor: ID LB paramlist RB body;
    def visitUserdefinedconstructor(self, ctx: OPLangParser.UserdefinedconstructorContext):
        name = ctx.ID().getText()
        params = self.visit(ctx.paramlist())
        body = self.visit(ctx.body())
        return ConstructorDecl(name, params, body)

    # destructor: DESTRUCTOR ID LB RB body;
    def visitDestructor(self, ctx: OPLangParser.DestructorContext):
        name = ctx.ID().getText()
        body = self.visit(ctx.body())
        return DestructorDecl(name, body)

    # methoddecl: staticfinal returntype ID LB paramlist RB body;
    def visitMethoddecl(self, ctx: OPLangParser.MethoddeclContext):
        if ctx.staticfinal():
            is_static, _ = self.visit(ctx.staticfinal())
        else:
            is_static = False

        return_type = self.visit(ctx.returntype())
        name = ctx.ID().getText()
        params = self.visit(ctx.paramlist()) or []
        body = self.visit(ctx.body())
        return MethodDecl(is_static, return_type, name, params, body)

    # body: LBRACE stmtlist RBRACE;
    def visitBody(self, ctx: OPLangParser.BodyContext):
        if ctx.LBRACE() and ctx.RBRACE():
            nodes = self.visit(ctx.stmtlist()) if ctx.stmtlist() else []
            vars_decls = [n for n in nodes if isinstance(n, VariableDecl)]
            stmts = [n for n in nodes if not isinstance(n, VariableDecl)]
            return BlockStatement(vars_decls, stmts)

    # paramlist: paramprime |;
    def visitParamlist(self, ctx: OPLangParser.ParamlistContext):
        if ctx.paramprime():
            return self.visit(ctx.paramprime())
        else:
            return []

    # paramprime: param SEMI paramprime | param;
    def visitParamprime(self, ctx: OPLangParser.ParamprimeContext):
        if ctx.paramprime():
            return (self.visit(ctx.param()) or []) + (self.visit(ctx.paramprime()) or [])
        else:
            return self.visit(ctx.param()) or []

    # param: (attritype | objectarrtype) (AMP | ) idlist;
    # Parameter() in nodes.py
    def visitParam(self, ctx: OPLangParser.ParamContext):
        if ctx.attritype():
            param_type = self.visit(ctx.attritype())
        elif ctx.objectarrtype():
            param_type = self.visit(ctx.objectarrtype())

        # Nếu có dấu & -> kiểu tham chiếu
        if ctx.AMP():
            param_type = ReferenceType(param_type)

        ids = self.visit(ctx.idlist()) or []
        return [Parameter(param_type, name.name if isinstance(name, Identifier) else name) for name in ids]

    # idlist: ID COMMA idlist | ID;.
    def visitIdlist(self, ctx: OPLangParser.IdlistContext):
        if ctx.ID():
            return [Identifier(ctx.ID().getText())]
        else:
            return [Identifier(ctx.ID().getText())] + self.visit(ctx.idlist())

    # stmtlist: stmt stmtlist |;
    def visitStmtlist(self, ctx: OPLangParser.StmtlistContext):
        if ctx.getChildCount() == 0:
            return []
        else:
            return [self.visit(ctx.stmt())] + (self.visit(ctx.stmtlist()) + [])

    # stmt: vardef | returnstmt | ifstmt | forstmt
    #              | continuestmt | breakstmt | reftype
    #              | assignstmt | attritype AMP ID SEMI | callexpr SEMI
    #              | body;
    def visitStmt(self, ctx: OPLangParser.StmtContext):
        if ctx.vardef():
            return self.visit(ctx.vardef())
        elif ctx.returnstmt():
            return self.visit(ctx.returnstmt())
        elif ctx.ifstmt():
            return self.visit(ctx.ifstmt())
        elif ctx.forstmt():
            return self.visit(ctx.forstmt())
        elif ctx.continuestmt():
            return self.visit(ctx.continuestmt())
        elif ctx.breakstmt():
            return self.visit(ctx.breakstmt())
        elif ctx.reftype():
            return self.visit(ctx.reftype())
        elif ctx.assignstmt():
            return self.visit(ctx.assignstmt())
        elif ctx.attritype():
            var_type = self.visit(ctx.attritype())
            var_type = ReferenceType(var_type)
            name = ctx.ID().getText()
            return VariableDecl(False, var_type, [Variable(name)])
        elif ctx.callexpr():
            return self.visit(ctx.callexpr())
        elif ctx.body():
            return self.visit(ctx.body())

    #### Xem lại kỹ chỗ này
    # callexpr: ID
    # | (ID | THIS) callmethods              // a.foo().goo(a,b), this.foo();
    # | (ID | THIS) DOT ID callexpr
    # | (ID | THIS) DOT ID ASSIGN expr       // a.length := expr, this.length := expr;
    # | (ID | THIS) DOT arrtype
    def visitCallexpr(self, ctx: OPLangParser.CallexprContext):
        # Case 1: ID
        if ctx.ID() and not ctx.callmethods() and not ctx.DOT():
            return Identifier(ctx.ID().getText())

        # Case 2: (ID | THIS) callmethods: io.someMethod
        if ctx.callmethods():
            primary = Identifier(ctx.ID(0).getText()) if ctx.ID() else ThisExpression()

            postfix_ops = self.visit(ctx.callmethods()) or []

            if isinstance(primary, Identifier) and len(postfix_ops) == 1 and isinstance(postfix_ops[0], MethodCall):
                class_name = primary.name
                method_name = postfix_ops[0].method_name
                args = postfix_ops[0].args
                # if class_name == "io":
                #     return MethodInvocationStatement(StaticMethodInvocation(class_name, method_name, args))
                return MethodInvocationStatement(PostfixExpression(primary, postfix_ops))
            return MethodInvocationStatement(PostfixExpression(primary, postfix_ops))

        # Case 3: (ID | THIS) DOT ID callexpr
        if ctx.DOT() and ctx.callexpr() and not ctx.ASSIGN():
            primary = Identifier(ctx.ID(0).getText()) if ctx.ID(0) else ThisExpression()
            member = MemberAccess(ctx.ID(1).getText())
            nested = self.visit(ctx.callexpr())
            # if isinstance(nested,Identifier) and nested.name == ctx.ID(1).getText():
            #     return StaticMemberAccess(primary.name if isinstance(primary, Identifier) else ThisExpression, nested)
            #
            if isinstance(nested, PostfixExpression):
                return PostfixExpression(primary, [member] + nested.postfix_ops)

            else:
                return PostfixExpression(primary, [member])

        # Case 4: ID DOT ID ASSIGN expr
        if ctx.ASSIGN() and ctx.ID() and not ctx.THIS():
            primary = Identifier(ctx.ID(0).getText())
            postfix_ops = [MemberAccess(ctx.ID(1).getText())]
            lhs = PostfixExpression(primary, postfix_ops)
            rhs = self.visit(ctx.expr())
            return AssignmentStatement(PostfixLHS(lhs), rhs)
        # Case 4.1: THIS DOT ID ASSIGN expr
        if ctx.THIS() and ctx.THIS():
            primary = ThisExpression()
            postfix_ops = [MemberAccess(ctx.ID(0).getText())]
            lhs = PostfixExpression(primary, postfix_ops)
            rhs = self.visit(ctx.expr())
            return AssignmentStatement(PostfixLHS(lhs), rhs)

        # Case 5: (ID | THIS) DOT arrtype
        if ctx.arrtype():
            class_name = ctx.ID().getText() if ctx.ID() else ThisExpression()
            member_type = self.visit(ctx.arrtype())
            return MemberAccess(class_name)

        return self.visitChildren(ctx)

    # attridecl: staticfinal attritype attrilist SEMI;
    def visitAttridecl(self, ctx: OPLangParser.AttrideclContext):
        is_static, is_final = self.visit(ctx.staticfinal())
        attr_type = self.visit(ctx.attritype())
        attributes = self.visit(ctx.attrilist())
        return AttributeDecl(is_static, is_final, attr_type, attributes)

    # attrilist: attrilistprime |;
    def visitAttrilist(self, ctx: OPLangParser.AttrilistContext):
        if ctx.getChildCount() == 0:
            return []
        return self.visit(ctx.attrilistprime())

    # attrilistprime: attribute COMMA attrilistprime | attribute;
    def visitAttrilistprime(self, ctx: OPLangParser.AttrilistprimeContext):
        if ctx.attrilistprime():
            return [self.visit(ctx.attribute())] + self.visit(ctx.attrilistprime())
        return [self.visit(ctx.attribute())]

    # attribute: (AMP | ) ID ASSIGN expr | (AMP | ) ID ;
    def visitAttribute(self, ctx: OPLangParser.AttributeContext):
        if ctx.ASSIGN():
            name = ctx.ID().getText()
            init_value = self.visit(ctx.expr())
            return Attribute(name, init_value)
        else:
            name = ctx.ID().getText()
            return Attribute(name)

    # vardef: (FINAL |) attritype varlist SEMI;
    def visitVardef(self, ctx: OPLangParser.VardefContext):
        is_final = True if ctx.FINAL() else False
        var_type = self.visit(ctx.attritype())
        variables = self.visit(ctx.varlist()) or []
        return VariableDecl(is_final, var_type, variables)

    # varlist: varlistprime |;
    def visitVarlist(self, ctx: OPLangParser.VarlistContext):
        if ctx.getChildCount() == 0:
            return []
        return self.visit(ctx.varlistprime())

    # varlistprime: var COMMA varlistprime | var;
    def visitVarlistprime(self, ctx: OPLangParser.VarlistprimeContext):
        if ctx.COMMA():
            return [self.visit(ctx.var())] + self.visit(ctx.varlistprime())
        return [self.visit(ctx.var())]

    # var: (AMP | ) ID (ASSIGN expr | );
    def visitVar(self, ctx: OPLangParser.VarContext):
        name = ctx.ID().getText()
        if ctx.expr():
            init_value = self.visit(ctx.expr())
            return Variable(name, init_value)
        else:
            return Variable(name)

    # attritype: (INT | FLOAT | BOOLEAN | STRING) (AMP |) | arrtype | classtype;
    def visitAttritype(self, ctx: OPLangParser.AttritypeContext):
        if ctx.arrtype():
            return self.visit(ctx.arrtype())
        elif ctx.classtype():
            return self.visit(ctx.classtype())
        if ctx.INT():
            primitive_type = PrimitiveType("int")
        elif ctx.FLOAT():
            primitive_type = PrimitiveType("float")
        elif ctx.STRING():
            primitive_type = PrimitiveType("string")
        elif ctx.BOOLEAN():
            primitive_type = PrimitiveType("boolean")
        if ctx.AMP():
            return ReferenceType(primitive_type)
        else:
            return primitive_type

    # returntype: attritype (AMP | ) | VOID;
    def visitReturntype(self, ctx: OPLangParser.ReturntypeContext):
        if ctx.VOID():
            return PrimitiveType("void")
        return self.visit(ctx.attritype())

    # returnstmt: RETURN (expr | ) SEMI;
    def visitReturnstmt(self, ctx: OPLangParser.ReturnstmtContext):
        value = self.visit(ctx.expr()) if ctx.expr() else NilLiteral()
        return ReturnStatement(value)

    # assignstmt: lhs ASSIGN expr SEMI;
    # AssignmentStatement in nodes.py
    def visitAssignstmt(self, ctx: OPLangParser.AssignstmtContext):
        lhs = self.visit(ctx.lhs())
        rhs = self.visit(ctx.expr())
        return AssignmentStatement(lhs, rhs)

    # lhs: ID
    # | arrayaccess
    # | (ID | THIS) DOT arrayaccess
    # | ID DOT ID
    # | (ID | THIS) DOT lhs
    # | (ID | THIS) callmethods DOT lhs
    # | LBRACE exprlist RBRACE DOT lhs;

    # IdLHS + PostfixLHS
    def visitLhs(self, ctx: OPLangParser.LhsContext):

        # ID
        if ctx.ID() and ctx.getChildCount() == 1:
            return IdLHS(ctx.ID(0).getText())

        # arrayaccess
        if ctx.arrayaccess() and ctx.getChildCount() == 1:
            pe = self.visit(ctx.arrayaccess())
            return PostfixLHS(pe)

        # (ID | THIS) DOT arrayaccess
        if ctx.DOT() and ctx.arrayaccess():
            primary = Identifier(ctx.ID(0).getText()) if ctx.ID() else ThisExpression()
            nested = self.visit(ctx.arrayaccess())
            return PostfixLHS(PostfixExpression(primary, [MemberAccess(nested.primary.name)] + nested.postfix_ops))

        # THIS DOT ID
        if ctx.THIS() and ctx.ID() and ctx.getChildCount() == 3:
            primary = ThisExpression()
            postfix_ops = [MemberAccess(ctx.ID(0).getText())]
            return PostfixLHS(PostfixExpression(primary, postfix_ops))

        # ID DOT ID
        if ctx.DOT() and ctx.ID() and ctx.getChildCount() == 3 and not ctx.lhs():
            primary = Identifier(ctx.ID(0).getText())
            postfix_ops = [MemberAccess(ctx.ID(1).getText())]
            return PostfixLHS(PostfixExpression(primary, postfix_ops))

        # (ID | THIS) DOT lhs
        if ctx.DOT() and ctx.lhs():
            primary = Identifier(ctx.ID(0).getText()) if ctx.ID() else ThisExpression()
            nested = self.visit(ctx.lhs())

            if isinstance(nested, IdLHS):
                return PostfixLHS(PostfixExpression(primary, [MemberAccess(nested.name)]))

            if isinstance(nested, PostfixLHS):
                inner = nested.postfix_expr
                # Nối primary hiện tại (a) với toàn bộ chain của inner (b.c[...])
                return PostfixLHS(PostfixExpression(primary, [MemberAccess(inner.primary.name)] + inner.postfix_ops))

            if isinstance(nested, PostfixExpression):
                return PostfixLHS(PostfixExpression(primary, nested.postfix_ops))

            if isinstance(nested, ArrayAccess):
                return PostfixLHS(PostfixExpression(primary, [nested]))

            return PostfixLHS(PostfixExpression(primary, [nested]))

        # Case 6: (ID | THIS) callmethods DOT lhs
        # if ctx.callmethods() and ctx.lhs():
        #     primary = Identifier(ctx.ID(0).getText()) if ctx.ID() else ThisExpression()
        #     postfix_ops = self.visit(ctx.callmethods())
        #     nested = self.visit(ctx.lhs())
        #     return PostfixLHS(PostfixExpression(primary, postfix_ops + [nested]))

        # Case 7: LBRACE exprlist RBRACE DOT lhs
        # if ctx.LBRACE():
        #     array_lit = ArrayLiteral(self.visit(ctx.exprlist()))
        #     nested = self.visit(ctx.lhs())
        #     return PostfixLHS(PostfixExpression(array_lit, [nested]))

        # fallback
        node = self.visitChildren(ctx)
        if isinstance(node, Expr):
            return PostfixLHS(node)
        return node

    # ifstmt: IF (expr | LB expr RB) THEN (LBRACE stmtlist RBRACE | stmt) elselist;
    def visitIfstmt(self, ctx: OPLangParser.IfstmtContext):
        if ctx.IF():
            condition = self.visit(ctx.expr())
            if ctx.stmtlist():
                then_nodes = self.visit(ctx.stmtlist())
                then_var_decls = [n for n in then_nodes if isinstance(n, VariableDecl)]
                then_statements = [n for n in then_nodes if not isinstance(n, VariableDecl)]
                then_stmt = BlockStatement(then_var_decls, then_statements)
            else:
                then_stmt = self.visit(ctx.stmt())

            else_stmt = self.visit(ctx.elselist()) if ctx.elselist() else None
            return IfStatement(condition, then_stmt, else_stmt)

    # elselist: ELSE (LBRACE stmtlist RBRACE | stmt) elselist |;
    def visitElselist(self, ctx: OPLangParser.ElselistContext):
        if ctx.getChildCount() == 0:
            return None
        else:
            if ctx.stmtlist():
                # else { stmtlist }
                else_nodes = self.visit(ctx.stmtlist()) or []
                var_decls = [n for n in else_nodes if isinstance(n, VariableDecl)]
                statements = [n for n in else_nodes if not isinstance(n, VariableDecl)]
                current_else = BlockStatement(var_decls, statements)
            elif ctx.stmt():
                # else stmt
                current_else = self.visit(ctx.stmt())

                # check nested else
            nested_else = self.visit(ctx.elselist()) if ctx.elselist() else None

            if nested_else:
                return IfStatement(None, current_else, nested_else)
            else:
                return current_else

    # forstmt: FOR ID ASSIGN expr (TO | DOWNTO) expr DO (LBRACE stmtlist RBRACE | stmt);
    def visitForstmt(self, ctx: OPLangParser.ForstmtContext):
        variable = ctx.ID().getText()
        start_expr = self.visit(ctx.expr(0))

        if ctx.TO():
            direction = "to"
        elif ctx.DOWNTO():
            direction = "downto"

        end_expr = self.visit(ctx.expr(1))

        if ctx.stmtlist():
            body_nodes = self.visit(ctx.stmtlist())
            var_decls = [n for n in body_nodes if isinstance(n, VariableDecl)]
            statements = [n for n in body_nodes if not isinstance(n, VariableDecl)]
            body = BlockStatement(var_decls, statements)

        elif ctx.stmt():
            body = self.visit(ctx.stmt())

        return ForStatement(variable, start_expr, direction, end_expr, body)

    # continuestmt: CONTINUE SEMI;
    def visitContinuestmt(self, ctx: OPLangParser.ContinuestmtContext):
        return ContinueStatement()

    # breakstmt: BREAK SEMI;
    def visitBreakstmt(self, ctx: OPLangParser.BreakstmtContext):
        return BreakStatement()

    # type: premitivetype | arrtype | classtype;
    def visitType(self, ctx: OPLangParser.TypeContext):
        if ctx.premitivetype():
            return self.visit(ctx.premitivetype())
        elif ctx.arrtype():
            return self.visit(ctx.arrtype())
        elif ctx.classtype():
            return self.visit(ctx.classtype())

    # premitivetype: INT | FLOAT | BOOLEAN | STRING | VOID;
    def visitPremitivetype(self, ctx: OPLangParser.PremitivetypeContext):
        if ctx.INT():
            return PrimitiveType("int")
        elif ctx.FLOAT():
            return PrimitiveType("float")
        elif ctx.BOOLEAN():
            return PrimitiveType("boolean")
        elif ctx.STRING():
            return PrimitiveType("string")
        elif ctx.VOID():
            return PrimitiveType("void")

    # arrtype: (INT | FLOAT | BOOLEAN | STRIN | classtype) LBRACK INTEGER_LITERAL RBRACK (AMP | );
    def visitArrtype(self, ctx: OPLangParser.ArrtypeContext):
        size = int(ctx.INTEGER_LITERAL().getText())
        if ctx.INT():
            element_type = PrimitiveType("int")
        elif ctx.FLOAT():
            element_type = PrimitiveType("float")
        elif ctx.BOOLEAN():
            element_type = PrimitiveType("boolean")
        elif ctx.STRING():
            element_type = PrimitiveType("string")
        elif ctx.classtype():
            element_type = ClassType(ctx.classtype().getText())

        arr_type = ArrayType(element_type, size)

        # Nếu có dấu &
        if ctx.AMP():
            return ReferenceType(arr_type)
        else:
            return arr_type

    # classtype: ID;
    def visitClasstype(self, ctx: OPLangParser.ClasstypeContext):
        class_name = ctx.ID().getText()
        return ClassType(class_name)

    # objectarrtype: classtype LBRACK INTEGER_LITERAL RBRACK (AMP | );
    def visitObjectarrtype(self, ctx: OPLangParser.ObjectarrtypeContext):
        element_type = self.visit(ctx.classtype())
        size = int(ctx.INTEGER_LITERAL().getText())
        arr_type = ArrayType(element_type, size)

        if ctx.AMP():
            arr_type = ReferenceType(arr_type)  # ReferenceType(ArrayType(...))

        return arr_type

    # reftype: attritype (AMP | ) ID ASSIGN expr SEMI;
    def visitReftype(self, ctx: OPLangParser.ReftypeContext):
        base_type = self.visit(ctx.attritype())
        if ctx.AMP():
            var_type = ReferenceType(base_type)
        else:
            var_type = base_type

        name = ctx.ID().getText()
        init_value = self.visit(ctx.expr())
        variable = Variable(name, init_value)

        return VariableDecl(False, var_type, [variable])

    # expr: relationexpr;
    def visitExpr(self, ctx: OPLangParser.ExprContext):
        return self.visit(ctx.relationexpr())

    # relationexpr: equalityexpr (LESS | GREATER | LESSEQ | GREATEREQ) equalityexpr
    #               | equalityexpr;
    def visitRelationexpr(self, ctx: OPLangParser.RelationexprContext):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.equalityexpr(0))
        else:
            lhs = self.visit(ctx.equalityexpr(0))
            if ctx.LESS():
                operator = "<"
            elif ctx.GREATER():
                operator = ">"
            elif ctx.LESSEQ():
                operator = "<="
            elif ctx.GREATEREQ():
                operator = ">="

            rhs = self.visit(ctx.equalityexpr(1))
            return BinaryOp(lhs, operator, rhs)

    # equalityexpr: equalchain | nequalexpr| andorexpr;
    def visitEqualityexpr(self, ctx: OPLangParser.EqualityexprContext):
        if ctx.equalchain():
            return self.visit(ctx.equalchain())
        elif ctx.nequalexpr():
            return self.visit(ctx.nequalexpr())
        elif ctx.andorexpr():
            return self.visit(ctx.andorexpr())

    # equalchain: andorexpr EQUAL andorexpr;
    def visitEqualchain(self, ctx: OPLangParser.EqualchainContext):
        lhs = self.visit(ctx.andorexpr(0))
        operator_equal = "=="
        rhs = self.visit(ctx.andorexpr(1))
        return BinaryOp(lhs, operator_equal, rhs)

    # nequalexpr: andorexpr NEQUAL andorexpr;
    def visitNequalexpr(self, ctx: OPLangParser.NequalexprContext):
        lhs = self.visit(ctx.andorexpr(0))
        operator_nequal = "!="
        rhs = self.visit(ctx.andorexpr(1))
        return BinaryOp(lhs, operator_nequal, rhs)

    # andorexpr: andorexpr (AND | OR) addsubexpr | addsubexpr;
    def visitAndorexpr(self, ctx: OPLangParser.AndorexprContext):
        if ctx.andorexpr():
            lhs = self.visit(ctx.andorexpr())

            if ctx.AND():
                operator = "&&"
            elif ctx.OR():
                operator = "||"

            rhs = self.visit(ctx.addsubexpr())

            return BinaryOp(lhs, operator, rhs)
        return self.visit(ctx.addsubexpr())

    # addsubexpr: addsubexpr (ADDOP | SUBOP) muldivexpr | muldivexpr;
    def visitAddsubexpr(self, ctx: OPLangParser.AddsubexprContext):
        if ctx.addsubexpr():
            lhs = self.visit(ctx.addsubexpr())

            if ctx.ADDOP():
                operator = "+"
            elif ctx.SUBOP():
                operator = "-"
            rhs = self.visit(ctx.muldivexpr())

            return BinaryOp(lhs, operator, rhs)

        return self.visit(ctx.muldivexpr())

    # muldivexpr: muldivexpr (MULOP | DIVOP | BACKSLASH | MODOP) concatexpr | concatexpr;
    def visitMuldivexpr(self, ctx: OPLangParser.MuldivexprContext):
        if ctx.muldivexpr():
            lhs = self.visit(ctx.muldivexpr())
            if ctx.MULOP():
                operator = "*"
            elif ctx.DIVOP():
                operator = "/"
            elif ctx.BACKSLASH():
                operator = ctx.BACKSLASH().getText()
            elif ctx.MODOP():
                operator = "%"
            rhs = self.visit(ctx.concatexpr())

            return BinaryOp(lhs, operator, rhs)

        return self.visit(ctx.concatexpr())

    # concatexpr: concatexpr EXP unaryexpr | unaryexpr;
    def visitConcatexpr(self, ctx: OPLangParser.ConcatexprContext):
        if ctx.concatexpr():
            lhs = self.visit(ctx.concatexpr())
            operator = "^"
            rhs = self.visit(ctx.unaryexpr())
            return BinaryOp(lhs, operator, rhs)
        return self.visit(ctx.unaryexpr())

    # unaryexpr: addsub postfix | NOT unaryexpr | postfix;
    def visitUnaryexpr(self, ctx: OPLangParser.UnaryexprContext):
        if ctx.addsub():
            operators = self.visit(ctx.addsub())
            operand = self.visit(ctx.postfix())
            # build từ trong ra ngoài
            for operator in reversed(operators):
                operand = UnaryOp(operator, operand)
            return operand

        elif ctx.NOT():
            operator = "!"
            operand = self.visit(ctx.unaryexpr())
            return UnaryOp(operator, operand)

        else:
            return self.visit(ctx.postfix())

    # postfix: primary postfixoplist | arrayaccess;
    def visitPostfix(self, ctx: OPLangParser.PostfixContext):
        if ctx.arrayaccess():
            return self.visit(ctx.arrayaccess())
        primary = self.visit(ctx.primary())
        postfix_ops = self.visit(ctx.postfixoplist())
        if postfix_ops:
            return PostfixExpression(primary, postfix_ops)
        return primary

    # addsub: (ADDOP | SUBOP) addsub | (ADDOP | SUBOP );
    # for muiltiple unary + and
    # E.g: +++-- => ['+', '+', '+', '-', '-']
    def visitAddsub(self, ctx: OPLangParser.AddsubContext):
        if ctx.addsub():
            operator = ctx.ADDOP().getText() if ctx.ADDOP() else ctx.SUBOP().getText()
            return [operator] + self.visit(ctx.addsub())
        else:
            return [ctx.ADDOP().getText()] if ctx.ADDOP() else [ctx.SUBOP().getText()]

    # postfixoplist: postfixop postfixoplist | ;
    def visitPostfixoplist(self, ctx: OPLangParser.PostfixoplistContext):
        if ctx.getChildCount() == 0:
            return []

        postfixop = self.visit(ctx.postfixop())
        postfixoplist = self.visit(ctx.postfixoplist()) or []

        # Flatten: nếu first là list, nối vào luôn
        if isinstance(postfixop, list):
            return postfixop + postfixoplist
        else:
            return [postfixop] + postfixoplist

    # postfixop:  callmethods | DOT ID | DOT arrayaccess;
    def visitPostfixop(self, ctx: OPLangParser.PostfixopContext):
        if ctx.callmethods():
            calls = self.visit(ctx.callmethods()) or []
            return calls
        elif ctx.ID():
            return MemberAccess(ctx.ID().getText())
        elif ctx.arrayaccess():
            return [self.visit(ctx.arrayaccess())]
        else:
            return []

    # arrayaccess: ID arr;
    def visitArrayaccess(self, ctx: OPLangParser.ArrayaccessContext):
        base_name = ctx.ID().getText()
        primary = Identifier(base_name)
        postfix_ops = self.visit(ctx.arr()) or []
        return PostfixExpression(primary, postfix_ops)

    # arr: LBRACK expr RBRACK arr | LBRACK expr RBRACK;.
    def visitArr(self, ctx: OPLangParser.ArrContext):
        expr = self.visit(ctx.expr())
        accesses = [ArrayAccess(expr)]
        if ctx.arr():
            accesses += self.visit(ctx.arr())
        return accesses

    # callmethods: DOT ID LB optionalarglist RB (callmethods | ) (arr |)
    def visitCallmethods(self, ctx: OPLangParser.CallmethodsContext):

        method_name = ctx.ID().getText()
        args = self.visit(ctx.optionalarglist()) or []
        postfix_ops = [MethodCall(method_name, args)]

        # Nếu có call chain .foo().bar()
        if ctx.callmethods():
            next_ops = self.visit(ctx.callmethods()) or []
            if isinstance(next_ops, list):
                postfix_ops += next_ops
            else:
                postfix_ops.append(next_ops)

        #  Nếu có array sau method .foo()[0]
        if ctx.arr():
            arr_ops = self.visit(ctx.arr()) or []
            if isinstance(arr_ops, list):
                postfix_ops.extend(arr_ops)
            else:
                postfix_ops.append(arr_ops)

        return postfix_ops

    # optionalarglist: arglist |;
    def visitOptionalarglist(self, ctx: OPLangParser.OptionalarglistContext):
        if ctx.arglist():
            return self.visit(ctx.arglist())
        elif ctx.getChildCount() == 0:
            return []

    # arglist: expr arglisttail;
    def visitArglist(self, ctx: OPLangParser.ArglistContext):
        return [self.visit(ctx.expr())] + (self.visit(ctx.arglisttail()) or [])

    # arglisttail: COMMA expr arglisttail |;
    def visitArglisttail(self, ctx: OPLangParser.ArglisttailContext):
        if ctx.getChildCount() == 0:
            return []
        return [self.visit(ctx.expr())] + (self.visit(ctx.arglisttail()) or [])

    # Visit a parse tree produced by OPLangParser#primary.
    def visitPrimary(self, ctx: OPLangParser.PrimaryContext):
        # Literal cases
        if ctx.INTEGER_LITERAL():
            return IntLiteral(int(ctx.INTEGER_LITERAL().getText()))
        if ctx.FLOAT_LITERAL():
            return FloatLiteral(float(ctx.FLOAT_LITERAL().getText()))
        if ctx.STRING_LITERAL():
            return StringLiteral(ctx.STRING_LITERAL().getText())
        if ctx.BOOLEAN_LITERAL():
            val = ctx.BOOLEAN_LITERAL().getText()
            return BoolLiteral(val == "true")

        # ID
        if ctx.ID() and ctx.getChildCount() == 1:
            return Identifier(ctx.ID().getText())

        # THIS
        if ctx.THIS() and ctx.getChildCount() == 1:
            return ThisExpression()

        # NIL
        if ctx.NIL():
            return NilLiteral()

        # NEW ID LB optionalarglist RB
        if ctx.NEW():
            class_name = ctx.ID().getText()
            args = self.visit(ctx.optionalarglist()) or []
            return ObjectCreation(class_name, args)

        # LB expr RB => grouping expression (thường lấy exprlist đầu tiên)
        if ctx.LB() and ctx.RB() and ctx.expr():
            expr = self.visit(ctx.expr(0))
            return ParenthesizedExpression(expr)

        # { exprlist }  => ArrayLiteral: {1, 2, 3,...}
        if ctx.LBRACE() and ctx.RBRACE() and ctx.exprlist() and not ctx.LBRACK():
            exprlist_ctx = ctx.exprlist(0)  # lấy phần tử đầu tiên thay vì ctx.exprlist()
            elements = self.visit(ctx.exprlist(0))
            return ArrayLiteral(elements)

        # { exprlist } [ exprlist ] => PostfixExpression(ArrayLiteral, [ArrayAccess...])
        if ctx.LBRACE() and ctx.RBRACE() and ctx.LBRACK() and ctx.exprlist(1):
            exprlist_ctx = ctx.exprlist(1)
            elements = self.visit(ctx.exprlist(0)) or []
            array_lit = ArrayLiteral(elements)
            indices = self.visit(ctx.exprlist(1)) or []
            # Mỗi expr trong exprlist là 1 chỉ số
            array_ops = [ArrayAccess(idx) for idx in indices]
            return PostfixExpression(array_lit, array_ops)

        # (ID | THIS) crazy
        if ctx.crazy():
            if ctx.ID():
                primary = Identifier(ctx.ID(0).getText())
            elif ctx.THIS():
                primary = ThisExpression()
            else:
                primary = None
            crazy_ops = self.visit(ctx.crazy()) or []
            return PostfixExpression(primary, crazy_ops)

        # { }  => Empty ArrayLiteral
        if ctx.LBRACE() and ctx.RBRACE() and not ctx.exprlist():
            return ArrayLiteral([])

        # (THIS | LB expr RB) LBRACK expr RBRACK
        if ctx.LBRACK() and ctx.RBRACK() and ctx.expr():
            if ctx.THIS():
                primary = ThisExpression()
            elif ctx.LB():
                # (expr) lấy expr bên trong
                primary = self.visit(ctx.expr(0))
            else:
                primary = None
            index_expr = self.visit(ctx.expr(-1))  # expr cuối là chỉ số
            return PostfixExpression(primary, [ArrayAccess(index_expr)])

        # fallback
        return self.visitChildren(ctx)

    # crazy: (DOT ID | arrtype) crazy | (DOT ID | arrtype);
    def visitCrazy(self, ctx: OPLangParser.CrazyContext):
        ops = []

        # DOT ID
        if ctx.DOT() and ctx.ID():
            ops.append(MemberAccess(ctx.ID().getText()))

        # arrtype
        if ctx.arrtype():
            arr_type = self.visit(ctx.arrtype())
            # arrtype thường dùng cho static member access
            ops.append(arr_type)

        # đệ quy crazy phía sau
        if ctx.crazy():
            tail = self.visit(ctx.crazy())
            if isinstance(tail, list):
                ops.extend(tail)
            else:
                ops.append(tail)
        return ops

    # exprlist: expr COMMA exprlist | expr;
    def visitExprlist(self, ctx: OPLangParser.ExprlistContext):
        if ctx.exprlist():
            return [self.visit(ctx.expr())] + self.visit(ctx.exprlist())
        else:
            return [self.visit(ctx.expr())]


