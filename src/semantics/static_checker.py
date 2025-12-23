"""
Static Semantic Checker for OPLang Programming Language

This module implements a comprehensive static semantic checker using visitor pattern
for the OPLang object-oriented programming language. It performs type checking,
scope management, inheritance validation, and detects all semantic errors as
specified in the OPLang language specification.
"""

# File đang làm nè nha
# 31 thg 10, 2025

from functools import reduce
from typing import Dict, List, Set, Optional, Any, Tuple, Union, NamedTuple
from ..utils.visitor import ASTVisitor
from ..utils.nodes import (
    ASTNode, Program, ClassDecl, AttributeDecl, Attribute, MethodDecl,
    ConstructorDecl, DestructorDecl, Parameter, VariableDecl, Variable,
    AssignmentStatement, IfStatement, ForStatement, BreakStatement,
    ContinueStatement, ReturnStatement, MethodInvocationStatement,
    BlockStatement, PrimitiveType, ArrayType, ClassType, ReferenceType,
    IdLHS, PostfixLHS, BinaryOp, UnaryOp, PostfixExpression, PostfixOp,
    MethodCall, MemberAccess, ArrayAccess, ObjectCreation, Identifier,
    ThisExpression, ParenthesizedExpression, IntLiteral, FloatLiteral,
    BoolLiteral, StringLiteral, ArrayLiteral, NilLiteral, Type
)
from .static_error import (
    StaticError, Redeclared, UndeclaredIdentifier, UndeclaredClass,
    UndeclaredAttribute, UndeclaredMethod, CannotAssignToConstant,
    TypeMismatchInStatement, TypeMismatchInExpression, TypeMismatchInConstant,
    MustInLoop, IllegalConstantExpression, IllegalArrayLiteral,
    IllegalMemberAccess, NoEntryPoint
)


# Final
# MSSV: 2313452
class FunctionType(Type):
    def __init__(self, param_types: List[Type], return_type: Type):
        super().__init__()
        self.param_types = param_types
        self.return_type = return_type

    def accept(self, visitor, o=None):
        return visitor.visit_function_type(self, o)


class Symbol:
    def __init__(self, name: str, typ: 'Type', isFinal: 'bool' = False, isStatic: 'bool' = False):
        self.name = name
        self.typ = typ
        self.isfinal = isFinal
        self.isStatic = isStatic


