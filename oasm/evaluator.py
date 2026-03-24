from .exceptions import *
from .ast_nodes import *
from .config import commands, command_aliases, functions


class Ref:
    pass


@dataclass
class LabelRef(Ref):
    token: Token
    name: str


@dataclass
class DataRef(Ref):
    token: Token
    name: str

    def __add__(self, other: int):
        return IndexRef(self.token, self.name, other)


@dataclass
class IndexRef(Ref):
    token: Token
    name: str
    index: int


@dataclass
class RegisterRef(Ref):
    token: Token
    name: str


@dataclass
class FunctionRef(Ref):
    token: Token
    name: str
    args: list


class Interpreter:
    def __init__(self, context):
        self.context = context

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.no_visit_method)
        return visitor(node)

    def visit_NumberNode(self, node):
        return node.value

    def visit_BinOpNode(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op.raw_value

        match op:
            case '+':
                return left + right
            case '-':
                return left - right
            case '*':
                return left * right
            case '/':
                if right == 0:
                    raise Exception(f'{left} / {right} is incorrect: division by zero!')
                return left / right
            case _:
                raise Exception(f'Unexpected operator: {op}')

    def visit_UnaryOpNode(self, node):
        right = self.visit(node.right)
        match node.op.raw_value:
            case '+':
                return right
            case '-':
                return -right
            case _:
                raise Exception(f'Unexpected operator: {node.op}')

    def visit_IdentifierNode(self, node):
        if node.name in (consts := self.context.consts):
            return consts[node.name]
        if node.name in (vars := self.context.variables):
            return DataRef(node.token, node.name)
        raise OasmNameError(
            node.token.meta,
            f'Undefined symbol: {node.name}'
        )

    def visit_IndexNode(self, node):
        if node.name in (vars := self.context.variables):
            return IndexRef(node.token, node.name, self.visit(node.index))

        raise OasmNameError(
            node.token.meta,
            f'Undefined symbol: {node.name}'
        )

    def visit_FunctionNode(self, node):
        if node.name not in functions:
            raise OasmNameError(node.token, f'Function {node.name} does not exist')
        args = [self.visit(arg) for arg in node.args]

        arg_types = []
        for arg in args:
            if isinstance(arg, RegisterRef):
                arg_types.append('reg')
            elif isinstance(arg, int) or isinstance(arg, float):
                arg_types.append('i64')
            elif isinstance(arg, DataRef):
                arg_types.append('data')
            elif isinstance(arg, LabelRef):
                arg_types.append('label')
            elif isinstance(arg, FunctionRef):
                arg_types.append(functions[arg.name]['returns'])
            else:
                raise RuntimeError(f'Unexpected type: {type(arg)} in {node}')

        if functions[node.name]['args'] == arg_types:
            return FunctionRef(node.token, node.name, args)

        raise OasmTypeError(
            node.token.meta,
            f'{node.name} expected {args}, got {arg_types}'
        )

        # match node.name:
        #     case 'sizeof':
        #         args = [self.visit(arg) for arg in node.args]
        #         if len(args) > 1:
        #             raise OasmTypeError(node.token.meta, f'{node.name} expected 1 argument, got {len(args)}')
        #         arg = args[0]
        #
        #         var_name = arg.name
        #         if var_name not in self.context.variables:
        #             raise OasmNameError(node.token.meta, f'Variable {var_name} not found')
        #
        #         var = self.context.variables[var_name]
        #         return var['size']
        #     case _:
        #         raise OasmNameError(node.token.meta, 'Function with this name does not exist')

    def visit_ListNode(self, node):
        return [self.visit(element) for element in node.elements]

    def visit_StringNode(self, node):
        return node.value

    def visit_LabelNode(self, node):
        return LabelRef(node.token, node.name)

    def visit_RegisterNode(self,node):
        return RegisterRef(node.token, node.name.upper())

    def visit_CommandNode(self, node):
        node.args = [self.visit(arg) for arg in node.args]
        arg_types = []
        for arg in node.args:
            if isinstance(arg, RegisterRef):
                arg_types.append('reg')
            elif isinstance(arg, int) or isinstance(arg, float):
                arg_types.append('i64')
            elif isinstance(arg, DataRef) or isinstance(arg, IndexRef):
                arg_types.append('data')
            elif isinstance(arg, LabelRef):
                arg_types.append('label')
            elif isinstance(arg, FunctionRef):
                arg_types.append(functions[arg.name]['returns'])
            else:
                raise RuntimeError(f'Unexpected type: {type(arg)} in {node}')

        if commands[node.name]['args'] == arg_types:
            return node

        if node.name not in command_aliases:
            raise OasmSyntaxError(node.token.meta, f'Invalid args for the command {node.name}: {', '.join(arg_types)}.\n'
                                                   f'Expected: {', '.join(commands[node.name]['args'])}')

        for alias in command_aliases[node.name]:
            if commands[alias]['args'] == arg_types:
                node.name = alias
                break
        else:
            raise OasmSyntaxError(node.token.meta, f'Invalid args for the command {node.name}: {', '.join(arg_types)}.\n'
                                                   f'Expected: {', '.join(commands[node.name]['args'])}')

        return node


    def no_visit_method(self, node):
        raise RuntimeError(f'No visit_{type(node).__name__}')
