#!/usr/bin/env python3
"""
ChocoPy Parser Implementation  
Based on Section 4 of ChocoPy Language Manual v2.2
"""

from typing import List, Optional
from lexer import Token, TokenType, ChocoPyLexer
from ast_nodes import *

class ParseError(Exception):
    def __init__(self, message: str, token: Optional[Token] = None):
        self.message = message
        self.token = token
        if token:
            super().__init__(f"Parse error at line {token.line}, column {token.column}: {message}")
        else:
            super().__init__(f"Parse error: {message}")

class ChocoPyParser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.current_token = tokens[0] if tokens else None
    
    def parse(self) -> Program:
        try:
            return self._parse_program()
        except ParseError as e:
            print(f"Parse error: {e}")
            raise
        except Exception as e:
            print(f"Unexpected parser error: {e}")
            raise ParseError(f"Unexpected error: {e}", self.current_token)
    
    def _advance(self) -> Token:
        token = self.current_token
        if self.current < len(self.tokens) - 1:
            self.current += 1
            self.current_token = self.tokens[self.current]
        return token
    
    def _peek(self, offset: int = 1) -> Optional[Token]:
        pos = self.current + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None
    
    def _match(self, *token_types: TokenType) -> bool:
        if self.current_token and self.current_token.type in token_types:
            return True
        return False
    
    def _consume(self, token_type: TokenType, message: str = None) -> Token:
        if not self.current_token:
            raise ParseError(message or f"Expected {token_type.name} but reached end of file")
        
        if self.current_token.type == token_type:
            return self._advance()
        else:
            error_msg = message or f"Expected {token_type.name} but got {self.current_token.type.name}"
            raise ParseError(error_msg, self.current_token)
    
    def _consume_newlines(self):
        while self._match(TokenType.NEWLINE):
            self._advance()
    
    def _parse_program(self) -> Program:
        declarations = []
        statements = []
        
        self._consume_newlines()
        
        while (self.current_token and 
               self.current_token.type in {TokenType.CLASS, TokenType.DEF} or
               self._is_var_def()):
            
            if self._match(TokenType.CLASS):
                declarations.append(self._parse_class_def())
            elif self._match(TokenType.DEF):
                declarations.append(self._parse_func_def())
            elif self._is_var_def():
                declarations.append(self._parse_var_def())
            else:
                break
            
            self._consume_newlines()
        
        while (self.current_token and 
               self.current_token.type != TokenType.EOF):
            
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue
                
            statements.append(self._parse_statement())
            self._consume_newlines()
        
        return Program(declarations, statements)
    
    def _is_var_def(self) -> bool:
        if (self._match(TokenType.ID) and 
            self._peek() and self._peek().type == TokenType.COLON):
            return True
        return False
    
    def _parse_class_def(self) -> ClassDef:
        self._consume(TokenType.CLASS)
        name = self._consume(TokenType.ID).value
        self._consume(TokenType.LPAREN)
        superclass = self._consume(TokenType.ID).value
        self._consume(TokenType.RPAREN)
        self._consume(TokenType.COLON)
        self._consume(TokenType.NEWLINE)
        self._consume(TokenType.INDENT)
        
        declarations = self._parse_class_body()
        
        self._consume(TokenType.DEDENT)
        
        return ClassDef(name, superclass, declarations)
    
    def _parse_class_body(self) -> List[Declaration]:
        declarations = []
        
        if self._match(TokenType.PASS):
            self._advance()
            self._consume(TokenType.NEWLINE)
            return declarations
        
        while (self.current_token and 
               not self._match(TokenType.DEDENT)):
            
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue
            elif self._match(TokenType.DEF):
                declarations.append(self._parse_func_def())
            elif self._is_var_def():
                declarations.append(self._parse_var_def())
            else:
                raise ParseError("Expected variable or function definition in class body", 
                               self.current_token)
        
        return declarations
    
    def _parse_func_def(self) -> FuncDef:
        self._consume(TokenType.DEF)
        name = self._consume(TokenType.ID).value
        self._consume(TokenType.LPAREN)
        
        params = []
        if not self._match(TokenType.RPAREN):
            params.append(self._parse_typed_var())
            while self._match(TokenType.COMMA):
                self._advance()
                params.append(self._parse_typed_var())
        
        self._consume(TokenType.RPAREN)
        
        return_type = None
        if self._match(TokenType.ARROW):
            self._advance()
            return_type = self._parse_type()
        
        self._consume(TokenType.COLON)
        self._consume(TokenType.NEWLINE)
        self._consume(TokenType.INDENT)
        
        declarations, statements = self._parse_func_body()
        
        self._consume(TokenType.DEDENT)
        
        return FuncDef(name, params, return_type, declarations, statements)
    
    def _parse_func_body(self) -> tuple[List[Declaration], List[Statement]]:
        declarations = []
        statements = []
        
        while (self.current_token and 
               not self._match(TokenType.DEDENT)):
            
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue
            elif self._match(TokenType.GLOBAL):
                declarations.append(self._parse_global_decl())
            elif self._match(TokenType.NONLOCAL):
                declarations.append(self._parse_nonlocal_decl())
            elif self._match(TokenType.DEF):
                declarations.append(self._parse_func_def())
            elif self._is_var_def():
                declarations.append(self._parse_var_def())
            else:
                break
        
        while (self.current_token and 
               not self._match(TokenType.DEDENT)):
            
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue
                
            statements.append(self._parse_statement())
        
        if not statements:
            raise ParseError("Function body must contain at least one statement", 
                           self.current_token)
        
        return declarations, statements
    
    def _parse_global_decl(self) -> GlobalDecl:
        self._consume(TokenType.GLOBAL)
        identifier = self._consume(TokenType.ID).value
        self._consume(TokenType.NEWLINE)
        return GlobalDecl(identifier)
    
    def _parse_nonlocal_decl(self) -> NonlocalDecl:
        self._consume(TokenType.NONLOCAL)
        identifier = self._consume(TokenType.ID).value
        self._consume(TokenType.NEWLINE)
        return NonlocalDecl(identifier)
    
    def _parse_var_def(self) -> VarDef:
        var = self._parse_typed_var()
        self._consume(TokenType.ASSIGN)
        value = self._parse_literal()
        self._consume(TokenType.NEWLINE)
        return VarDef(var, value)
    
    def _parse_typed_var(self) -> TypedVar:
        identifier = self._consume(TokenType.ID).value
        self._consume(TokenType.COLON)
        type_annotation = self._parse_type()
        return TypedVar(identifier, type_annotation)
    
    def _parse_type(self) -> Type:
        if self._match(TokenType.ID, TokenType.IDSTRING):
            classname = self._advance().value
            return ClassType(classname)
        elif self._match(TokenType.LBRACKET):
            self._advance()
            element_type = self._parse_type()
            self._consume(TokenType.RBRACKET)
            return ListType(element_type)
        else:
            raise ParseError("Expected type annotation", self.current_token)
    
    def _parse_statement(self) -> Statement:
        if self._match(TokenType.IF):
            return self._parse_if_stmt()
        elif self._match(TokenType.WHILE):
            return self._parse_while_stmt()
        elif self._match(TokenType.FOR):
            return self._parse_for_stmt()
        else:
            stmt = self._parse_simple_stmt()
            self._consume(TokenType.NEWLINE)
            return stmt
    
    def _parse_simple_stmt(self) -> Statement:
        if self._match(TokenType.PASS):
            self._advance()
            return PassStmt()
        elif self._match(TokenType.RETURN):
            self._advance()
            value = None
            if not self._match(TokenType.NEWLINE):
                value = self._parse_expression()
            return ReturnStmt(value)
        else:
            return self._parse_assignment_or_expr()
    
    def _parse_assignment_or_expr(self) -> Statement:
        expr = self._parse_expression()
        
        if self._match(TokenType.ASSIGN):
            targets = [expr]
            
            while self._match(TokenType.ASSIGN):
                self._advance()
                if self._match(TokenType.ASSIGN):
                    targets.append(self._parse_expression())
                else:
                    value = self._parse_expression()
                    return AssignStmt(targets, value)
            
            value = self._parse_expression()
            return AssignStmt(targets, value)
        else:
            return ExprStmt(expr)
    
    def _parse_if_stmt(self) -> IfStmt:
        self._consume(TokenType.IF)
        condition = self._parse_expression()
        self._consume(TokenType.COLON)
        then_body = self._parse_block()
        
        elif_conditions = []
        elif_bodies = []
        else_body = None
        
        while self._match(TokenType.ELIF):
            self._advance()
            elif_condition = self._parse_expression()
            self._consume(TokenType.COLON)
            elif_body = self._parse_block()
            elif_conditions.append(elif_condition)
            elif_bodies.append(elif_body)
        
        if self._match(TokenType.ELSE):
            self._advance()
            self._consume(TokenType.COLON)
            else_body = self._parse_block()
        
        return IfStmt(condition, then_body, elif_conditions, elif_bodies, else_body)
    
    def _parse_while_stmt(self) -> WhileStmt:
        self._consume(TokenType.WHILE)
        condition = self._parse_expression()
        self._consume(TokenType.COLON)
        body = self._parse_block()
        return WhileStmt(condition, body)
    
    def _parse_for_stmt(self) -> ForStmt:
        self._consume(TokenType.FOR)
        identifier = self._consume(TokenType.ID).value
        self._consume(TokenType.IN)
        iterable = self._parse_expression()
        self._consume(TokenType.COLON)
        body = self._parse_block()
        return ForStmt(identifier, iterable, body)
    
    def _parse_block(self) -> List[Statement]:
        self._consume(TokenType.NEWLINE)
        self._consume(TokenType.INDENT)
        
        statements = []
        while not self._match(TokenType.DEDENT):
            if self._match(TokenType.NEWLINE):
                self._advance()
                continue
            statements.append(self._parse_statement())
        
        self._consume(TokenType.DEDENT)
        
        if not statements:
            raise ParseError("Block must contain at least one statement", self.current_token)
        
        return statements
    
    def _parse_expression(self) -> Expr:
        return self._parse_if_expr()
    
    def _parse_if_expr(self) -> Expr:
        expr = self._parse_or_expr()
        
        if self._match(TokenType.IF):
            self._advance()
            condition = self._parse_or_expr()
            self._consume(TokenType.ELSE, "Expected 'else' in conditional expression")
            else_expr = self._parse_if_expr()
            return IfExpr(condition, expr, else_expr)
        
        return expr
    
    def _parse_or_expr(self) -> Expr:
        left = self._parse_and_expr()
        
        while self._match(TokenType.OR):
            op = self._advance().value
            right = self._parse_and_expr()
            left = BinaryOp(left, op, right)
        
        return left
    
    def _parse_and_expr(self) -> Expr:
        left = self._parse_not_expr()
        
        while self._match(TokenType.AND):
            op = self._advance().value
            right = self._parse_not_expr()
            left = BinaryOp(left, op, right)
        
        return left
    
    def _parse_not_expr(self) -> Expr:
        if self._match(TokenType.NOT):
            op = self._advance().value
            operand = self._parse_not_expr()
            return UnaryOp(op, operand)
        
        return self._parse_comparison_expr()
    
    def _parse_comparison_expr(self) -> Expr:
        left = self._parse_additive_expr()
        
        if self._match(TokenType.EQUAL, TokenType.NOT_EQUAL, TokenType.LESS, 
                       TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL, 
                       TokenType.IS):
            op = self._advance().value
            right = self._parse_additive_expr()
            return BinaryOp(left, op, right)
        
        return left
    
    def _parse_additive_expr(self) -> Expr:
        left = self._parse_multiplicative_expr()
        
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._parse_multiplicative_expr()
            left = BinaryOp(left, op, right)
        
        return left
    
    def _parse_multiplicative_expr(self) -> Expr:
        left = self._parse_unary_expr()
        
        while self._match(TokenType.MULTIPLY, TokenType.FLOOR_DIV, TokenType.MODULO):
            op = self._advance().value
            right = self._parse_unary_expr()
            left = BinaryOp(left, op, right)
        
        return left
    
    def _parse_unary_expr(self) -> Expr:
        if self._match(TokenType.MINUS):
            op = self._advance().value
            operand = self._parse_unary_expr()
            return UnaryOp(op, operand)
        
        return self._parse_postfix_expr()
    
    def _parse_postfix_expr(self) -> Expr:
        expr = self._parse_primary_expr()
        
        while True:
            if self._match(TokenType.DOT):
                self._advance()
                member = self._consume(TokenType.ID).value
                
                if self._match(TokenType.LPAREN):
                    self._advance()
                    args = self._parse_argument_list()
                    self._consume(TokenType.RPAREN)
                    member_expr = MemberExpr(expr, member)
                    expr = MethodCallExpr(member_expr, args)
                else:
                    expr = MemberExpr(expr, member)
                    
            elif self._match(TokenType.LBRACKET):
                self._advance()
                index = self._parse_expression()
                self._consume(TokenType.RBRACKET)
                expr = IndexExpr(expr, index)
                
            elif self._match(TokenType.LPAREN):
                self._advance()
                args = self._parse_argument_list()
                self._consume(TokenType.RPAREN)
                expr = CallExpr(expr, args)
                
            else:
                break
        
        return expr
    
    def _parse_primary_expr(self) -> Expr:
        if self._match(TokenType.ID):
            return Identifier(self._advance().value)
        
        elif self._match(TokenType.INTEGER, TokenType.STRING, TokenType.IDSTRING,
                         TokenType.TRUE, TokenType.FALSE, TokenType.NONE):
            return self._parse_literal()
        
        elif self._match(TokenType.LPAREN):
            self._advance()
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN)
            return expr
        
        elif self._match(TokenType.LBRACKET):
            return self._parse_list_expr()
        
        else:
            raise ParseError(f"Unexpected token in expression: {self.current_token.type.name}", 
                           self.current_token)
    
    def _parse_list_expr(self) -> ListExpr:
        self._consume(TokenType.LBRACKET)
        
        elements = []
        if not self._match(TokenType.RBRACKET):
            elements.append(self._parse_expression())
            while self._match(TokenType.COMMA):
                self._advance()
                elements.append(self._parse_expression())
        
        self._consume(TokenType.RBRACKET)
        return ListExpr(elements)
    
    def _parse_argument_list(self) -> List[Expr]:
        args = []
        if not self._match(TokenType.RPAREN):
            args.append(self._parse_expression())
            while self._match(TokenType.COMMA):
                self._advance()
                args.append(self._parse_expression())
        
        return args
    
    def _parse_literal(self) -> Literal:
        if self._match(TokenType.INTEGER):
            value = int(self._advance().value)
            return IntegerLiteral(value)
        elif self._match(TokenType.TRUE):
            self._advance()
            return BooleanLiteral(True)
        elif self._match(TokenType.FALSE):
            self._advance()
            return BooleanLiteral(False)
        elif self._match(TokenType.NONE):
            self._advance()
            return NoneLiteral()
        elif self._match(TokenType.STRING, TokenType.IDSTRING):
            value = self._advance().value
            return StringLiteral(value)
        else:
            raise ParseError("Expected literal", self.current_token)