class StaticChecker(ASTVisitor):
    def __init__(self):
        self.list_class: List[ClassDecl] = []
        self.loop = 0
        self.current_return_type: Optional[Type] = None
        self.in_static_method = False
        self.current_class: Optional[ClassDecl] = None

    def check_program(self, ast):
        self.visit(ast)

    def visit_program(self, node: "Program", o: Any = None):
        # self.list_class += node.class_decls
        # Không cộng dồn để khai báo tuần tự
        self.list_class = []
        reduce(lambda acc, class_decl: [self.visit(class_decl, acc)] + acc[1:], node.class_decls,
               [[Symbol("io", ClassType("io"))]])

        main_found = False
        for cls in self.list_class:
            # self.list_class: List[ClassDecl] = []
            for member in cls.members:
                if isinstance(member, MethodDecl):
                    is_static = member.is_static
                    has_no_params = len(member.params) == 0
                    returns_void = (isinstance(member.return_type,
                                               PrimitiveType) and member.return_type.type_name == "void")

                    if is_static and has_no_params and returns_void:
                        main_found = True
                        break

            if main_found:
                break

        if not main_found:
            raise NoEntryPoint()

    def visit_class_decl(self, node: "ClassDecl", o: list[list[Symbol]] = None) -> list[Symbol]:
        found = next(filter(lambda sym: sym.name == node.name, o[0]), None)
        if found:
            raise Redeclared("Class", node.name)

        # Kiểm tra Undeclared S_are_types_compatibleuperclass
        if node.superclass:
            parent_found = next(filter(lambda sym: sym.name == node.superclass, o[0]), None)
            if not parent_found:
                raise UndeclaredClass(node.superclass)
        self.list_class.append(node)
        self.current_class = node
        # Dùng reduce để duyệt qua các thành viên, truyền vào môi trường mới
        reduce(lambda acc, member: [self.visit(member, acc)] + acc[1:], node.members, [[]] + o)

        self.current_class = None
        # Trả về global scope đã được cập nhật với class mới
        return [Symbol(node.name, ClassType(node.name))] + o[0]

    # HELPING FUNCTIONS
    # Thêm phương thức private này vào class StaticChecker
    # def _check_is_constant_expr(self, expr):
    #     # Biểu thức hằng số không được là nil
    #     if expr is None or isinstance(expr, NilLiteral):
    #         raise IllegalConstantExpression(expr if expr else NilLiteral())
    #     if isinstance(expr, ArrayLiteral):
    #         for element in expr.value:
    #             self._check_is_constant_expr(element)
    #     elif isinstance(expr, ObjectCreation):
    #         for arg in expr.args:
    #             self._check_is_constant_expr(arg)
    #
    #     # Biểu thức hằng số không thể là biến, this, lời gọi hàm,...
    #     elif not isinstance(expr, (IntLiteral, FloatLiteral, BoolLiteral, StringLiteral, BinaryOp, UnaryOp)):
    #         raise IllegalConstantExpression(expr)
    #
    #     # Nếu là toán tử, phải kiểm tra đệ quy các toán hạng
    #     elif isinstance(expr, BinaryOp):
    #         self._check_is_constant_expr(expr.left)
    #         self._check_is_constant_expr(expr.right)
    #     elif isinstance(expr, UnaryOp):
    #         self._check_is_constant_expr(expr.operand)
    #
    # CHECK TYPE COMPATIBALE
    def _are_types_compatible(self, lhs_type: Type, rhs_type: Type) -> bool:
        # Lấy ra kiểu dữ liệu thực sự để so sánh
        comp_lhs_type = lhs_type.referenced_type if isinstance(lhs_type, ReferenceType) else lhs_type
        comp_rhs_type = rhs_type.referenced_type if isinstance(rhs_type, ReferenceType) else rhs_type

        # 1. Cho phép ép kiểu int -> float
        if (isinstance(comp_lhs_type, PrimitiveType) and comp_lhs_type.type_name == "float" and
                isinstance(comp_rhs_type, PrimitiveType) and comp_rhs_type.type_name == "int"):
            return True

        # 2. Nếu hai kiểu không cùng loại, chúng không tương thích
        if type(comp_lhs_type) is not type(comp_rhs_type):
            return False

        # 3. So sánh chi tiết cho từng loại
        if isinstance(comp_lhs_type, PrimitiveType):
            is_type_compatible = comp_lhs_type.type_name == comp_rhs_type.type_name
            return is_type_compatible

        if isinstance(comp_lhs_type, ArrayType):
            if comp_lhs_type.size != comp_rhs_type.size:
                return False
            if isinstance(comp_rhs_type.element_type,
                          PrimitiveType) and comp_rhs_type.element_type.type_name == "unknown":
                return True
            # Quy tắc nghiêm ngặt cho mảng: kiểu phần tử phải giống hệt
            elem_lhs = comp_lhs_type.element_type
            elem_rhs = comp_rhs_type.element_type
            if type(elem_lhs) is not type(elem_rhs): return False
            if isinstance(elem_lhs, PrimitiveType): return elem_lhs.type_name == elem_rhs.type_name
            if isinstance(elem_lhs, ClassType): return elem_lhs.class_name == elem_rhs.class_name
            return False

        if isinstance(comp_lhs_type, ClassType):
            # Xử lý kế thừa
            current_class_name = comp_rhs_type.class_name
            while current_class_name:
                if current_class_name == comp_lhs_type.class_name:
                    return True
                parent_decl = next((cls for cls in self.list_class if cls.name == current_class_name), None)
                current_class_name = parent_decl.superclass if parent_decl else None
            return False

        return False

    def _check_is_constant_expr(self, expr, o=None):
        # Hàm nội bộ để kiểm tra đệ quy và bắt lỗi từ con đẩy lên cha
        def recursive_check(child_expr):
            try:
                self._check_is_constant_expr(child_expr, o)
            except IllegalConstantExpression:
                # Nếu con lỗi, ném lỗi tại node cha hiện tại (expr)
                # Đây là fix cho test_082 và test_084
                raise IllegalConstantExpression(expr)

        if expr is None or isinstance(expr, NilLiteral):
            # Nil không được làm hằng số
            raise IllegalConstantExpression(expr if expr else NilLiteral())

        # 1. Các literal luôn đúng
        if isinstance(expr, (IntLiteral, FloatLiteral, BoolLiteral, StringLiteral)):
            return

        # 2. Mảng và Object: Kiểm tra đệ quy các phần tử
        if isinstance(expr, ArrayLiteral):
            for element in expr.value:
                # Lưu ý: ArrayLiteral lỗi tại chính nó nếu phần tử con lỗi
                self._check_is_constant_expr(element, o)
            return

        if isinstance(expr, ObjectCreation):
            for arg in expr.args:
                # ObjectCreation lỗi tại chính nó nếu tham số lỗi
                self._check_is_constant_expr(arg, o)
            return

        # 3. Biểu thức ngoặc: Kiểm tra bên trong
        if isinstance(expr, ParenthesizedExpression):
            recursive_check(expr.expr)
            return

        # 4. Phép toán hai ngôi: Kiểm tra trái phải
        if isinstance(expr, BinaryOp):
            recursive_check(expr.left)
            recursive_check(expr.right)
            return

        # 5. Phép toán một ngôi: Kiểm tra toán hạng
        if isinstance(expr, UnaryOp):
            recursive_check(expr.operand)
            return

        # 6. Identifier và Postfix (Truy cập thành viên): Fix cho test_086
        # Chỉ hợp lệ nếu có scope (o) và biến đó là final
        if isinstance(expr, (Identifier, PostfixExpression)):
            if o is None:
                raise IllegalConstantExpression(expr)

            # Kiểm tra xem định danh này có phải là hằng số (final) không
            try:
                # Gọi visit để lấy Symbol
                sym = self.visit(expr, o)
                # Nếu visit trả về Type (trường hợp class access), lấy thuộc tính typ nếu cần
                # Nhưng thường Identifier/Postfix trả về Symbol hoặc Type.

                is_final = False
                if isinstance(sym, Symbol):
                    is_final = sym.isfinal
                # Nếu logic của bạn trả về Type cho Enum/Constant đặc biệt, cần handle ở đây
                # Nhưng theo Symbol class của bạn thì check sym.isfinal là chuẩn.

                if not is_final:
                    raise IllegalConstantExpression(expr)
            except IllegalConstantExpression:
                raise
            except Exception:
                # Bất kỳ lỗi nào khác (Undeclared, TypeMismatch...)
                # khi đang check hằng số đều coi là biểu thức hằng không hợp lệ
                raise IllegalConstantExpression(expr)
            return

        # Các trường hợp khác (Call, v.v.)
        raise IllegalConstantExpression(expr)

    def visit_attribute_decl(self, node: "AttributeDecl", o: list[list[Symbol]] = None) -> list[Symbol]:
        current_scope = o[0]
        for attr in node.attributes:
            kind = "Constant" if node.is_final else "Attribute"
            found = next(filter(lambda sym: sym.name == attr.name, current_scope), None)
            if found:
                raise Redeclared(kind, attr.name)

            # Logic for checking valid constant expression
            if node.is_final and attr.init_value:
                self._check_is_constant_expr(attr.init_value, o)

            if attr.init_value:
                init_sym = self.visit(attr.init_value, o)
                if node.is_final and not self._are_types_compatible(node.attr_type, init_sym.typ):
                    raise TypeMismatchInConstant(node)

            new_symbol = Symbol(attr.name, node.attr_type, node.is_final, node.is_static)
            current_scope = [new_symbol] + current_scope

        return current_scope

    # kind: Variable, Constant, Attribute, Class, Method, Parameter
    def visit_attribute(self, node: "Attribute", o: list[list[Symbol]] = None) -> list[Symbol]:
        pass

    def visit_method_decl(self, node: "MethodDecl", o: list[list[Symbol]] = None) -> list[Symbol]:
        current_scope = o[0]

        # --- FIX: Support Method Overloading (Test 121) ---
        # 1. Tìm tất cả các symbol có cùng tên trong scope hiện tại
        entries = [sym for sym in current_scope if sym.name == node.name]

        # 2. Lấy danh sách kiểu tham số của method đang khai báo
        new_param_types = [p.param_type for p in node.params]

        for entry in entries:
            # Nếu trùng tên với Attribute/Constant -> Vẫn là Redeclared (không overload được với field)
            if not isinstance(entry.typ, FunctionType):
                raise Redeclared("Method", node.name)

            # Nếu là Method, kiểm tra signature (danh sách kiểu tham số)
            existing_param_types = entry.typ.param_types

            # Nếu số lượng tham số khác nhau -> OK (Overload hợp lệ) -> Bỏ qua check tiếp
            if len(existing_param_types) != len(new_param_types):
                continue

            # Nếu cùng số lượng, kiểm tra kiểu từng tham số (Strict Match)
            # Hai method trùng nhau khi và chỉ khi TẤT CẢ kiểu tham số giống hệt nhau
            is_duplicate_signature = True
            for t1, t2 in zip(existing_param_types, new_param_types):
                type_differs = False

                # So sánh loại class Type
                if type(t1) is not type(t2):
                    type_differs = True
                elif isinstance(t1, PrimitiveType) and t1.type_name != t2.type_name:
                    type_differs = True
                elif isinstance(t1, ClassType) and t1.class_name != t2.class_name:
                    type_differs = True
                elif isinstance(t1, ArrayType):
                    # So sánh mảng: size và kiểu phần tử
                    if t1.size != t2.size:
                        type_differs = True
                    # Check deep element type (giản lược: check class name/type name)
                    elif isinstance(t1.element_type,
                                    PrimitiveType) and t1.element_type.type_name != t2.element_type.type_name:
                        type_differs = True
                    elif isinstance(t1.element_type,
                                    ClassType) and t1.element_type.class_name != t2.element_type.class_name:
                        type_differs = True

                if type_differs:
                    is_duplicate_signature = False
                    break

            # Nếu signature y hệt -> Lỗi Redeclared thực sự
            if is_duplicate_signature:
                raise Redeclared("Method", node.name)
        # ----------------------------------------------------

        # (Logic cũ: Tạo scope cho param và visit body)
        param_scope = []
        for param in node.params:
            found_param = next(filter(lambda p: p.name == param.name, param_scope), None)
            if found_param:
                raise Redeclared("Parameter", param.name)
            param_scope += [Symbol(param.name, param.param_type)] + param_scope

        # Check conflicts between params and var in body
        if isinstance(node.body, BlockStatement):
            for decl in node.body.var_decls:
                for var in decl.variables:
                    if any(p.name == var.name for p in param_scope):
                        kind = "Constant" if decl.is_final else "Variable"
                        raise Redeclared(kind, var.name)

        # Logic quản lý static method
        old_in_static = self.in_static_method
        self.in_static_method = node.is_static

        try:
            self.current_return_type = node.return_type
            self.visit(node.body, [param_scope] + o[1:])
        finally:
            self.current_return_type = None
            self.in_static_method = old_in_static

        method_type = FunctionType([p.param_type for p in node.params], node.return_type)

        # Cộng dồn symbol vào scope hiện tại
        return [Symbol(node.name, method_type, isStatic=node.is_static)] + current_scope

    def visit_constructor_decl(self, node: "ConstructorDecl", o: list[list[Symbol]] = None) -> list[Symbol]:
        current_scope = o[0]

        param_scope = []

        for param in node.params:
            found_param = next(filter(lambda sym: sym.name == param.name, param_scope), None)
            if found_param:
                raise Redeclared("Parameter", param.name)

            param_scope += [Symbol(param.name, param.param_type)]

            # Visit thân hàm với môi trường mới
        self.visit(node.body, [param_scope] + o)
        return current_scope

    def visit_destructor_decl(self, node: "DestructorDecl", o: list[list[Symbol]] = None) -> list[Symbol]:
        self.visit(node.body, o)
        return o[0]

    def visit_parameter(self, node: "Parameter", o: list[list[Symbol]] = None) -> list[Symbol]:
        return [Symbol(node.name, node.param_type)] + o[0]

    def visit_block_statement(self, node: "BlockStatement", o: list[list[Symbol]] = None) -> list[Symbol]:
        local_scope = reduce(lambda acc, decl: self.visit(decl, [acc] + o), node.var_decls, [])
        """
        Khi muốn tạo một môi trường env mới để 
        visit xuống sâu hơn, quy tắc gần như luôn luôn là:

        new_env = [scope_mới] + scope_cũ
        """

        # Môi trường mới để duyệt các statements: [local_scope, param_scope, class_scope, ...]
        new_env = [local_scope] + o

        # Duyệt qua các statements
        list(map(lambda stmt: self.visit(stmt, new_env), node.statements))

        return o[0]

    def visit_variable_decl(self, node: "VariableDecl", o: list[list[Symbol]] = None) -> list[Symbol]:
        current_scope = o[0]

        for var in node.variables:
            kind = "Constant" if node.is_final else "Variable"

            found_in_local = next(filter(lambda sym: sym.name == var.name, current_scope), None)
            if found_in_local:
                raise Redeclared(kind, var.name)

            if node.is_final:
                self._check_is_constant_expr(var.init_value, o)

            if var.init_value:
                init_sym = self.visit(var.init_value, o)
                if not self._are_types_compatible(node.var_type, init_sym.typ):
                    if node.is_final:
                        raise TypeMismatchInConstant(node)
                    else:
                        raise TypeMismatchInStatement(node)

            current_scope = [Symbol(var.name, node.var_type, node.is_final)] + current_scope

        return current_scope

    def visit_variable(self, node: "Variable", o: Any = None):
        pass

    def visit_assignment_statement(self, node: "AssignmentStatement", o: list[list[Symbol]] = None) -> list[Symbol]:
        lhs_symbol = self.visit(node.lhs, o)
        rhs_symbol = self.visit(node.rhs, o)

        if lhs_symbol.isfinal:
            raise CannotAssignToConstant(node)

        lhs_type = lhs_symbol.typ
        rhs_type = rhs_symbol.typ

        if not self._are_types_compatible(lhs_type, rhs_type):
            raise TypeMismatchInStatement(node)

        return o[0]

    def visit_if_statement(self, node: "IfStatement", o: Any = None):
        condition_symbol = self.visit(node.condition, o)
        if not isinstance(condition_symbol.typ, PrimitiveType) or condition_symbol.typ.type_name != "boolean":
            raise TypeMismatchInStatement(node)

        self.visit(node.then_stmt, o)

        if node.else_stmt:
            self.visit(node.else_stmt, o)

    def visit_for_statement(self, node: "ForStatement", o: list[list[Symbol]] = None) -> list[Symbol]:
        start_symbol = self.visit(node.start_expr, o)
        end_symbol = self.visit(node.end_expr, o)

        if (not isinstance(start_symbol.typ, PrimitiveType) or start_symbol.typ.type_name != "int" or
                not isinstance(end_symbol.typ, PrimitiveType) or end_symbol.typ.type_name != "int"):
            raise TypeMismatchInStatement(node)

        var_found = reduce(
            lambda found_so_far, scope: found_so_far or next(filter(lambda sym: sym.name == node.variable, scope),
                                                             None), o, None)

        # Note: If undeclared, it should have been caught elsewhere, but for TypeMismatch checks:
        if var_found:
            if not isinstance(var_found.typ, PrimitiveType) or var_found.typ.type_name != "int":
                raise TypeMismatchInStatement(node)

        if self.current_class:
            for member in self.current_class.members:
                if isinstance(member, AttributeDecl):
                    for attr in member.attributes:
                        if attr.name == node.variable and member.is_final:
                            raise CannotAssignToConstant(node)

        self.loop += 1
        self.visit(node.body, o)
        self.loop -= 1
        return o[0]

    def visit_break_statement(self, node: "BreakStatement", o: list[list[Symbol]] = None) -> list[Symbol]:
        if self.loop == 0:
            raise MustInLoop(node)
        return o[0]

    def visit_continue_statement(self, node: "ContinueStatement", o: list[list[Symbol]] = None) -> list[Symbol]:
        if self.loop == 0:
            raise MustInLoop(node)
        return o[0]

    def visit_return_statement(self, node: "ReturnStatement", o: Any = None):
        if self.current_return_type:
            expected_type = self.current_return_type

            # Trường hợp 1: Hàm yêu cầu void
            if isinstance(expected_type, PrimitiveType) and expected_type.type_name == 'void':
                if node.value and not isinstance(node.value, NilLiteral):
                    raise TypeMismatchInStatement(node)
            # Trường hợp 2: Hàm yêu cầu kiểu cụ thể
            else:
                if not node.value or isinstance(node.value, NilLiteral):
                    raise TypeMismatchInStatement(node)

                return_sym = self.visit(node.value, o)
                actual_type = return_sym.typ

                # SO SÁNH NGHIÊM NGẶT: Không dùng _are_types_compatible
                if type(expected_type) is not type(actual_type):
                    raise TypeMismatchInStatement(node)
                if isinstance(expected_type, PrimitiveType) and expected_type.type_name != actual_type.type_name:
                    raise TypeMismatchInStatement(node)
                if isinstance(expected_type, ClassType) and expected_type.class_name != actual_type.class_name:
                    raise TypeMismatchInStatement(node)
                # (Thêm logic cho ArrayType nếu cần)
        return o[0]

    def visit_id_lhs(self, node: "IdLHS", o: list[list[Symbol]] = None) -> Type:
        # find in all scopes
        # found = next((sym for scope in o for sym in scope if sym.name == node.name), None)

        # Here: wtf ??!!!
        found = reduce(
            lambda found_so_far, scope: found_so_far or next(filter(lambda sym: sym.name == node.name, scope), None), o,
            None)
        if not found:
            raise UndeclaredIdentifier(node.name)

        return found

    def visit_identifier(self, node: "Identifier", o: list[list[Symbol]] = None) -> list[Symbol]:
        found = reduce(
            lambda found_so_far, scope: found_so_far or next(filter(lambda sym: sym.name == node.name, scope), None), o,
            None)

        if not found:
            class_found = next(filter(lambda cls: cls.name == node.name, self.list_class), None)
            if class_found:
                return Symbol(node.name, ClassType(node.name))
            raise UndeclaredIdentifier(node.name)

        return found

    # def visit_postfix_expression(self, node: "PostfixExpression", o: list[list[Symbol]] = None) -> Type:
    #     if not node.postfix_ops:
    #         obj = self.visit(node.primary, o)
    #         return obj if isinstance(obj, Symbol) else Symbol("", obj)

    #     # Xác định ngữ cảnh truy cập: static (A.foo) hay instance (a.foo)
    #     is_static_access = (isinstance(node.primary, Identifier) and
    #                         any(cls.name == node.primary.name for cls in self.list_class))

    #     obj_type_or_symbol = self.visit(node.primary, o)

    #     if isinstance(obj_type_or_symbol, Type):
    #         obj_type = obj_type_or_symbol
    #     else:
    #         obj_type = obj_type_or_symbol.typ

    #     # store the final member in postfix_ops
    #     final_member_symbol = None

    #     for op in node.postfix_ops:

    #         # Not ClassType
    #         if not isinstance(obj_type, ClassType):
    #             raise TypeMismatchInExpression(node)

    #         class_name = obj_type.class_name

    #         if class_name == "io":
    #             if not isinstance(op, MethodCall):
    #                 # io không có thuộc tính, chỉ có phương thức
    #                 raise IllegalMemberAccess(op)

    #             method_name = op.method_name
    #             # arg_symbols = [self.visit(arg, o) for arg in op.args]
    #             arg_symbols = list(map(lambda arg: self.visit(arg, o), op.args))

    #             # arg_types = [sym.typ for sym in arg_symbols]
    #             arg_types = list(map(lambda sym: sym.typ, arg_symbols))

    #             # Định nghĩa API của thư viện 'io'
    #             io_api = {
    #                 "readInt": ([], PrimitiveType("int")),
    #                 "writeInt": ([PrimitiveType("int")], PrimitiveType("void")),
    #                 "writeIntLn": ([PrimitiveType("int")], PrimitiveType("void")),
    #                 "readFloat": ([], PrimitiveType("float")),
    #                 "writeFloat": ([PrimitiveType("float")], PrimitiveType("void")),
    #                 "writeFloatLn": ([PrimitiveType("float")], PrimitiveType("void")),
    #                 "readBool": ([], PrimitiveType("boolean")),
    #                 "writeBool": ([PrimitiveType("boolean")], PrimitiveType("void")),
    #                 "writeBoolLn": ([PrimitiveType("boolean")], PrimitiveType("void")),
    #                 "readStr": ([], PrimitiveType("string")),
    #                 "writeStr": ([PrimitiveType("string")], PrimitiveType("void")),
    #                 "writeStrLn": ([PrimitiveType("string")], PrimitiveType("void")),
    #             }

    #             if method_name not in io_api:
    #                 raise UndeclaredMethod(method_name)

    #             expected_params, return_type = io_api[method_name]

    #             # 1. Kiểm tra số lượng đối số
    #             if len(arg_types) != len(expected_params):
    #                 raise TypeMismatchInExpression(node)

    #             # 2. Kiểm tra kiểu của đối số (nếu có)
    #             if len(expected_params) > 0:
    #                 if not self._are_types_compatible(expected_params[0], arg_types[0]):
    #                     raise TypeMismatchInExpression(node)

    #             obj_type = return_type
    #             continue # Bỏ qua phần tra cứu ClassDecl và tiếp tục
    #         class_decl = next(filter(lambda cls: cls.name == class_name, self.list_class), None)

    #         if not class_decl:
    #             raise UndeclaredClass(class_name)

    #         # Attribute access
    #         if isinstance(op, MemberAccess):
    #             member_name = op.member_name
    #             found_attr_symbol = None

    #             current_class = class_decl
    #             while current_class:
    #                 for member in class_decl.members:
    #                     if isinstance(member, AttributeDecl):
    #                         if any (attr.name == member_name for attr in member.attributes):
    #                             found_attr_symbol = Symbol(member_name, member.attr_type, member.is_final, member.is_static)
    #                             break
    #                 if found_attr_symbol:
    #                     break
    #                 if current_class.superclass:
    #                     current_class = next(filter(lambda cls: cls.name == current_class.name, self.list_class), None)
    #                 else:
    #                     current_class = None

    #             if not found_attr_symbol:
    #                 raise UndeclaredAttribute(member_name)

    #             if is_static_access and not found_attr_symbol.isStatic:
    #                 raise IllegalMemberAccess(op)
    #             if not is_static_access and found_attr_symbol.isStatic and not isinstance(node.primary, ThisExpression):
    #                 raise IllegalMemberAccess(op)

    #             final_member_symbol = found_attr_symbol
    #             obj_type = final_member_symbol.typ

    #         # Method calls
    #         elif isinstance(op, MethodCall):
    #             method_name = op.method_name
    #             found_method = None

    #             current_class = class_decl
    #             while current_class:
    #                 found_method = next((m for m in current_class.members if isinstance(m, MethodDecl) and m.name == method_name), None)
    #                 if found_method:
    #                     break
    #                 # Leo lên cha
    #                 if current_class.superclass:
    #                      current_class = next((cls for cls in self.list_class if cls.name == current_class.superclass), None)
    #                 else:
    #                     current_class = None

    #             if not found_method:
    #                 raise UndeclaredMethod(method_name)

    #             param_types = list(map(lambda p: p.param_type, found_method.params))
    #             arg_symbols = [self.visit(arg, o) for arg in op.args]
    #             arg_types = [sym.typ for sym in arg_symbols]

    #             if len(param_types) != len(arg_types):
    #                 raise TypeMismatchInExpression(node)

    #             for param_t, arg_t in zip(param_types, arg_types):
    #                 if not self._are_types_compatible(param_t, arg_t):
    #                     raise TypeMismatchInExpression(node)

    #             # KIỂM TRA MỚI: IllegalMemberAccess
    #             if is_static_access and not found_method.is_static:
    #                 raise IllegalMemberAccess(op)
    #             if not is_static_access and found_method.is_static:
    #                 raise IllegalMemberAccess(op)

    #             # Tạo Symbol cho phương thức tìm thấy
    #             method_type = FunctionType([p.param_type for p in found_method.params], found_method.return_type)
    #             final_member_symbol = Symbol(method_name, method_type, isStatic=found_method.is_static)
    #             obj_type = final_member_symbol.typ.return_type # Cập nhật type cho vòng lặp tiếp theo

    #     last_op = node.postfix_ops[-1]

    #     if isinstance(last_op, MemberAccess):
    #         return final_member_symbol

    #     elif isinstance(last_op, MethodCall):
    #         return Symbol("", obj_type)

    #     return final_member_symbol
    def visit_postfix_expression(self, node: "PostfixExpression", o: list[list[Symbol]] = None) -> Type:
        if not node.postfix_ops:
            obj = self.visit(node.primary, o)
            return obj if isinstance(obj, Symbol) else Symbol("", obj)

        # Xác định ngữ cảnh truy cập: static (A.foo) hay instance (a.foo)
        is_static_access = (isinstance(node.primary, Identifier) and
                            any(cls.name == node.primary.name for cls in self.list_class))

        obj_type_or_symbol = self.visit(node.primary, o)

        if isinstance(obj_type_or_symbol, Type):
            obj_type = obj_type_or_symbol
        else:
            obj_type = obj_type_or_symbol.typ

        final_member_symbol = None

        for op in node.postfix_ops:
            # FIX: Add ArrayAccess handling - test061
            if isinstance(op, ArrayAccess):
                if not isinstance(obj_type, ArrayType):
                    raise TypeMismatchInExpression(node)

                idx_sym = self.visit(op.index, o)
                if not isinstance(idx_sym.typ, PrimitiveType) or idx_sym.typ.type_name != "int":
                    raise TypeMismatchInExpression(node)

                obj_type = obj_type.element_type
                final_member_symbol = Symbol("", obj_type)
                continue

            if not isinstance(obj_type, ClassType):
                raise TypeMismatchInExpression(node)

            class_name = obj_type.class_name

            # --- XỬ LÝ LỚP IO (Giữ nguyên logic cũ) ---
            if class_name == "io":
                if not isinstance(op, MethodCall):
                    raise IllegalMemberAccess(node)

                method_name = op.method_name
                arg_symbols = list(map(lambda arg: self.visit(arg, o), op.args))
                arg_types = list(map(lambda sym: sym.typ, arg_symbols))

                io_api = {
                    "readInt": ([], PrimitiveType("int")),
                    "writeInt": ([PrimitiveType("int")], PrimitiveType("void")),
                    "writeIntLn": ([PrimitiveType("int")], PrimitiveType("void")),
                    "readFloat": ([], PrimitiveType("float")),
                    "writeFloat": ([PrimitiveType("float")], PrimitiveType("void")),
                    "writeFloatLn": ([PrimitiveType("float")], PrimitiveType("void")),
                    "readBool": ([], PrimitiveType("boolean")),
                    "writeBool": ([PrimitiveType("boolean")], PrimitiveType("void")),
                    "writeBoolLn": ([PrimitiveType("boolean")], PrimitiveType("void")),
                    "readStr": ([], PrimitiveType("string")),
                    "writeStr": ([PrimitiveType("string")], PrimitiveType("void")),
                    "writeStrLn": ([PrimitiveType("string")], PrimitiveType("void")),
                }

                if method_name not in io_api:
                    raise UndeclaredMethod(method_name)

                expected_params, return_type = io_api[method_name]
                if len(arg_types) != len(expected_params):
                    raise TypeMismatchInExpression(node)
                if len(expected_params) > 0:
                    if not self._are_types_compatible(expected_params[0], arg_types[0]):
                        raise TypeMismatchInExpression(node)

                obj_type = return_type
                continue

                # --- XỬ LÝ LỚP THƯỜNG ---
            class_decl = next(filter(lambda cls: cls.name == class_name, self.list_class), None)
            if not class_decl:
                raise UndeclaredClass(class_name)

            # Attribute access
            if isinstance(op, MemberAccess):
                member_name = op.member_name
                found_attr_symbol = None

                # --- LOGIC MỚI: DUYỆT LÊN CÁC LỚP CHA ĐỂ TÌM ATTRIBUTE ---
                current_class = class_decl
                while current_class:
                    for member in current_class.members:
                        if isinstance(member, AttributeDecl):
                            if any(attr.name == member_name for attr in member.attributes):
                                found_attr_symbol = Symbol(member_name, member.attr_type, member.is_final,
                                                           member.is_static)
                                break
                    if found_attr_symbol:
                        break
                    # Leo lên cha
                    if current_class.superclass:
                        current_class = next(filter(lambda cls: cls.name == current_class.superclass, self.list_class),
                                             None)
                    else:
                        current_class = None
                # ---------------------------------------------------------

                if not found_attr_symbol:
                    raise UndeclaredAttribute(member_name)

                if is_static_access and not found_attr_symbol.isStatic:
                    raise IllegalMemberAccess(node)
                if not is_static_access and found_attr_symbol.isStatic and not isinstance(node.primary, ThisExpression):
                    raise IllegalMemberAccess(node)

                final_member_symbol = found_attr_symbol
                obj_type = final_member_symbol.typ

            # Method calls
            elif isinstance(op, MethodCall):
                method_name = op.method_name
                found_method = None

                # --- LOGIC MỚI: DUYỆT LÊN CÁC LỚP CHA ĐỂ TÌM METHOD ---
                current_class = class_decl
                while current_class:
                    found_method = next(
                        filter(lambda m: isinstance(m, MethodDecl) and m.name == method_name, current_class.members),
                        None)
                    if found_method:
                        break
                    # Leo lên cha
                    if current_class.superclass:
                        current_class = next(filter(lambda cls: cls.name == current_class.superclass, self.list_class),
                                             None)
                    else:
                        current_class = None
                        # -----------------------------------------------------

                if not found_method:
                    raise UndeclaredMethod(method_name)

                param_types = list(map(lambda p: p.param_type, found_method.params))
                arg_symbols = [self.visit(arg, o) for arg in op.args]
                arg_types = [sym.typ for sym in arg_symbols]

                if len(param_types) != len(arg_types):
                    raise TypeMismatchInExpression(node)

                for param_t, arg_t in zip(param_types, arg_types):
                    if not self._are_types_compatible(param_t, arg_t):
                        raise TypeMismatchInExpression(node)

                if is_static_access and not found_method.is_static:
                    raise IllegalMemberAccess(node)
                if not is_static_access and found_method.is_static:
                    raise IllegalMemberAccess(node)

                method_type = FunctionType([p.param_type for p in found_method.params], found_method.return_type)
                final_member_symbol = Symbol(method_name, method_type, isStatic=found_method.is_static)
                obj_type = final_member_symbol.typ.return_type

        last_op = node.postfix_ops[-1]

        if isinstance(last_op, MemberAccess):
            return final_member_symbol
        elif isinstance(last_op, MethodCall):
            return Symbol("", obj_type)

        return final_member_symbol

    def visit_method_invocation_statement(self, node: "MethodInvocationStatement", o: list[list[Symbol]] = None) -> \
    list[Symbol]:
        try:
            # Sửa ở đây: node.method_call
            self.visit(node.method_call, o)
        except TypeMismatchInExpression:
            raise TypeMismatchInStatement(node)
        return o[0]

    def visit_postfix_lhs(self, node: "PostfixLHS", o: list[list[Symbol]] = None) -> Symbol:
        try:
            return self.visit(node.postfix_expr, o)
        except IllegalMemberAccess:
            raise IllegalMemberAccess(node)

    def visit_method_call(self, node: "MethodCall", o: Any = None):
        pass

    def visit_member_access(self, node: "MemberAccess", o: Any = None):
        pass

    def visit_this_expression(self, node: "ThisExpression", o: list[list[Symbol]] = None) -> ClassType:
        if self.in_static_method:
            raise UndeclaredIdentifier("this")
            # Sử dụng current_class nếu có, fallback về logic cũ nếu cần
        if self.current_class:
            return ClassType(self.current_class.name)
        return ClassType(self.list_class[len(o[-1]) - 1].name)

    ##! -------------- Task 2 --------------
    def visit_parenthesized_expression(
            self, node: "ParenthesizedExpression", o: Any = None
    ):
        self.visit(node.expr, o)

    def visit_object_creation(self, node: "ObjectCreation", o: Any = None) -> Symbol:
        # 1. Tìm ClassDecl của lớp đang được tạo
        class_name = node.class_name
        class_decl = next(filter(lambda cls: cls.name == class_name, self.list_class), None)

        if not class_decl:
            raise UndeclaredClass(class_name)

        # 2. Lấy kiểu của các đối số (arguments) được truyền vào
        arg_symbols = [self.visit(arg, o) for arg in node.args]
        arg_types = [sym.typ for sym in arg_symbols]

        # 3. Tìm tất cả các constructor trong lớp đó
        constructors = [mem for mem in class_decl.members if isinstance(mem, ConstructorDecl)]

        # 4. Tìm một constructor phù hợp
        found_constructor = False
        # --- LOGIC MỚI: XỬ LÝ DEFAULT CONSTRUCTOR ---
        if not constructors and not node.args:
            # Nếu class không có constructor nào VÀ lời gọi không có đối số -> Hợp lệ (Default Constructor)
            found_constructor = True
        else:
            # Logic cũ: Duyệt qua các constructor đã khai báo
            for constr in constructors:
                param_types = [p.param_type for p in constr.params]

                if len(param_types) != len(arg_types):
                    continue

                if all(self._are_types_compatible(param, arg) for param, arg in zip(param_types, arg_types)):
                    found_constructor = True
                    break

        # 5. Nếu không tìm thấy constructor nào phù hợp, ném ra lỗi
        if not found_constructor:
            raise TypeMismatchInExpression(node)

        # 6. Nếu hợp lệ, trả về một Symbol đại diện cho đối tượng mới
        return Symbol(class_name, ClassType(class_name))

    def visit_primitive_type(self, node: "PrimitiveType", o: Any = None):
        pass

    def visit_array_type(self, node: "ArrayType", o: Any = None):
        pass

    def visit_class_type(self, node: "ClassType", o: Any = None):
        pass

    def visit_reference_type(self, node: "ReferenceType", o: Any = None):
        pass

    def visit_binary_op(self, node: "BinaryOp", o: Any = None) -> Symbol:
        left_sym = self.visit(node.left, o)
        right_sym = self.visit(node.right, o)
        left_type = left_sym.typ
        right_type = right_sym.typ
        op = node.operator

        # Phép toán số học: +, -, *, /
        if op in ['+', '-', '*', '/']:
            if not (isinstance(left_type, PrimitiveType) and left_type.type_name in ["int", "float"] and
                    isinstance(right_type, PrimitiveType) and right_type.type_name in ["int", "float"]):
                raise TypeMismatchInExpression(node)
            if left_type.type_name == "float" or right_type.type_name == "float":
                return Symbol("", PrimitiveType("float"))
            return Symbol("", PrimitiveType("int"))

        # Phép toán % và \ (chỉ cho int)
        elif op == "%":
            if not (isinstance(left_type, PrimitiveType) and left_type.type_name == "int" and
                    isinstance(right_type, PrimitiveType) and right_type.type_name == "int"):
                raise TypeMismatchInExpression(node)
            return Symbol("", PrimitiveType("int"))

        elif op == '^':
            if not (isinstance(left_type, PrimitiveType) and left_type.type_name == "string" and
                    isinstance(right_type, PrimitiveType) and right_type.type_name == "string"):
                raise TypeMismatchInExpression(node)
            return Symbol("", PrimitiveType("string"))

        # Relational Operators (==, !=, <, >, <=, >=)
        elif op in ['==', '!=', '<', '>', '<=', '>=']:
            # Check type compatibility
            valid = False

            # For strict equality/inequality, usually types must be compatible
            if op in ['==', '!=']:
                # Example rule: Types must be same or coercible
                # Usually checking simple compatibility is enough,
                # or specifically allowing int/float mix and boolean/boolean
                if self._are_types_compatible(left_type, right_type) or self._are_types_compatible(right_type,
                                                                                                   left_type):
                    valid = True
                # Also allow int/float comparisons specifically if not covered by compatible
                if (isinstance(left_type, PrimitiveType) and left_type.type_name in ['int', 'float'] and
                        isinstance(right_type, PrimitiveType) and right_type.type_name in ['int', 'float']):
                    valid = True

            # For ordering <, >, <=, >=, usually only numeric
            else:
                if (isinstance(left_type, PrimitiveType) and left_type.type_name in ['int', 'float'] and
                        isinstance(right_type, PrimitiveType) and right_type.type_name in ['int', 'float']):
                    valid = True

            if not valid:
                raise TypeMismatchInExpression(node)
            return Symbol("", PrimitiveType("boolean"))

        # Boolean Operators (&&, ||)
        elif op in ['&&', '||']:
            if not (isinstance(left_type, PrimitiveType) and left_type.type_name == "boolean" and
                    isinstance(right_type, PrimitiveType) and right_type.type_name == "boolean"):
                raise TypeMismatchInExpression(node)
            return Symbol("", PrimitiveType("boolean"))
        return Symbol("", PrimitiveType("boolean"))

    def visit_unary_op(self, node: "UnaryOp", o: Any = None) -> Symbol:
        operand_sym = self.visit(node.operand, o)
        operand_type = operand_sym.typ
        op = node.operator

        if op == '-':
            if not (isinstance(operand_type, PrimitiveType) and operand_type.type_name in ["int", "float"]):
                raise TypeMismatchInExpression(node)
            return Symbol("", operand_type)  # Return int or float depending on input

        elif op == '!':
            if not (isinstance(operand_type, PrimitiveType) and operand_type.type_name == "boolean"):
                raise TypeMismatchInExpression(node)
            return Symbol("", PrimitiveType("boolean"))

        return Symbol("", operand_type)

    def visit_array_access(self, node: "ArrayAccess", o: Any = None):
        pass

    # Primtive type
    def visit_int_literal(self, node: "IntLiteral", o: Any = None):
        return Symbol("", PrimitiveType("int"))

    def visit_float_literal(self, node: "FloatLiteral", o: Any = None):
        return Symbol("", PrimitiveType("float"))

    def visit_bool_literal(self, node: "BoolLiteral", o: Any = None):
        return Symbol("", PrimitiveType("boolean"))

    def visit_string_literal(self, node: "StringLiteral", o: Any = None):
        return Symbol("", PrimitiveType("string"))

    def visit_array_literal(self, node: "ArrayLiteral", o: Any = None):
        if not node.value:
            return Symbol("", ArrayType(PrimitiveType("unknown"), 0))

        # Type of array = type of first element
        element_symbols = [self.visit(elem, o) for elem in node.value]
        array_type = element_symbols[0].typ

        for current_sym in element_symbols[1:]:
            if type(array_type) is not type(current_sym.typ) or \
                    (isinstance(array_type, PrimitiveType) and array_type.type_name != current_sym.typ.type_name):
                raise IllegalArrayLiteral(node)

        return Symbol("", ArrayType(array_type, len(node.value)))

    def visit_nil_literal(self, node: "NilLiteral", o: Any = None):
        return Symbol("", PrimitiveType("nil"))