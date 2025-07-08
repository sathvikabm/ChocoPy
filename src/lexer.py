"""
ChocoPy Lexer Implementation
Based on Section 3 of ChocoPy Language Manual v2.2
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class TokenType(Enum):
    # Literals
    INTEGER = "INTEGER"
    STRING = "STRING"
    IDSTRING = "IDSTRING"
    
    # Identifiers
    ID = "ID"
    
    # Keywords
    CLASS = "class"
    DEF = "def"
    IF = "if"
    ELIF = "elif"
    ELSE = "else"
    WHILE = "while"
    FOR = "for"
    IN = "in"
    RETURN = "return"
    PASS = "pass"
    AND = "and"
    OR = "or"
    NOT = "not"
    IS = "is"
    GLOBAL = "global"
    NONLOCAL = "nonlocal"
    TRUE = "True"
    FALSE = "False"
    NONE = "None"
    
    # Python keywords (for compatibility)
    AS = "as"
    ASSERT = "assert"
    ASYNC = "async"
    AWAIT = "await"
    BREAK = "break"
    CONTINUE = "continue"
    DEL = "del"
    EXCEPT = "except"
    FINALLY = "finally"
    FROM = "from"
    IMPORT = "import"
    LAMBDA = "lambda"
    RAISE = "raise"
    TRY = "try"
    WITH = "with"
    YIELD = "yield"
    
    # Operators
    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"
    FLOOR_DIV = "//"
    MODULO = "%"
    EQUAL = "=="
    NOT_EQUAL = "!="
    LESS = "<"
    LESS_EQUAL = "<="
    GREATER = ">"
    GREATER_EQUAL = ">="
    ASSIGN = "="
    
    # Delimiters
    LPAREN = "("
    RPAREN = ")"
    LBRACKET = "["
    RBRACKET = "]"
    COMMA = ","
    COLON = ":"
    DOT = "."
    ARROW = "->"
    
    # Structural
    NEWLINE = "NEWLINE"
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    EOF = "EOF"

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}', {self.line}:{self.column})"

class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Lexer error at line {line}, column {column}: {message}")

class ChocoPyLexer:
    KEYWORDS = {
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 
        'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 
        'except', 'finally', 'for', 'from', 'global', 'if', 'import', 
        'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 
        'return', 'try', 'while', 'with', 'yield'
    }
    
    MAX_INTEGER = 2147483647
    
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        self.indent_stack = [0]
        self.at_line_start = True
        
    def tokenize(self) -> List[Token]:
        try:
            while self.position < len(self.source):
                self._handle_line_start()
                
                if self.position >= len(self.source):
                    break
                    
                char = self._current_char()
                
                if char in ' \t':
                    self._skip_whitespace()
                    continue
                elif char == '#':
                    self._skip_comment()
                    continue
                elif char == '\n':
                    self._handle_newline()
                elif char.isdigit():
                    self._handle_number()
                elif char == '"':
                    self._handle_string()
                elif char.isalpha() or char == '_':
                    self._handle_identifier()
                else:
                    self._handle_operator()
            
            self._handle_end_of_file()
            self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
            return self.tokens
            
        except Exception as e:
            if isinstance(e, LexerError):
                raise
            else:
                raise LexerError(f"Unexpected error: {str(e)}", self.line, self.column)
    
    def _current_char(self) -> str:
        if self.position >= len(self.source):
            return '\0'
        return self.source[self.position]
    
    def _peek_char(self, offset: int = 1) -> str:
        pos = self.position + offset
        if pos >= len(self.source):
            return '\0'
        return self.source[pos]
    
    def _advance(self) -> str:
        if self.position < len(self.source):
            char = self.source[self.position]
            if char == '\n':
                self.line += 1
                self.column = 1
                self.at_line_start = True
            else:
                self.column += 1
                self.at_line_start = False
            self.position += 1
            return char
        return '\0'
    
    def _handle_line_start(self):
        if not self.at_line_start:
            return
            
        indent_level = 0
        start_pos = self.position
        
        while self.position < len(self.source):
            char = self.source[self.position]
            if char == ' ':
                indent_level += 1
                self.position += 1
                self.column += 1
            elif char == '\t':
                indent_level = (indent_level // 8 + 1) * 8
                self.position += 1
                self.column += 1
            else:
                break
        
        if (self.position >= len(self.source) or 
            self.source[self.position] == '\n' or 
            self.source[self.position] == '#'):
            self.at_line_start = False
            return
        
        current_indent = self.indent_stack[-1]
        
        if indent_level > current_indent:
            self.indent_stack.append(indent_level)
            self.tokens.append(Token(TokenType.INDENT, "", self.line, 1))
        elif indent_level < current_indent:
            while len(self.indent_stack) > 1 and self.indent_stack[-1] > indent_level:
                self.indent_stack.pop()
                self.tokens.append(Token(TokenType.DEDENT, "", self.line, 1))
            
            if self.indent_stack[-1] != indent_level:
                raise LexerError("Indentation error", self.line, 1)
        
        self.at_line_start = False
    
    def _skip_whitespace(self):
        while self.position < len(self.source) and self.source[self.position] in ' \t':
            self._advance()
    
    def _skip_comment(self):
        while self.position < len(self.source) and self.source[self.position] != '\n':
            self._advance()
    
    def _handle_newline(self):
        start_line, start_col = self.line, self.column
        self._advance()
        
        if (self.tokens and 
            self.tokens[-1].type not in {TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT}):
            self.tokens.append(Token(TokenType.NEWLINE, "\\n", start_line, start_col))
    
    def _handle_number(self):
        start_line, start_col = self.line, self.column
        start_pos = self.position
        
        while self.position < len(self.source) and self.source[self.position].isdigit():
            self._advance()
        
        value_str = self.source[start_pos:self.position]
        
        if len(value_str) > 1 and value_str[0] == '0':
            raise LexerError("Integer literals cannot have leading zeros", start_line, start_col)
        
        try:
            value = int(value_str)
            if value > self.MAX_INTEGER:
                raise LexerError(f"Integer literal too large (max {self.MAX_INTEGER})", 
                               start_line, start_col)
        except ValueError:
            raise LexerError("Invalid integer literal", start_line, start_col)
        
        self.tokens.append(Token(TokenType.INTEGER, value_str, start_line, start_col))
    
    def _handle_string(self):
        start_line, start_col = self.line, self.column
        self._advance()
        
        value = ""
        while self.position < len(self.source) and self.source[self.position] != '"':
            char = self.source[self.position]
            
            if char == '\\':
                self._advance()
                if self.position >= len(self.source):
                    raise LexerError("Unterminated string literal", start_line, start_col)
                
                escape_char = self.source[self.position]
                if escape_char == '"':
                    value += '"'
                elif escape_char == 'n':
                    value += '\n'
                elif escape_char == 't':
                    value += '\t'
                elif escape_char == '\\':
                    value += '\\'
                else:
                    raise LexerError(f"Invalid escape sequence '\\{escape_char}'", 
                                   self.line, self.column)
                self._advance()
            else:
                if ord(char) < 32 or ord(char) > 126:
                    raise LexerError(f"Invalid character in string (code {ord(char)})", 
                                   self.line, self.column)
                value += char
                self._advance()
        
        if self.position >= len(self.source):
            raise LexerError("Unterminated string literal", start_line, start_col)
        
        self._advance()
        
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value):
            token_type = TokenType.IDSTRING
        else:
            token_type = TokenType.STRING
        
        self.tokens.append(Token(token_type, value, start_line, start_col))
    
    def _handle_identifier(self):
        start_line, start_col = self.line, self.column
        start_pos = self.position
        
        while (self.position < len(self.source) and 
               (self.source[self.position].isalnum() or self.source[self.position] == '_')):
            self._advance()
        
        value = self.source[start_pos:self.position]
        
        if value in self.KEYWORDS:
            token_type = getattr(TokenType, value.upper(), TokenType.ID)
            self.tokens.append(Token(token_type, value, start_line, start_col))
        else:
            self.tokens.append(Token(TokenType.ID, value, start_line, start_col))
    
    def _handle_operator(self):
        start_line, start_col = self.line, self.column
        char = self._current_char()
        next_char = self._peek_char()
        
        two_char_ops = {
            '==': TokenType.EQUAL,
            '!=': TokenType.NOT_EQUAL,
            '<=': TokenType.LESS_EQUAL,
            '>=': TokenType.GREATER_EQUAL,
            '//': TokenType.FLOOR_DIV,
            '->': TokenType.ARROW,
        }
        
        two_char = char + next_char
        if two_char in two_char_ops:
            self.tokens.append(Token(two_char_ops[two_char], two_char, start_line, start_col))
            self._advance()
            self._advance()
            return
        
        single_char_ops = {
            '+': TokenType.PLUS, '-': TokenType.MINUS, '*': TokenType.MULTIPLY,
            '%': TokenType.MODULO, '=': TokenType.ASSIGN, '<': TokenType.LESS,
            '>': TokenType.GREATER, '(': TokenType.LPAREN, ')': TokenType.RPAREN,
            '[': TokenType.LBRACKET, ']': TokenType.RBRACKET, ',': TokenType.COMMA,
            ':': TokenType.COLON, '.': TokenType.DOT,
        }
        
        if char in single_char_ops:
            self.tokens.append(Token(single_char_ops[char], char, start_line, start_col))
            self._advance()
        else:
            raise LexerError(f"Unexpected character '{char}'", start_line, start_col)
    
    def _handle_end_of_file(self):
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, "", self.line, self.column))
