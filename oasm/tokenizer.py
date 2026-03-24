from dataclasses import dataclass

from .meta import MetaData, File
from .patterns import *
from .exceptions import OasmSyntaxError
from .config import command_names, register_names, function_names


@dataclass
class Token:
    type: str
    raw_value: str
    meta: MetaData

    def __str__(self):
        return f'[{str(self.meta)}] {self.type}({repr(self.raw_value)})'

    def __repr__(self):
        return f'[{str(self.meta)}] {self.type}({repr(self.raw_value)})'


@dataclass
class Tokens:
    file: File
    tokens: list[Token]

    def __str__(self):
        return f'Expr({self.tokens})'

    def __getitem__(self, index):
        return self.tokens[index]

    def __len__(self):
        return len(self.tokens)

    def __iter__(self):
        return iter(self.tokens)


# @dataclass
# class Expr:
#     _tokens: list[Token]
#
#     def __str__(self):
#         return f'Expr({repr(self._tokens)})'
#
#     def __getitem__(self, index):
#         return self._tokens[index]
#
#     def __len__(self):
#         return len(self._tokens)


class Tokenizer:
    def __init__(self, file: File):
        self.file = file

        self.token_specification = [
            ('section', SECTION),
            ('label', LABEL),
            ('float', FLOAT),
            ('hex_int', HEX_INT),
            ('int', INT),
            ('string', STRING),
            ('char', CHAR),
            ('identifier', IDENTIFIER),
            ('l_paren', L_PAREN),
            ('r_paren', R_PAREN),
            ('l_bracket', L_BRACKET),
            ('r_bracket', R_BRACKET),
            ('op', OP),
            ('assign', ASSIGN),
            ('comma', COMMA),
            ('newline', NEWLINE),
            ('skip', SKIP),
            ('unclosed_string', UNCLOSED_STRING),
            ('mismatch', MISMATCH),
        ]

        self._tokens = []
        # self._exprs = []
        #
        # self._status = {
        #     'tokens': False,
        #     'exprs': False,
        # }

    # @property
    # def tokens(self) -> list[Token]:
    #     return self._tokens
    #
    # @property
    # def exprs(self) -> list[Expr]:
    #     return self._exprs
    #
    # @property
    # def status(self) -> bool:
    #     return self._status['tokens'] and self._status['exprs']

    def work(self):
        self.tokenize()
        return Tokens(self.file, self._tokens)

    def tokenize(self):
        # if self._status['tokens']:
        #     return

        master_pattern = '|'.join(
            f'(?P<{name}>{reg.pattern})' for name, reg in self.token_specification
        )
        master_re = re.compile(master_pattern)

        line = 1
        line_start = 0

        for mo in master_re.finditer(self.file.content):
            kind = mo.lastgroup
            if kind == 'skip': continue

            column = mo.start() - line_start + 1
            value = mo.group()
            meta = MetaData(self.file, line, column)

            match kind:
                case 'unclosed_string':
                    raise OasmSyntaxError(meta, f'string {repr(value)} is unclosed')
                case 'mismatch':
                    raise OasmSyntaxError(meta, f'{repr(value)} is unacceptable')
                case 'newline':
                    line += 1
                    line_start = mo.end()
                case 'identifier':
                    if value in function_names:
                        kind = 'function'
                    elif value.upper() in register_names:
                        kind = 'reg'
                    elif value.upper() in command_names:
                        kind = 'command'

            self._tokens.append(Token(kind, value, meta))

        # self._status['tokens'] = True

    # def build_expr(self):
    #     if self._status['exprs']:
    #         return
    #     if not self._status['tokens']:
    #         raise TokenizerError('You should call tokenize() first')
    #
    #     temp_tokens = []
    #
    #     for token in self._tokens:
    #         if token.type == 'newline':
    #             if temp_tokens:
    #                 self._exprs.append(Expr(temp_tokens))
    #                 temp_tokens = []
    #         else:
    #             temp_tokens.append(token)
    #
    #     self._status['exprs'] = True
