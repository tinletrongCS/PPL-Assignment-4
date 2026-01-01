"""
Code Generator for OPLang programming language.
This module implements a code generator that traverses AST nodes and generates
Java bytecode using the Emitter and Frame classes.
"""

from typing import Any, List, Optional
from ..utils.visitor import ASTVisitor
from ..utils.nodes import *
from .emitter import Emitter, is_void_type, is_int_type, is_string_type, is_bool_type, is_float_type
from .frame import Frame
from .error import IllegalOperandException, IllegalRuntimeException
from .io import IO_SYMBOL_LIST
from .utils import *
from functools import *


class CodeGenerator(ASTVisitor):
    """
    Code generator for OPLang.
    Traverses AST and generates JVM bytecode.
    """
    
    def __init__(self):
        self.current_class = None
        self.emit = None  # Will be initialized per class

    # ============================================================================
    # Program and Class Declarations
    # ============================================================================

    def visit_program(self, node: "Program", o: Any = None):
        """
        Visit program node - generate code for all classes.
        """
        # Process all class declarations
        for class_decl in node.class_decls:
            self.visit(class_decl, o)

    def visit_class_decl(self, node: "ClassDecl", o: Any = None):
        """
        Visit class declaration - generate class structure.
        """
        self.current_class = node.name
        class_file = node.name + ".j"
        self.emit = Emitter(class_file)
        
        # Determine superclass
        superclass = node.superclass if node.superclass else "java/lang/Object"
        
        # Emit class prolog
        self.emit.print_out(self.emit.emit_prolog(node.name, superclass))
        
        # Process class members (attributes, methods, constructors, destructors)
        for member in node.members:
            self.visit(member, o)
        
        # Emit class epilog
        self.emit.emit_epilog()

    # ============================================================================
    # Attribute Declarations
    # ============================================================================

    def visit_attribute_decl(self, node: "AttributeDecl", o: Any = None):
        """
        Visit attribute declaration - generate field directives.
        Implement attribute initialization if needed
        """
        for attr in node.attributes:
            self.visit(attr, node)

    def visit_attribute(self, node: "Attribute", o: Any = None):
        """
        Visit individual attribute - generate field directive.
        """
        attr_decl = o  # AttributeDecl node
        class_name = self.current_class
        field_name = class_name + "/" + node.name
        
        # Emit field directive
        if attr_decl.is_static:
            self.emit.print_out(
                self.emit.emit_attribute(
                    field_name,
                    attr_decl.attr_type,
                    attr_decl.is_final
                )
            )
        else:
            # Instance field
            self.emit.print_out(
                self.emit.jvm.emitINSTANCEFIELD(
                    field_name,
                    self.emit.get_jvm_type(attr_decl.attr_type)
                )
            )
        
        # Handle initialization if node.init_value is not None

    # ============================================================================
    # Method Declarations
    # ============================================================================

    def visit_method_decl(self, node: "MethodDecl", o: Any = None):
        """
        Visit method declaration - generate method code.
        """
        frame = Frame(node.name, node.return_type)
        self.generate_method(node, frame, node.is_static)

    def visit_constructor_decl(self, node: "ConstructorDecl", o: Any = None):
        """
        Visit constructor declaration - generate constructor code.
        """
        # Implement constructor generation * 
        frame = Frame(node.name, node.return_type)
        self.generate_method(node, frame, node.is_static)
        

    def visit_destructor_decl(self, node: "DestructorDecl", o: Any = None):
        """
        Visit destructor declaration - generate destructor code.
        """
        # Implement destructor generation *
        frame = Frame("finalize", PrimitiveType("void"))
        self.generate_method(node, frame, False)

    def visit_parameter(self, node: "Parameter", o: Any = None):
        """
        Visit parameter - register parameter in frame.
        """
        # This is handled in generate_method
        pass

    def generate_method(self, node: "MethodDecl", frame: Frame, is_static: bool):
        """
        Generate code for a method.
        """
        class_name = self.current_class
        method_name = node.name
        return_type = node.return_type

        # 1. Xử lý signature đặc biệt cho hàm main
        if method_name == "main" and is_static:
            # Ép descriptor thành ([Ljava/lang/String;)V bằng cách tạo FunctionType giả lập
            # OPLang ArrayType cần element_type và size
            mtype = FunctionType([ArrayType(PrimitiveType("string"), 0)], PrimitiveType("void"))
        else:
            param_types = [p.param_type for p in node.params]
            mtype = FunctionType(param_types, return_type)

        # Emit method directive (.method public static main([Ljava/lang/String;)V)
        self.emit.print_out(
            self.emit.emit_method(
                method_name,
                mtype,
                is_static
            )
        )

        frame.enter_scope(True)
        from_label = frame.get_start_label()
        to_label = frame.get_end_label()

        # 2. Quản lý Index: Giữ chỗ cho tham số trong bảng biến cục bộ
        sym_list = []

        extra_io = [
            Symbol("print", FunctionType([PrimitiveType("string")], PrimitiveType("void")), CName("io")),
            Symbol("int2str", FunctionType([PrimitiveType("int")], PrimitiveType("string")), CName("io"))
        ]

        if method_name == "main" and is_static:
            # Index 0 dành cho tham số String[] args mà JVM truyền vào
            frame.get_new_index()
        elif not is_static:
            # Index 0 dành cho 'this' đối với instance method
            this_idx = frame.get_new_index()
            self.emit.print_out(
                self.emit.emit_var(
                    this_idx,
                    "this",
                    ClassType(class_name),
                    from_label,
                    to_label
                )
            )
            sym_list.append(Symbol("this", ClassType(class_name), Index(this_idx)))

        # Khai báo các tham số thực tế từ AST (nếu có)
        for param in node.params:
            idx = frame.get_new_index()
            self.emit.print_out(
                self.emit.emit_var(
                    idx,
                    param.name,
                    param.param_type,
                    from_label,
                    to_label
                )
            )
            sym_list.append(Symbol(param.name, param.param_type, Index(idx)))

        # Thêm các ký hiệu IO để có thể gọi hàm print, int2str...
        sym_list = extra_io + IO_SYMBOL_LIST + sym_list

        self.emit.print_out(self.emit.emit_label(from_label, frame))

        # 3. Generate code cho thân hàm (Body)
        o = SubBody(frame, sym_list)
        self.visit(node.body, o)

        # Tự động thêm lệnh return nếu là hàm void
        if is_void_type(return_type):
            self.emit.print_out(self.emit.emit_return(return_type, frame))

        self.emit.print_out(self.emit.emit_label(to_label, frame))
        self.emit.print_out(self.emit.emit_end_method(frame))

        frame.exit_scope()

    # ============================================================================
    # Type System
    # ============================================================================

    def visit_primitive_type(self, node: "PrimitiveType", o: Any = None):
        pass

    def visit_array_type(self, node: "ArrayType", o: Any = None):
        pass

    def visit_class_type(self, node: "ClassType", o: Any = None):
        pass

    def visit_reference_type(self, node: "ReferenceType", o: Any = None):
        pass

    # ============================================================================
    # Statements
    # ============================================================================

    def visit_block_statement(self, node: "BlockStatement", o: SubBody = None):
        """
        Visit block statement - process variable declarations and statements.
        """
        if o is None:
            return
        
        # Process variable declarations
        for var_decl in node.var_decls:
            o = self.visit(var_decl, o)
        
        # Process statements
        for stmt in node.statements:
            self.visit(stmt, o)

    def visit_variable_decl(self, node: "VariableDecl", o: SubBody = None):
        """
        Visit variable declaration - register local variables.
        """
        if o is None:
            return o
        
        frame = o.frame
        from_label = frame.get_start_label()
        to_label = frame.get_end_label()
        
        new_sym = []
        for var in node.variables:
            idx = frame.get_new_index()
            self.emit.print_out(
                self.emit.emit_var(
                    idx,
                    var.name,
                    node.var_type,
                    from_label,
                    to_label
                )
            )
            
            # Add to symbol list
            new_sym.append(Symbol(var.name, node.var_type, Index(idx)))
            
            # Handle initialization if present
            if var.init_value is not None:
                # Generate code for initialization
                code, typ = self.visit(var.init_value, Access(frame, o.sym))
                self.emit.print_out(code)
                self.emit.print_out(
                    self.emit.emit_write_var(var.name, node.var_type, idx, frame)
                )
        
        return SubBody(frame, new_sym + o.sym)

    def visit_variable(self, node: "Variable", o: Any = None):
        pass

    def visit_assignment_statement(self, node: "AssignmentStatement", o: SubBody = None):
        """
        Visit assignment statement - generate assignment code.
        """
        if o is None:
            return
        
        # Generate code for RHS
        code, typ = self.visit(node.rhs, Access(o.frame, o.sym))
        self.emit.print_out(code)
        
        # Generate code for LHS
        lhs_code, lhs_type = self.visit(node.lhs, Access(o.frame, o.sym, is_left=True))
        self.emit.print_out(lhs_code)

    def visit_if_statement(self, node: "IfStatement", o: Any = None):
        """
        Visit if statement.
        Implement if statement code generation
        """
        frame = o.frame
        cond_code, _ = self.visit(node.condition, Access(frame, o.sym))
        self.emit.print_out(cond_code)
        
        else_label = frame.get_new_label()
        exit_label = frame.get_new_label()
        
        self.emit.print_out(self.emit.emit_if_false(else_label, frame))
        self.visit(node.then_stmt, o)
        self.emit.print_out(self.emit.emit_goto(exit_label, frame))
        
        self.emit.print_out(self.emit.emit_label(else_label, frame))
        if node.else_stmt:
            self.visit(node.else_stmt, o)
        self.emit.print_out(self.emit.emit_label(exit_label, frame))

    def visit_for_statement(self, node: "ForStatement", o: Any = None):
        """
        Visit for statement.
        Implement for statement code generation
        """
        frame = o.frame
        # 1. Initialize
        start_code, _ = self.visit(node.start_expr, Access(frame, o.sym))
        self.emit.print_out(start_code)
        sym = next(s for s in o.sym if s.name == node.variable)
        self.emit.print_out(self.emit.emit_write_var(sym.name, sym.type, sym.value.value, frame))
        
        loop_label = frame.get_new_label()
        continue_label = frame.get_new_label()
        break_label = frame.get_new_label()
        
        frame.enter_loop()
        frame.con_label.append(continue_label)
        frame.brk_label.append(break_label)
        
        self.emit.print_out(self.emit.emit_label(loop_label, frame))
        
        # 2. Condition
        self.emit.print_out(self.emit.emit_read_var(sym.name, sym.type, sym.value.value, frame))
        end_code, _ = self.visit(node.end_expr, Access(frame, o.sym))
        self.emit.print_out(end_code)
        
        if node.direction == "to":
            self.emit.print_out(self.emit.jvm.emitIFICMPGT(break_label))
        else:
            self.emit.print_out(self.emit.jvm.emitIFICMPLT(break_label))
        frame.pop(); frame.pop()
        
        # 3. Body
        self.visit(node.body, o)
        
        # 4. Update
        self.emit.print_out(self.emit.emit_label(continue_label, frame))
        self.emit.print_out(self.emit.emit_read_var(sym.name, sym.type, sym.value.value, frame))
        self.emit.print_out(self.emit.emit_push_iconst(1, frame))
        if node.direction == "to":
            self.emit.print_out(self.emit.jvm.emitIADD())
        else:
            self.emit.print_out(self.emit.jvm.emitISUB())
        frame.pop()
        self.emit.print_out(self.emit.emit_write_var(sym.name, sym.type, sym.value.value, frame))
        
        self.emit.print_out(self.emit.emit_goto(loop_label, frame))
        self.emit.print_out(self.emit.emit_label(break_label, frame))
        
        frame.exit_loop()

    def visit_break_statement(self, node: "BreakStatement", o: Any = None):
        """
        Visit break statement.
        Implement break statement code generation
        """
        self.emit.print_out(self.emit.emit_goto(o.frame.get_break_label(), o.frame))

    def visit_continue_statement(self, node: "ContinueStatement", o: Any = None):
        """
        Visit continue statement.
        Implement continue statement code generation
        """
        self.emit.print_out(self.emit.emit_goto(o.frame.get_continue_label(), o.frame))

    def visit_return_statement(self, node: "ReturnStatement", o: SubBody = None):
        """
        Visit return statement - generate return code.
        """
        if o is None:
            return
        
        # Generate code for return value
        code, typ = self.visit(node.value, Access(o.frame, o.sym))
        self.emit.print_out(code)
        
        # Emit return instruction
        self.emit.print_out(self.emit.emit_return(typ, o.frame))

    def visit_method_invocation_statement(
        self, node: "MethodInvocationStatement", o: Any = None
    ):
        """
        Visit method invocation statement.
        """
        # Implement method invocation statement

        code, typ = self.visit(node.method_call, Access(o.frame, o.sym, False))
        self.emit.print_out(code)

        if not is_void_type(typ):
            self.emit.print_out(self.emit.emit_pop(o.frame))
    # ============================================================================
    # Left-hand Side (LHS)
    # ============================================================================

    def visit_id_lhs(self, node: "IdLHS", o: Access = None):
        """
        Visit identifier LHS - generate code to write to variable.
        """
        if o is None:
            return "", None
        
        # Find symbol
        sym = next(filter(lambda x: x.name == node.name, o.sym), None)
        if sym is None:
            raise IllegalOperandException(f"Undeclared variable: {node.name}")
        
        if type(sym.value) is Index:
            code = self.emit.emit_write_var(
                sym.name, sym.type, sym.value.value, o.frame
            )
            return code, sym.type
        else:
            raise IllegalOperandException(f"Cannot assign to: {node.name}")

    def visit_postfix_lhs(self, node: "PostfixLHS", o: Any = None):
        """
        Visit postfix LHS (for member access, array access).
        TODO: Implement postfix LHS code generation
        """
        pass

    # ============================================================================
    # Expressions
    # ============================================================================

    def visit_binary_op(self, node: "BinaryOp", o: Access = None):
        """
        Visit binary operation.
        Implement binary operation code generation
        """
        lc, lt = self.visit(node.left, o)
        rc, rt = self.visit(node.right, o)
        
        if node.operator in ["&&", "||"]:
            # Short-circuit logic
            res_label = o.frame.get_new_label()
            exit_label = o.frame.get_new_label()
            code = lc
            if node.operator == "&&":
                code += self.emit.emit_if_false(res_label, o.frame)
                code += rc
                code += self.emit.emit_goto(exit_label, o.frame)
                code += self.emit.emit_label(res_label, o.frame)
                code += self.emit.emit_push_iconst(0, o.frame)
            else:
                code += self.emit.emit_if_true(res_label, o.frame)
                code += rc
                code += self.emit.emit_goto(exit_label, o.frame)
                code += self.emit.emit_label(res_label, o.frame)
                code += self.emit.emit_push_iconst(1, o.frame)
            code += self.emit.emit_label(exit_label, o.frame)
            return code, PrimitiveType("boolean")

        # Arithmetic and Relational
        code = lc
        if is_float_type(lt) and is_int_type(rt): rc += self.emit.emit_i2f(o.frame)
        if is_int_type(lt) and is_float_type(rt): code += self.emit.emit_i2f(o.frame)
        code += rc
        
        res_type = PrimitiveType("float") if (is_float_type(lt) or is_float_type(rt) or node.operator == "/") else lt
        
        if node.operator in ["+", "-"]: code += self.emit.emit_add_op(node.operator, res_type, o.frame)
        elif node.operator in ["*", "/"]: code += self.emit.emit_mul_op(node.operator, res_type, o.frame)
        elif node.operator == "\\": code += self.emit.emit_div(o.frame)
        elif node.operator == "%": code += self.emit.emit_mod(o.frame)
        elif node.operator in [">", ">=", "<", "<=", "==", "!="]:
            code += self.emit.emit_re_op(node.operator, lt if is_float_type(lt) or is_float_type(rt) else lt, o.frame)
            res_type = PrimitiveType("boolean")
            
        return code, res_type

    def visit_unary_op(self, node: "UnaryOp", o: Access = None):
        """
        Visit unary operation.
        Implement unary operation code generation
        """
        code, typ = self.visit(node.operand, o)
        if node.operator == "-":
            return code + self.emit.emit_neg_op(typ, o.frame), typ
        elif node.operator == "!":
            return code + self.emit.emit_not(PrimitiveType("boolean"), o.frame), PrimitiveType("boolean")
        return code, typ

    def visit_postfix_expression(self, node: "PostfixExpression", o: Access = None):
        """
        Visit postfix expression (method calls, member access, array access).
        Implement postfix expression code generation *
        """
        code, typ = self.visit(node.operand, o)
        if node.operator == "-":
            return code + self.emit.emit_neg_op(typ, o.frame), typ
        elif node.operator == "!":
            return code + self.emit.emit_not(PrimitiveType("boolean"), o.frame), PrimitiveType("boolean")
        return code, typ
    
    def visit_method_call(self, node: "MethodCall", o: Access = None):
        """
        Visit method call.
        Implement method call code generation *
        """
        sym = next(filter(lambda x: x.name == node.method_name, o.sym), None)
        if sym is None:
            raise IllegalOperandException(f"Undeclared variable: {node.method_name}")

        # Sinh mã để đẩy các đối số (arguments) lên stack
        arg_code = ""
        for arg in node.args:
            c, t = self.visit(arg, Access(o.frame, o.sym, False))
            arg_code += c

        # Gọi hàm tĩnh từ class 'io'
        if isinstance(sym.value, CName):
            cname = sym.value.value
            mname = node.method_name

            # Ánh xạ print sang writeStr của thư viện io
            if cname == "io" and mname == "print":
                mname = "writeStr"

            # Ánh xạ int2str sang String.valueOf của Java để lấy kết quả "42"
            if mname == "int2str":
                return arg_code + self.emit.emit_invoke_static(
                    "java/lang/String/valueOf",
                    FunctionType([PrimitiveType("int")], PrimitiveType("string")),
                    o.frame
                ), PrimitiveType("string")

            invoke_code = self.emit.emit_invoke_static(f"{cname}/{mname}", sym.type, o.frame)
            return arg_code + invoke_code, sym.type.return_type

        return arg_code, sym.type.return_type

    def visit_member_access(self, node: "MemberAccess", o: Access = None):
        """
        Visit member access.
        Implement member access code generation
        """
        # o.is_first holds the type of the base expression
        class_name = o.is_first.class_name
        return self.emit.emit_get_field(f"{class_name}/{node.member_name}", o.is_first, o.frame), o.is_first

    def visit_array_access(self, node: "ArrayAccess", o: Access = None):
        """
        Visit array access.
        Implement array access code generation
        """
        idx_code, _ = self.visit(node.index, Access(o.frame, o.sym))
        elem_type = o.is_first.element_type
        return idx_code + self.emit.emit_aload(elem_type, o.frame), elem_type

    def visit_object_creation(self, node: "ObjectCreation", o: Access = None):
        """
        Visit object creation.
        Implement object creation code generation *
        """
        code = self.emit.jvm.emitNEW(node.class_name)
        code += self.emit.emit_dup(o.frame)
        o.frame.push() # new pushes obj
        arg_types = []
        for arg in node.args:
            ac, at = self.visit(arg, Access(o.frame, o.sym))
            code += ac
            arg_types.append(at)
        code += self.emit.emit_invoke_special(o.frame, f"{node.class_name}/<init>", FunctionType(arg_types, PrimitiveType("void")))
        return code, ClassType(node.class_name)


    def visit_identifier(self, node: "Identifier", o: Access = None):
        """
        Visit identifier - generate code to read variable.
        """
        if o is None:
            return "", None

        # Find symbol
        sym = next(filter(lambda x: x.name == node.name, o.sym), None)
        if sym is None:
            raise IllegalOperandException(f"Undeclared identifier: {node.name}")

        if type(sym.value) is Index:
            code = self.emit.emit_read_var(
                sym.name, sym.type, sym.value.value, o.frame
            )
            return code, sym.type
        return "", sym.type

    def visit_this_expression(self, node: "ThisExpression", o: Access = None):
        """
        Visit this expression - load 'this' reference.
        """
        if o is None:
            return "", None
        
        # Find 'this' in symbol table (should be at index 0 for instance methods)
        this_sym = next(filter(lambda x: x.name == "this", o.sym), None)
        if this_sym is None:
            raise IllegalOperandException("'this' not available in static context")
        
        if type(this_sym.value) is Index:
            code = self.emit.emit_read_var(
                "this", this_sym.type, this_sym.value.value, o.frame
            )
            return code, this_sym.type
        else:
            raise IllegalOperandException("Invalid 'this' reference")

    def visit_parenthesized_expression(
        self, node: "ParenthesizedExpression", o: Access = None
    ):
        """
        Visit parenthesized expression - just visit inner expression.
        """
        return self.visit(node.expr, o)

    # ============================================================================
    # Literals
    # ============================================================================

    def visit_int_literal(self, node: "IntLiteral", o: Access = None):
        """
        Visit integer literal - push integer constant.
        """
        if o is None:
            return "", None
        code = self.emit.emit_push_iconst(node.value, o.frame)
        return code, PrimitiveType("int")

    def visit_float_literal(self, node: "FloatLiteral", o: Access = None):
        """
        Visit float literal - push float constant.
        """
        if o is None:
            return "", None
        code = self.emit.emit_push_fconst(str(node.value), o.frame)
        return code, PrimitiveType("float")

    def visit_bool_literal(self, node: "BoolLiteral", o: Access = None):
        """
        Visit boolean literal - push boolean constant.
        """
        if o is None:
            return "", None
        value_str = "1" if node.value else "0"
        code = self.emit.emit_push_iconst(value_str, o.frame)
        return code, PrimitiveType("boolean")

    def visit_string_literal(self, node: "StringLiteral", o: Access = None):
        """
        Visit string literal - push string constant.
        """
        if o is None:
            return "", None
        code = self.emit.emit_push_const('"' + node.value + '"', PrimitiveType("string"), o.frame)
        return code, PrimitiveType("string")

    def visit_array_literal(self, node: "ArrayLiteral", o: Access = None):
        """
        Visit array literal.
         Implement array literal code generation
        """
        # OPLang Array Literal: {1, 2, 3}
        code = self.emit.emit_push_iconst(len(node.value), o.frame)
        elem_type = PrimitiveType("int") # Default or infer
        if len(node.value) > 0:
            _, elem_type = self.visit(node.value[0], o)
            # Pop result of inference visit if needed
            o.frame.pop()
            
        code += self.emit.emit_new_array(self.emit.get_full_type(elem_type))
        for i, val in enumerate(node.value):
            code += self.emit.emit_dup(o.frame)
            code += self.emit.emit_push_iconst(i, o.frame)
            vc, _ = self.visit(val, o)
            code += vc
            code += self.emit.emit_astore(elem_type, o.frame)
        return code, ArrayType(elem_type, len(node.value))

    def visit_nil_literal(self, node: "NilLiteral", o: Access = None):
        """
        Visit nil literal - push null reference.
        """
        if o is None:
            return "", None
        o.frame.push()
        code = self.emit.jvm.emitPUSHNULL()
        return code, None  # Type will be determined by context

    # def visit_method_invocation(self, node: "MethodInvocation", o: Any = None):
    #     pass

    # def visit_static_method_invocation(self, node: "StaticMethodInvocation", o: Any = None):
    #     pass

    # def visit_static_member_access(self, node: "StaticMemberAccess", o: Any = None):
    #     pass

