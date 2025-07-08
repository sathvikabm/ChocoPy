"""
ChocoPy Type Checker Implementation
Based on Section 5 of ChocoPy Language Manual v2.2
"""

from typing import Dict, List, Optional, Set, Union
from ast_nodes import *

class TypeCheckError(Exception):
    def __init__(self, message: str, node: Optional[ASTNode] = None):
        self.message = message
        self.node = node
        super().__init__(message)

class FunctionInfo:
    def __init__(self, name: str, params: List[Type], return_type: Type, func_def: FuncDef):
        self.name = name
        self.params = params
        self.return_type = return_type
        self.func_def = func_def

class SymbolTable:
    def __init__(self, parent: Optional['SymbolTable'] = None):
        self.parent = parent
        self.symbols: Dict[str, Type] = {}
        
    def define(self, name: str, type_: Type):
        self.symbols[name] = type_
        
    def lookup(self, name: str) -> Optional[Type]:
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent:
            return self.parent.lookup(name)
        return None
        
    def lookup_local(self, name: str) -> Optional[Type]:
        return self.symbols.get(name)

class ClassInfo:
    def __init__(self, name: str, superclass: Optional['ClassInfo'] = None):
        self.name = name
        self.superclass = superclass
        self.methods: Dict[str, FuncDef] = {}
        self.attributes: Dict[str, Type] = {}
        
    def get_method(self, name: str) -> Optional[FuncDef]:
        if name in self.methods:
            return self.methods[name]
        elif self.superclass:
            return self.superclass.get_method(name)
        return None
        
    def get_attribute(self, name: str) -> Optional[Type]:
        if name in self.attributes:
            return self.attributes[name]
        elif self.superclass:
            return self.superclass.get_attribute(name)
        return None

