from .ast_nodes import *
from .tokenizer import Tokens
from .exceptions import OasmSyntaxError, OasmNameError


class ASTBuilder:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = -1
        self.current_token = None
        self.eat()

    def check_eof(self):
        if self.current_token is not None:
            raise OasmSyntaxError(
                self.current_token.meta,
                f"Unexpected token: '{self.current_token.raw_value}'"
            )

    def eat(self):
        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def bin_op(self, func, op_values):
        left = func()
        while self.current_token is not None and self.current_token.raw_value in op_values:
            op = self.current_token
            self.eat()
            right = func()

            left = BinOpNode(left, op, right)
        return left

    def factor(self):
        token = self.current_token

        if token is None:
            raise RuntimeError('Expected token, got None')

        if token.type in ('int', 'hex_int', 'float', 'char',):
            self.eat()
            return NumberNode(token)
        elif token.type == 'string':
            self.eat()
            return StringNode(token)
        elif token.type == 'identifier':
            self.eat()
            node = IdentifierNode(token)

            if self.current_token is not None and self.current_token.raw_value == '[':
                self.eat()
                index_expr = self.expr()
                if self.current_token is None or self.current_token.raw_value != ']':
                    raise OasmSyntaxError(token.meta, "Expected ']' after array index")
                self.eat()

                return IndexNode(node.token, index_expr)

            return node
        elif token.type == 'reg':
            self.eat()
            return RegisterNode(token)
        elif token.type == 'label':
            self.eat()
            return LabelNode(token)
        elif token.type == 'function':
            self.eat()
            if self.current_token.type != 'l_paren':
                raise OasmSyntaxError(
                    self.current_token.meta,
                    f'"(" expected, got f{self.current_token.raw_value} instead'
                )
            self.eat()
            args = self.parse_list('r_paren')
            if (val := self.current_token.raw_value) != ')' or self.current_token is None:
                raise OasmSyntaxError(token.meta, f"Expected ')', got {val} instead")

            self.eat()
            self.check_eof()
            return FunctionNode(token, ListNode(args))
        elif token.type == 'l_bracket':
            self.eat()
            lst = self.parse_list('r_bracket')
            if (val := self.current_token.type) != 'r_bracket' or self.current_token is None:
                raise OasmSyntaxError(token.meta, f"Expected ']', got {val} instead")

            self.eat()
            return ListNode(lst)
        elif token.type == 'l_paren':
            self.eat()
            result = self.expr()
            if (val := self.current_token.type) != 'r_paren' or self.current_token is None:
                raise OasmSyntaxError(token.meta, f"Expected ')', got {val} instead")

            self.eat()
            return result
        elif token.raw_value in ('+', '-'):
            self.eat()
            right = self.factor()
            return UnaryOpNode(token, right)
        raise OasmSyntaxError(
            token.meta,
            f"Unexpected token: {token.raw_value}"
        )

    def pow(self):
        left = self.factor()

        if self.current_token is None or self.current_token.raw_value != '^':
            return left

        op = self.current_token
        self.eat()
        right = self.pow()

        return BinOpNode(left, op, right)

    def term(self):
        return self.bin_op(self.pow, ('*', '/'))

    def expr(self):
        return self.bin_op(self.term, ('+', '-'))

    def parse(self):
        if self.current_token is None:
            return None

        result = self.expr()

        if self.current_token is not None:
            raise OasmSyntaxError(self.current_token.meta, "Unexpected token after expression: {self.current_token}'")

        return result

    def parse_list(self, end_token_type):
        elements = []
        if self.current_token and self.current_token.type != end_token_type:
            elements.append(self.expr())
            while self.current_token and self.current_token.type == 'comma':
                self.eat()
                elements.append(self.expr())

        return elements

    def parse_command_args(self, end_token_type):
        elements = []
        if self.current_token and self.current_token.type != end_token_type:
            elements.append(self.expr())
            while self.current_token and self.current_token.type == 'comma':
                self.eat()
                elements.append(self.expr())

        self.check_eof()
        return elements


class Parser:
    def __init__(self, tokens: Tokens):
        self.tokens = tokens

        self.lines = []

        self.macros = {}
        self.consts = {}
        self.variables = {}
        self.labels = {}
        self.commands = []

        self.macro_section = []
        self.data_section = []
        self.code_section = []


    def work(self):
        self.split()
        self.sectionize()
        self.parse_macro()
        self.parse_data()
        self.parse_code()
        return self.macros, self.consts, self.variables, self.commands

    def split(self):
        temp_tokens = []

        for token in self.tokens:
            if token.type == 'newline':
                if temp_tokens:
                    self.lines.append(temp_tokens)
                    temp_tokens = []
            else:
                temp_tokens.append(token)

        if temp_tokens:
            self.lines.append(temp_tokens)
            temp_tokens = []


    def sectionize(self):
        section = None
        for line in self.lines:
            command = line[0]
            if command.type == 'section':
                section = command.raw_value.split()[1]
            elif section is None:
                self.macro_section.append(line)
            elif section == '.data':
                self.data_section.append(line)
            elif section == '.code':
                self.code_section.append(line)
            else:
                raise OasmSyntaxError(command.meta, 'Undefined section')

    def parse_macro(self):
        ...

    def parse_data(self):
        for expr in self.data_section:
            if len(expr) < 3:
                raise OasmSyntaxError(expr[0].meta, 'Invalid syntax: expected <identifier> = <value>')
            if (var_token := expr[0]).type != 'identifier':
                raise OasmSyntaxError(
                    var_token.meta,
                    'Invalid syntax: expected identifier, got {var_token.type} instead',
                )
            elif var_token.raw_value in self.macros:
                raise OasmNameError(
                    var_token.meta,
                    'This name is taken by macro',
                )
            elif var_token.raw_value in self.consts:
                raise OasmNameError(
                    var_token.meta,
                    'This name is taken by const',
                )
            elif var_token.raw_value in self.variables:
                raise OasmNameError(
                    var_token.meta,
                    'Variable with this name already exists',
                )

            if expr[1].type != 'assign':
                raise OasmSyntaxError(
                    expr[1].meta,
                    'Invalid syntax for data section. Did you mean "="?',
                )
            val_tokens = expr[2:]

            ast_builder = ASTBuilder(val_tokens)
            ast = ast_builder.parse()

            self.variables[var_token.raw_value] = {
                'ast': ast,
                'value': None,
                'type': None,
                'size': None,
                'bytes': None
            }

    def parse_code(self):
        for expr in self.code_section:
            if (key_token := expr[0]).type == 'label':
                if len(expr) > 1:
                    raise OasmSyntaxError(
                        key_token.meta,
                        f'Invalid syntax: There should be nothing after the label',
                    )
                self.commands.append(LabelNode(key_token))
                continue
            elif (key_token := expr[0]).type != 'command':
                raise OasmSyntaxError(
                    key_token.meta,
                    f'Invalid syntax: expected command, got {key_token.type} instead',
                )
            arg_tokens = expr[1:]
            if not arg_tokens:
                self.commands.append(CommandNode(key_token, []))
                continue
            self.commands.append(CommandNode(key_token, ASTBuilder(arg_tokens).parse_command_args(None)))
