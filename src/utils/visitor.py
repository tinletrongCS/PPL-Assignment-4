"""
Visitor interface for AST traversal in OPLang programming language.
This module defines the abstract visitor pattern interface for traversing
and processing AST nodes.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .nodes import *


class ASTVisitor(ABC):
    """Abstract base class for AST visitors."""

    def visit(self, node: "ASTNode", o: Any = None):
        """Visit a node using the visitor pattern."""
        return node.accept(self, o)

    # Program and class declarations
    @abstractmethod
    def visit_program(self, node: "Program", o: Any = None):
        pass

    @abstractmethod
    def visit_class_decl(self, node: "ClassDecl", o: Any = None):
        pass

    # Attribute declarations
    @abstractmethod
    def visit_attribute_decl(self, node: "AttributeDecl", o: Any = None):
        pass

    @abstractmethod
    def visit_attribute(self, node: "Attribute", o: Any = None):
        pass

    # Method declarations
    @abstractmethod
    def visit_method_decl(self, node: "MethodDecl", o: Any = None):
        pass

    @abstractmethod
    def visit_constructor_decl(self, node: "ConstructorDecl", o: Any = None):
        pass

    @abstractmethod
    def visit_destructor_decl(self, node: "DestructorDecl", o: Any = None):
        pass

    @abstractmethod
    def visit_parameter(self, node: "Parameter", o: Any = None):
        pass

    # Type system
    @abstractmethod
    def visit_primitive_type(self, node: "PrimitiveType", o: Any = None):
        pass

    @abstractmethod
    def visit_array_type(self, node: "ArrayType", o: Any = None):
        pass

    @abstractmethod
    def visit_class_type(self, node: "ClassType", o: Any = None):
        pass

    @abstractmethod
    def visit_reference_type(self, node: "ReferenceType", o: Any = None):
        pass

    # Statements
    @abstractmethod
    def visit_block_statement(self, node: "BlockStatement", o: Any = None):
        pass

    @abstractmethod
    def visit_variable_decl(self, node: "VariableDecl", o: Any = None):
        pass

    @abstractmethod
    def visit_variable(self, node: "Variable", o: Any = None):
        pass

    @abstractmethod
    def visit_assignment_statement(self, node: "AssignmentStatement", o: Any = None):
        pass

    @abstractmethod
    def visit_if_statement(self, node: "IfStatement", o: Any = None):
        pass

    @abstractmethod
    def visit_for_statement(self, node: "ForStatement", o: Any = None):
        pass

    @abstractmethod
    def visit_break_statement(self, node: "BreakStatement", o: Any = None):
        pass

    @abstractmethod
    def visit_continue_statement(self, node: "ContinueStatement", o: Any = None):
        pass

    @abstractmethod
    def visit_return_statement(self, node: "ReturnStatement", o: Any = None):
        pass

    @abstractmethod
    def visit_method_invocation_statement(
        self, node: "MethodInvocationStatement", o: Any = None
    ):
        pass

    # Left-hand side (LHS)
    @abstractmethod
    def visit_id_lhs(self, node: "IdLHS", o: Any = None):
        pass

    @abstractmethod
    def visit_postfix_lhs(self, node: "PostfixLHS", o: Any = None):
        pass

    # Expressions
    @abstractmethod
    def visit_binary_op(self, node: "BinaryOp", o: Any = None):
        pass

    @abstractmethod
    def visit_unary_op(self, node: "UnaryOp", o: Any = None):
        pass

    @abstractmethod
    def visit_postfix_expression(self, node: "PostfixExpression", o: Any = None):
        pass

    @abstractmethod
    def visit_method_call(self, node: "MethodCall", o: Any = None):
        pass

    @abstractmethod
    def visit_member_access(self, node: "MemberAccess", o: Any = None):
        pass

    @abstractmethod
    def visit_array_access(self, node: "ArrayAccess", o: Any = None):
        pass

    @abstractmethod
    def visit_object_creation(self, node: "ObjectCreation", o: Any = None):
        pass

    @abstractmethod
    def visit_static_method_invocation(
        self, node: "StaticMethodInvocation", o: Any = None
    ):
        pass

    @abstractmethod
    def visit_static_member_access(self, node: "StaticMemberAccess", o: Any = None):
        pass

    @abstractmethod
    def visit_method_invocation(self, node: "MethodInvocation", o: Any = None):
        pass

    @abstractmethod
    def visit_identifier(self, node: "Identifier", o: Any = None):
        pass

    @abstractmethod
    def visit_this_expression(self, node: "ThisExpression", o: Any = None):
        pass

    @abstractmethod
    def visit_parenthesized_expression(
        self, node: "ParenthesizedExpression", o: Any = None
    ):
        pass

    # Literals
    @abstractmethod
    def visit_int_literal(self, node: "IntLiteral", o: Any = None):
        pass

    @abstractmethod
    def visit_float_literal(self, node: "FloatLiteral", o: Any = None):
        pass

    @abstractmethod
    def visit_bool_literal(self, node: "BoolLiteral", o: Any = None):
        pass

    @abstractmethod
    def visit_string_literal(self, node: "StringLiteral", o: Any = None):
        pass

    @abstractmethod
    def visit_array_literal(self, node: "ArrayLiteral", o: Any = None):
        pass

    @abstractmethod
    def visit_nil_literal(self, node: "NilLiteral", o: Any = None):
        pass


class BaseVisitor(ASTVisitor):
    """Base visitor that provides default implementations for all visit methods.
    Subclasses can override only the methods they need to customize."""

    def visit_program(self, node: "Program", o: Any = None):
        for class_decl in node.class_decls:
            self.visit(class_decl, o)

    def visit_class_decl(self, node: "ClassDecl", o: Any = None):
        for member in node.members:
            self.visit(member, o)

    def visit_attribute_decl(self, node: "AttributeDecl", o: Any = None):
        self.visit(node.attr_type, o)
        for attr in node.attributes:
            self.visit(attr, o)

    def visit_attribute(self, node: "Attribute", o: Any = None):
        if node.init_value:
            self.visit(node.init_value, o)

    def visit_method_decl(self, node: "MethodDecl", o: Any = None):
        self.visit(node.return_type, o)
        for param in node.params:
            self.visit(param, o)
        self.visit(node.body, o)

    def visit_constructor_decl(self, node: "ConstructorDecl", o: Any = None):
        for param in node.params:
            self.visit(param, o)
        self.visit(node.body, o)

    def visit_destructor_decl(self, node: "DestructorDecl", o: Any = None):
        self.visit(node.body, o)

    def visit_parameter(self, node: "Parameter", o: Any = None):
        self.visit(node.param_type, o)

    def visit_primitive_type(self, node: "PrimitiveType", o: Any = None):
        pass

    def visit_array_type(self, node: "ArrayType", o: Any = None):
        self.visit(node.element_type, o)

    def visit_class_type(self, node: "ClassType", o: Any = None):
        pass

    def visit_reference_type(self, node: "ReferenceType", o: Any = None):
        self.visit(node.referenced_type, o)

    def visit_block_statement(self, node: "BlockStatement", o: Any = None):
        for var_decl in node.var_decls:
            self.visit(var_decl, o)
        for stmt in node.statements:
            self.visit(stmt, o)

    def visit_variable_decl(self, node: "VariableDecl", o: Any = None):
        self.visit(node.var_type, o)
        for var in node.variables:
            self.visit(var, o)

    def visit_variable(self, node: "Variable", o: Any = None):
        if node.init_value:
            self.visit(node.init_value, o)

    def visit_assignment_statement(self, node: "AssignmentStatement", o: Any = None):
        self.visit(node.lhs, o)
        self.visit(node.rhs, o)

    def visit_if_statement(self, node: "IfStatement", o: Any = None):
        self.visit(node.condition, o)
        self.visit(node.then_stmt, o)
        if node.else_stmt:
            self.visit(node.else_stmt, o)

    def visit_for_statement(self, node: "ForStatement", o: Any = None):
        self.visit(node.start_expr, o)
        self.visit(node.end_expr, o)
        self.visit(node.body, o)

    def visit_break_statement(self, node: "BreakStatement", o: Any = None):
        pass

    def visit_continue_statement(self, node: "ContinueStatement", o: Any = None):
        pass

    def visit_return_statement(self, node: "ReturnStatement", o: Any = None):
        self.visit(node.value, o)

    def visit_method_invocation_statement(
        self, node: "MethodInvocationStatement", o: Any = None
    ):
        self.visit(node.method_invocation, o)

    def visit_id_lhs(self, node: "IdLHS", o: Any = None):
        pass

    def visit_postfix_lhs(self, node: "PostfixLHS", o: Any = None):
        self.visit(node.postfix_expr, o)

    def visit_binary_op(self, node: "BinaryOp", o: Any = None):
        self.visit(node.left, o)
        self.visit(node.right, o)

    def visit_unary_op(self, node: "UnaryOp", o: Any = None):
        self.visit(node.operand, o)

    def visit_postfix_expression(self, node: "PostfixExpression", o: Any = None):
        self.visit(node.primary, o)
        for op in node.postfix_ops:
            self.visit(op, o)

    def visit_method_call(self, node: "MethodCall", o: Any = None):
        for arg in node.args:
            self.visit(arg, o)

    def visit_member_access(self, node: "MemberAccess", o: Any = None):
        pass

    def visit_array_access(self, node: "ArrayAccess", o: Any = None):
        self.visit(node.index, o)

    def visit_object_creation(self, node: "ObjectCreation", o: Any = None):
        for arg in node.args:
            self.visit(arg, o)

    # def visit_static_method_invocation(
    #     self, node: "StaticMethodInvocation", o: Any = None
    # ):
    #     for arg in node.args:
    #         self.visit(arg, o)
    #
    # def visit_static_member_access(self, node: "StaticMemberAccess", o: Any = None):
    #     pass
    #
    # def visit_method_invocation(self, node: "MethodInvocation", o: Any = None):
    #     self.visit(node.postfix_expr, o)

    def visit_identifier(self, node: "Identifier", o: Any = None):
        pass

    def visit_this_expression(self, node: "ThisExpression", o: Any = None):
        pass

    def visit_parenthesized_expression(
        self, node: "ParenthesizedExpression", o: Any = None
    ):
        self.visit(node.expr, o)

    def visit_int_literal(self, node: "IntLiteral", o: Any = None):
        pass

    def visit_float_literal(self, node: "FloatLiteral", o: Any = None):
        pass

    def visit_bool_literal(self, node: "BoolLiteral", o: Any = None):
        pass

    def visit_string_literal(self, node: "StringLiteral", o: Any = None):
        pass

    def visit_array_literal(self, node: "ArrayLiteral", o: Any = None):
        for elem in node.value:
            self.visit(elem, o)

    def visit_nil_literal(self, node: "NilLiteral", o: Any = None):
        pass