class ChocoPyTypeChecker:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.classes: Dict[str, ClassInfo] = {}
        self.functions: Dict[str, FunctionInfo] = {}  # Add function storage
        self.current_class: Optional[ClassInfo] = None
        self.current_function: Optional[FuncDef] = None
        self.return_type: Optional[Type] = None
        
        # Initialize built-in types
        self._init_builtins()
    
    def _init_builtins(self):
        """Initialize built-in types and functions"""
        # Built-in types
        self.classes["object"] = ClassInfo("object")
        self.classes["int"] = ClassInfo("int", self.classes["object"])
        self.classes["bool"] = ClassInfo("bool", self.classes["int"])
        self.classes["str"] = ClassInfo("str", self.classes["object"])
        
        # Built-in functions
        self.symbol_table.define("print", ClassType("function"))
        self.symbol_table.define("len", ClassType("function"))
        self.symbol_table.define("input", ClassType("function"))
    
    def check_program(self, program: Program) -> Program:
        """Type check the entire program"""
        try:
            # First pass: collect class and function declarations
            for decl in program.declarations:
                if isinstance(decl, ClassDef):
                    self._declare_class(decl)
                elif isinstance(decl, FuncDef):
                    self._declare_function(decl)
                elif isinstance(decl, VarDef):
                    self._check_var_def(decl)
            
            # Second pass: check class bodies
            for decl in program.declarations:
                if isinstance(decl, ClassDef):
                    self._check_class_def(decl)
                elif isinstance(decl, FuncDef):
                    self._check_func_def(decl)
            
            # Check statements
            for stmt in program.statements:
                self._check_statement(stmt)
                
            return program
            
        except TypeCheckError as e:
            print(f"Type check error: {e}")
            raise
    
    def _declare_class(self, class_def: ClassDef):
        """Declare a class in the type environment"""
        if class_def.name in self.classes:
            raise TypeCheckError(f"Class {class_def.name} already defined")
        
        superclass = None
        if class_def.superclass != "object":
            if class_def.superclass not in self.classes:
                raise TypeCheckError(f"Undefined superclass: {class_def.superclass}")
            superclass = self.classes[class_def.superclass]
        else:
            superclass = self.classes["object"]
        
        self.classes[class_def.name] = ClassInfo(class_def.name, superclass)
    
    def _declare_function(self, func_def: FuncDef):
        """Declare a function in the symbol table"""
        # Create function type
        func_type = ClassType("function")
        self.symbol_table.define(func_def.name, func_type)
        
        # Store function info for later lookup
        param_types = [self._check_type(param.type) for param in func_def.params]
        return_type = self._check_type(func_def.return_type) if func_def.return_type else ClassType("None")
        
        self.functions[func_def.name] = FunctionInfo(
            func_def.name, param_types, return_type, func_def
        )
    
    def _check_class_def(self, class_def: ClassDef):
        """Type check a class definition"""
        class_info = self.classes[class_def.name]
        self.current_class = class_info
        
        # Create new scope for class
        old_symbol_table = self.symbol_table
        self.symbol_table = SymbolTable(old_symbol_table)
        
        try:
            # Check class body
            for decl in class_def.declarations:
                if isinstance(decl, VarDef):
                    var_type = self._check_type(decl.var.type)
                    class_info.attributes[decl.var.identifier] = var_type
                    self._check_var_def(decl)
                elif isinstance(decl, FuncDef):
                    class_info.methods[decl.name] = decl
                    self._check_func_def(decl)
        finally:
            self.symbol_table = old_symbol_table
            self.current_class = None
    
    def _check_func_def(self, func_def: FuncDef):
        """Type check a function definition"""
        self.current_function = func_def
        
        # Check return type
        if func_def.return_type:
            self.return_type = self._check_type(func_def.return_type)
        else:
            self.return_type = ClassType("None")
        
        # Create new scope for function
        old_symbol_table = self.symbol_table
        self.symbol_table = SymbolTable(old_symbol_table)
        
        try:
            # Add parameters to scope
            for param in func_def.params:
                param_type = self._check_type(param.type)
                self.symbol_table.define(param.identifier, param_type)
            
            # Check declarations
            for decl in func_def.declarations:
                if isinstance(decl, VarDef):
                    self._check_var_def(decl)
                elif isinstance(decl, FuncDef):
                    self._check_func_def(decl)
            
            # Check statements
            for stmt in func_def.statements:
                self._check_statement(stmt)
                
        finally:
            self.symbol_table = old_symbol_table
            self.current_function = None
            self.return_type = None
    
    def _check_var_def(self, var_def: VarDef):
        """Type check a variable definition"""
        var_type = self._check_type(var_def.var.type)
        value_type = self._check_literal(var_def.value)
        
        if not self._is_assignable(value_type, var_type):
            raise TypeCheckError(f"Cannot assign {value_type} to variable of type {var_type}")
        
        self.symbol_table.define(var_def.var.identifier, var_type)
    
    def _check_statement(self, stmt: Statement):
        """Type check a statement"""
        if isinstance(stmt, ExprStmt):
            self._check_expression(stmt.expr)
        elif isinstance(stmt, AssignStmt):
            self._check_assign_stmt(stmt)
        elif isinstance(stmt, IfStmt):
            self._check_if_stmt(stmt)
        elif isinstance(stmt, WhileStmt):
            self._check_while_stmt(stmt)
        elif isinstance(stmt, ForStmt):
            self._check_for_stmt(stmt)
        elif isinstance(stmt, ReturnStmt):
            self._check_return_stmt(stmt)
        elif isinstance(stmt, PassStmt):
            pass  # Nothing to check
        else:
            raise TypeCheckError(f"Unknown statement type: {type(stmt)}")
    
    def _check_assign_stmt(self, stmt: AssignStmt):
        """Type check assignment statement"""
        value_type = self._check_expression(stmt.value)
        
        for target in stmt.targets:
            target_type = self._check_expression(target)
            if not self._is_assignable(value_type, target_type):
                raise TypeCheckError(f"Cannot assign {value_type} to {target_type}")
    
    def _check_if_stmt(self, stmt: IfStmt):
        """Type check if statement"""
        cond_type = self._check_expression(stmt.condition)
        if not self._is_subtype(cond_type, ClassType("bool")):
            raise TypeCheckError("If condition must be boolean")
        
        for stmt_body in stmt.then_body:
            self._check_statement(stmt_body)
        
        for elif_cond in stmt.elif_conditions:
            elif_cond_type = self._check_expression(elif_cond)
            if not self._is_subtype(elif_cond_type, ClassType("bool")):
                raise TypeCheckError("Elif condition must be boolean")
        
        for elif_body in stmt.elif_bodies:
            for stmt_body in elif_body:
                self._check_statement(stmt_body)
        
        if stmt.else_body:
            for stmt_body in stmt.else_body:
                self._check_statement(stmt_body)
    
    def _check_while_stmt(self, stmt: WhileStmt):
        """Type check while statement"""
        cond_type = self._check_expression(stmt.condition)
        if not self._is_subtype(cond_type, ClassType("bool")):
            raise TypeCheckError("While condition must be boolean")
        
        for stmt_body in stmt.body:
            self._check_statement(stmt_body)
    
    def _check_for_stmt(self, stmt: ForStmt):
        """Type check for statement"""
        iterable_type = self._check_expression(stmt.iterable)
        
        # Check if iterable is a list type
        if not isinstance(iterable_type, ListType):
            raise TypeCheckError("For loop requires list type")
        
        # Create new scope for loop variable
        old_symbol_table = self.symbol_table
        self.symbol_table = SymbolTable(old_symbol_table)
        
        try:
            # Add loop variable to scope
            self.symbol_table.define(stmt.identifier, iterable_type.element_type)
            
            for stmt_body in stmt.body:
                self._check_statement(stmt_body)
        finally:
            self.symbol_table = old_symbol_table
    
    def _check_return_stmt(self, stmt: ReturnStmt):
        """Type check return statement"""
        if stmt.value:
            return_type = self._check_expression(stmt.value)
        else:
            return_type = ClassType("None")
        
        if self.return_type and not self._is_assignable(return_type, self.return_type):
            raise TypeCheckError(f"Cannot return {return_type}, expected {self.return_type}")
    
    def _check_expression(self, expr: Expr) -> Type:
        """Type check an expression and return its type"""
        if isinstance(expr, Literal):
            expr_type = self._check_literal(expr)
        elif isinstance(expr, Identifier):
            expr_type = self._check_identifier(expr)
        elif isinstance(expr, BinaryOp):
            expr_type = self._check_binary_op(expr)
        elif isinstance(expr, UnaryOp):
            expr_type = self._check_unary_op(expr)
        elif isinstance(expr, IfExpr):
            expr_type = self._check_if_expr(expr)
        elif isinstance(expr, ListExpr):
            expr_type = self._check_list_expr(expr)
        elif isinstance(expr, IndexExpr):
            expr_type = self._check_index_expr(expr)
        elif isinstance(expr, MemberExpr):
            expr_type = self._check_member_expr(expr)
        elif isinstance(expr, MethodCallExpr):
            expr_type = self._check_method_call_expr(expr)
        elif isinstance(expr, CallExpr):
            expr_type = self._check_call_expr(expr)
        else:
            raise TypeCheckError(f"Unknown expression type: {type(expr)}")
        
        expr.inferred_type = expr_type
        return expr_type
    
    def _check_literal(self, literal: Literal) -> Type:
        """Type check a literal"""
        if isinstance(literal, IntegerLiteral):
            return ClassType("int")
        elif isinstance(literal, BooleanLiteral):
            return ClassType("bool")
        elif isinstance(literal, StringLiteral):
            return ClassType("str")
        elif isinstance(literal, NoneLiteral):
            return ClassType("None")
        else:
            raise TypeCheckError(f"Unknown literal type: {type(literal)}")
    
    def _check_identifier(self, identifier: Identifier) -> Type:
        """Type check an identifier"""
        var_type = self.symbol_table.lookup(identifier.name)
        if var_type is None:
            raise TypeCheckError(f"Undefined variable: {identifier.name}")
        return var_type
    
    def _check_binary_op(self, binary_op: BinaryOp) -> Type:
        """Type check a binary operation"""
        left_type = self._check_expression(binary_op.left)
        right_type = self._check_expression(binary_op.right)
        
        op = binary_op.operator
        
        # Arithmetic operations
        if op in ['+', '-', '*', '//', '%']:
            if (self._is_subtype(left_type, ClassType("int")) and 
                self._is_subtype(right_type, ClassType("int"))):
                return ClassType("int")
            else:
                raise TypeCheckError(f"Arithmetic operation requires int operands")
        
        # Comparison operations
        elif op in ['==', '!=']:
            return ClassType("bool")
        elif op in ['<', '<=', '>', '>=']:
            if (self._is_subtype(left_type, ClassType("int")) and 
                self._is_subtype(right_type, ClassType("int"))):
                return ClassType("bool")
            else:
                raise TypeCheckError(f"Comparison operation requires int operands")
        
        # Logical operations
        elif op in ['and', 'or']:
            if (self._is_subtype(left_type, ClassType("bool")) and 
                self._is_subtype(right_type, ClassType("bool"))):
                return ClassType("bool")
            else:
                raise TypeCheckError(f"Logical operation requires bool operands")
        
        # Identity comparison
        elif op == 'is':
            return ClassType("bool")
        
        else:
            raise TypeCheckError(f"Unknown binary operator: {op}")
    
    def _check_unary_op(self, unary_op: UnaryOp) -> Type:
        """Type check a unary operation"""
        operand_type = self._check_expression(unary_op.operand)
        
        if unary_op.operator == '-':
            if self._is_subtype(operand_type, ClassType("int")):
                return ClassType("int")
            else:
                raise TypeCheckError("Unary minus requires int operand")
        elif unary_op.operator == 'not':
            if self._is_subtype(operand_type, ClassType("bool")):
                return ClassType("bool")
            else:
                raise TypeCheckError("Not operator requires bool operand")
        else:
            raise TypeCheckError(f"Unknown unary operator: {unary_op.operator}")
    
    def _check_if_expr(self, if_expr: IfExpr) -> Type:
        """Type check conditional expression"""
        cond_type = self._check_expression(if_expr.condition)
        then_type = self._check_expression(if_expr.then_expr)
        else_type = self._check_expression(if_expr.else_expr)
        
        if not self._is_subtype(cond_type, ClassType("bool")):
            raise TypeCheckError("Conditional expression condition must be boolean")
        
        # Find common supertype
        if self._types_equal(then_type, else_type):
            return then_type
        elif self._is_subtype(then_type, else_type):
            return else_type
        elif self._is_subtype(else_type, then_type):
            return then_type
        else:
            return ClassType("object")  # Common supertype
    
    def _check_list_expr(self, list_expr: ListExpr) -> Type:
        """Type check list expression"""
        if not list_expr.elements:
            return ListType(ClassType("object"))  # Empty list
        
        # Check all elements have compatible types
        element_type = self._check_expression(list_expr.elements[0])
        for element in list_expr.elements[1:]:
            elem_type = self._check_expression(element)
            if not self._is_assignable(elem_type, element_type):
                element_type = ClassType("object")  # Fall back to object
        
        return ListType(element_type)
    
    def _check_index_expr(self, index_expr: IndexExpr) -> Type:
        """Type check index expression"""
        list_type = self._check_expression(index_expr.list_expr)
        index_type = self._check_expression(index_expr.index)
        
        if not isinstance(list_type, ListType):
            raise TypeCheckError("Index operation requires list type")
        
        if not self._is_subtype(index_type, ClassType("int")):
            raise TypeCheckError("List index must be int")
        
        return list_type.element_type
    
    def _check_member_expr(self, member_expr: MemberExpr) -> Type:
        """Type check member expression"""
        object_type = self._check_expression(member_expr.object)
        
        if isinstance(object_type, ClassType):
            class_info = self.classes.get(object_type.classname)
            if class_info:
                attr_type = class_info.get_attribute(member_expr.member)
                if attr_type:
                    return attr_type
        
        raise TypeCheckError(f"No attribute '{member_expr.member}' in type {object_type}")
    
    def _check_method_call_expr(self, method_call: MethodCallExpr) -> Type:
        """Type check method call expression"""
        # For now, assume method calls return object type
        # In a full implementation, we'd look up method signatures
        self._check_expression(method_call.method.object)
        for arg in method_call.args:
            self._check_expression(arg)
        return ClassType("object")
    
    def _check_call_expr(self, call_expr: CallExpr) -> Type:
        """Type check function call expression"""
        func_type = self._check_expression(call_expr.function)
        
        # Check arguments
        for arg in call_expr.args:
            self._check_expression(arg)
        
        # For built-in functions
        if isinstance(call_expr.function, Identifier):
            func_name = call_expr.function.name
            
            if func_name == "len":
                return ClassType("int")
            elif func_name == "print":
                return ClassType("None")
            elif func_name == "input":
                return ClassType("str")
            
            # For user-defined functions, look up their return type
            if func_name in self.functions:
                func_info = self.functions[func_name]
                return func_info.return_type
        
        # Default fallback
        return ClassType("object")
    
    def _check_type(self, type_: Type) -> Type:
        """Validate a type annotation"""
        if isinstance(type_, ClassType):
            if type_.classname not in self.classes:
                raise TypeCheckError(f"Undefined type: {type_.classname}")
            return type_
        elif isinstance(type_, ListType):
            element_type = self._check_type(type_.element_type)
            return ListType(element_type)
        else:
            raise TypeCheckError(f"Unknown type: {type_}")
    
    def _is_subtype(self, subtype: Type, supertype: Type) -> bool:
        """Check if subtype is a subtype of supertype"""
        if self._types_equal(subtype, supertype):
            return True
        
        if isinstance(subtype, ClassType) and isinstance(supertype, ClassType):
            sub_class = self.classes.get(subtype.classname)
            super_class = self.classes.get(supertype.classname)
            
            if sub_class and super_class:
                current = sub_class
                while current:
                    if current.name == super_class.name:
                        return True
                    current = current.superclass
        
        return False
    
    def _is_assignable(self, source: Type, target: Type) -> bool:
        """Check if source type can be assigned to target type"""
        return self._is_subtype(source, target)
    
    def _types_equal(self, type1: Type, type2: Type) -> bool:
        """Check if two types are equal"""
        if isinstance(type1, ClassType) and isinstance(type2, ClassType):
            return type1.classname == type2.classname
        elif isinstance(type1, ListType) and isinstance(type2, ListType):
            return self._types_equal(type1.element_type, type2.element_type)
        return False