from dataclasses import dataclass
from .tokenizer import Token
from .exceptions import OasmValueError


def get_value(token: Token):
    match token.type:
        case 'int':
            return int(token.raw_value)
        case 'hex_int':
            return int(token.raw_value, 16)
        case 'float':
            return float(token.raw_value)
        case 'char':
            chr = bytes(token.raw_value.strip("'"), 'utf-8').decode('unicode_escape')
            if len(chr) > 1:
                raise OasmValueError(token.meta, 'Char must be a single character')
            return ord(chr)
        case 'string':
            return bytes(token.raw_value.strip('"'), 'utf-8').decode('unicode_escape')
        case _:
            raise OasmValueError('Expected number or char')


class ASTNode:
    pass


class NumberNode(ASTNode):
    def __init__(self, token):
        self.token = token

    @property
    def value(self):
        return get_value(self.token)

    def __str__(self):
        return f'NumberNode({self.token.raw_value})'

    def __repr__(self):
        return f'NumberNode({self.token.raw_value})'


class StringNode(ASTNode):
    def __init__(self, token):
        self.token = token

    @property
    def value(self):
        return get_value(self.token)

    def __str__(self):
        return f'StringNode({self.token.raw_value})'

    def __repr__(self):
        return f'StringNode({self.token.raw_value})'


class BinOpNode(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __str__(self):
        return f'BinOpNode({self.left}, {self.op}, {self.right})'

    def __repr__(self):
        return f'BinOpNode({self.left}, {self.op}, {self.right})'


class UnaryOpNode(ASTNode):
    def __init__(self, op, right):
        self.op = op
        self.right = right

    def __str__(self):
        return f'UnaryOpNode({self.op}, {self.right})'

    def __repr__(self):
        return f'UnaryOpNode({self.op}, {self.right})'


class IdentifierNode(ASTNode):
    def __init__(self, token):
        self.token = token
        self.name = token.raw_value

    def __str__(self):
        return f'IdentifierNode({self.token})'

    def  __repr__(self):
        return f'IdentifierNode({self.token})'


class IndexNode(ASTNode):
    def __init__(self, token, index):
        self.token = token
        self.name = token.raw_value
        self.index = index

    def __str__(self):
        return f'IndexNode({self.name}[{self.index}])'

    def  __repr__(self):
        return f'IndexNode({self.token})'

class ListNode(ASTNode):
    def __init__(self, elements):
        self.elements = elements

    def __repr__(self):
        return f'ListNode({self.elements})'

    def __iter__(self):
        return iter(self.elements)

    def __getitem__(self, item):
        return self.elements[item]


class LabelNode(ASTNode):
    def __init__(self, token):
        self.token = token
        self.name = token.raw_value.strip(':')

    def __str__(self):
        return f'LabelNode({self.name})'

    def __repr__(self):
        return f'LabelNode({self.name})'


class CommandNode(ASTNode):
    def __init__(self, mnemonic_token, args):
        self.token = mnemonic_token
        self.name = mnemonic_token.raw_value.upper()
        self.args = args

    def __str__(self):
        return f'CommandNode({self.name}, args={self.args})'

    def __repr__(self):
        return f'CommandNode({self.name}, args={self.args})'


class RegisterNode(ASTNode):
    def __init__(self, token):
        self.token = token
        self.name = token.raw_value

    @property
    def value(self):
        return self.name.upper()

    def __str__(self):
        return f'RegisterNode({self.name})'

    def __repr__(self):
        return f'RegisterNode({self.name})'


class FunctionNode(ASTNode):
    def __init__(self, token, args):
        self.token = token
        self.name = token.raw_value
        self.args = args

    def __str__(self):
        return f'FunctionNode({self.name}, args={self.args})'

    def __repr__(self):
        return f'FunctionNode({self.name}, {self.args})'
