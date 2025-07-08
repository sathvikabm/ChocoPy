"""
AST Node Definitions for ChocoPy
Based on Section 4 of ChocoPy Language Manual v2.2
"""

from typing import List, Optional, Union, Any
from dataclasses import dataclass, field
from abc import ABC

class ASTNode(ABC):
    """Base class for all AST nodes"""
    pass

# === PROGRAM STRUCTURE ===

@dataclass
class Program(ASTNode):
    """Top-level program: declarations + statements"""
    declarations: List['Declaration']
    statements: List['Statement']
    
    def __str__(self):
        return f"Program({len(self.declarations)} decls, {len(self.statements)} stmts)"

@dataclass
class Declaration(ASTNode):
    """Base class for all declarations"""
    pass

@dataclass
class VarDef(Declaration):
    """Variable definition: x: int = 5"""
    var: 'TypedVar'
    value: 'Literal'
    
    def __str__(self):
        return f"VarDef({self.var} = {self.value})"

@dataclass
class FuncDef(Declaration):
    """Function definition"""
    name: str
    params: List['TypedVar']
    return_type: Optional['Type']
    declarations: List[Declaration]
    statements: List['Statement']
    
    def __str__(self):
        return f"FuncDef({self.name}, {len(self.params)} params)"

@dataclass
class ClassDef(Declaration):
    """Class definition"""
    name: str
    superclass: str
    declarations: List[Declaration]
    
    def __str__(self):
        return f"ClassDef({self.name} : {self.superclass})"

# === TYPES ===

@dataclass
class Type(ASTNode):
    """Base class for type annotations"""
    pass

@dataclass
class ClassType(Type):
    """Class type: int, str, MyClass"""
    classname: str
    
    def __str__(self):
        return self.classname

@dataclass
class ListType(Type):
    """List type: [int], [str]"""
    element_type: Type
    
    def __str__(self):
        return f"[{self.element_type}]"

@dataclass
class TypedVar(ASTNode):
    """Typed variable: x: int"""
    identifier: str
    type: Type
    
    def __str__(self):
        return f"{self.identifier}: {self.type}"

# === STATEMENTS ===

@dataclass
class Statement(ASTNode):
    """Base class for all statements"""
    pass

@dataclass
class ExprStmt(Statement):
    """Expression statement"""
    expr: 'Expr'
    
    def __str__(self):
        return f"ExprStmt({self.expr})"

@dataclass
class AssignStmt(Statement):
    """Assignment: x = 5 or x = y = z = 5"""
    targets: List['Expr']
    value: 'Expr'
    
    def __str__(self):
        return f"AssignStmt({self.targets} = {self.value})"

@dataclass
class IfStmt(Statement):
    """If statement with optional elif/else"""
    condition: 'Expr'
    then_body: List[Statement]
    elif_conditions: List['Expr'] = field(default_factory=list)
    elif_bodies: List[List[Statement]] = field(default_factory=list)
    else_body: Optional[List[Statement]] = None
    
    def __str__(self):
        return f"IfStmt(condition={self.condition})"

@dataclass
class WhileStmt(Statement):
    """While loop"""
    condition: 'Expr'
    body: List[Statement]
    
    def __str__(self):
        return f"WhileStmt({self.condition})"

@dataclass
class ForStmt(Statement):
    """For loop: for x in expr:"""
    identifier: str
    iterable: 'Expr'
    body: List[Statement]
    
    def __str__(self):
        return f"ForStmt({self.identifier} in {self.iterable})"

@dataclass
class ReturnStmt(Statement):
    """Return statement"""
    value: Optional['Expr'] = None
    
    def __str__(self):
        return f"ReturnStmt({self.value})"

@dataclass
class PassStmt(Statement):
    """Pass statement"""
    
    def __str__(self):
        return "PassStmt()"

@dataclass
class GlobalDecl(Statement):
    """Global declaration"""
    identifier: str
    
    def __str__(self):
        return f"GlobalDecl({self.identifier})"

@dataclass
class NonlocalDecl(Statement):
    """Nonlocal declaration"""
    identifier: str
    
    def __str__(self):
        return f"NonlocalDecl({self.identifier})"

# === EXPRESSIONS ===

@dataclass
class Expr(ASTNode):
    """Base class for all expressions"""
    # Type annotation will be added by type checker
    # Put this field last to avoid inheritance issues
    inferred_type: Optional['Type'] = field(default=None, init=False)

@dataclass
class Literal(Expr):
    """Base class for literals"""
    pass

@dataclass
class IntegerLiteral(Literal):
    value: int
    
    def __str__(self):
        return str(self.value)

@dataclass
class BooleanLiteral(Literal):
    value: bool
    
    def __str__(self):
        return str(self.value)

@dataclass
class StringLiteral(Literal):
    value: str
    
    def __str__(self):
        return f'"{self.value}"'

@dataclass
class NoneLiteral(Literal):
    
    def __str__(self):
        return "None"

@dataclass
class Identifier(Expr):
    """Variable reference"""
    name: str
    
    def __str__(self):
        return self.name

@dataclass
class BinaryOp(Expr):
    """Binary operation: left op right"""
    left: 'Expr'
    operator: str
    right: 'Expr'
    
    def __str__(self):
        return f"({self.left} {self.operator} {self.right})"

@dataclass
class UnaryOp(Expr):
    """Unary operation: op operand"""
    operator: str
    operand: 'Expr'
    
    def __str__(self):
        return f"({self.operator} {self.operand})"

@dataclass
class IfExpr(Expr):
    """Conditional expression: expr1 if condition else expr2"""
    condition: 'Expr'
    then_expr: 'Expr'
    else_expr: 'Expr'
    
    def __str__(self):
        return f"({self.then_expr} if {self.condition} else {self.else_expr})"

@dataclass
class ListExpr(Expr):
    """List literal: [1, 2, 3]"""
    elements: List['Expr']
    
    def __str__(self):
        return f"[{', '.join(str(e) for e in self.elements)}]"

@dataclass
class IndexExpr(Expr):
    """Index access: expr[index]"""
    list_expr: 'Expr'
    index: 'Expr'
    
    def __str__(self):
        return f"{self.list_expr}[{self.index}]"

@dataclass
class MemberExpr(Expr):
    """Member access: expr.member"""
    object: 'Expr'
    member: str
    
    def __str__(self):
        return f"{self.object}.{self.member}"

@dataclass
class MethodCallExpr(Expr):
    """Method call: obj.method(args)"""
    method: 'MemberExpr'
    args: List['Expr']
    
    def __str__(self):
        args_str = ', '.join(str(arg) for arg in self.args)
        return f"{self.method}({args_str})"

@dataclass
class CallExpr(Expr):
    """Function call: func(args)"""
    function: 'Expr'
    args: List['Expr']
    
    def __str__(self):
        args_str = ', '.join(str(arg) for arg in self.args)
        return f"{self.function}({args_str})"