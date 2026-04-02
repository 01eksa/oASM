from . import config
from .ast_nodes import *
from .exceptions import OasmSyntaxError, OasmNameError, OasmIndexError
from .evaluator import Ref, RegisterRef, LabelRef, DataRef, IndexRef
from .utils import to_bytes


class Translator:
    def __init__(self, macros, consts, variables, commands, labels):
        self.macros = macros
        self.consts = consts
        self.variables = variables
        self.commands = commands
        self.labels = labels

        self.data_chunks = []
        self.code_chunks = []

        self.code_section = b''
        self.data_section = b''

    def parse_ref(self, ref: Ref):
        if isinstance(ref, RegisterRef):
            reg = config.registers[ref.name]
            return reg.to_bytes(1)
        elif isinstance(ref, DataRef):
            if (var := ref.name) in self.variables:
                return self.variables[var]['offset'].to_bytes(8, byteorder=config.byteorder)
            else:
                raise OasmNameError(ref.token.meta, f'Unknown variable: {ref.name}')
        elif isinstance(ref, IndexRef):
            if (var := ref.name) in self.variables:
                if self.variables[var]['type'] == 'list':
                    offset = self.variables[var]['offset']+ref.index*8
                    if offset >= self.variables[var]['size']:
                        raise OasmIndexError(ref.token.meta, 'Index out of sange!')
                elif self.variables[var]['type'] == 'str':
                    offset = self.variables[var]['offset']+ref.index
                    if offset >= self.variables[var]['size']:
                        raise OasmIndexError(ref.token.meta, 'Index out of sange!')
                else:
                    raise OasmSyntaxError(ref.token.meta, f'You can use indexes only for arrays')
                return offset.to_bytes(8, byteorder=config.byteorder)
            else:
                raise OasmNameError(ref.token.meta, f'Unknown variable: {ref.name}')
        elif isinstance(ref, LabelRef):
            if (label := ref.name) in self.labels:
                return self.labels[label].to_bytes(8, byteorder=config.byteorder)
            else:
                raise OasmNameError(ref.token.meta, f'Unknown label: {ref.name}')
        else:
            raise TypeError(f'Unknown ref: {ref}')

    def gen_file(self):
        self.gen_data()
        self.gen_code()

        file = b''

        header = to_bytes(config.HEADER, config.byteorder)
        version = config.MAJOR.to_bytes(2, byteorder=config.byteorder) + config.MINOR.to_bytes(2, byteorder=config.byteorder)
        data_size = len(self.data_section).to_bytes(8, byteorder=config.byteorder)
        code_size = len(self.code_section).to_bytes(8, byteorder=config.byteorder)
        stack_size = config.stack_size.to_bytes(8, byteorder=config.byteorder)
        call_stack_size = config.call_stack_size.to_bytes(8, byteorder=config.byteorder)

        file += header + version + data_size + code_size + stack_size + call_stack_size + self.data_section + self.code_section
        return file

    def gen_data(self):
        for name in self.variables:
            var = self.variables[name]
            self.data_chunks.append(var['bytes'])

        self.data_section = b''.join(self.data_chunks)

    def gen_code(self):
        for command in self.commands:
            if isinstance(command, LabelNode):
                continue

            self.code_chunks.append(config.commands[command.name]['code'].to_bytes(1))

            if command.args:
                for arg in command.args:
                    if isinstance(arg, Ref):
                        self.code_chunks.append(self.parse_ref(arg))
                    elif isinstance(arg, int):
                        self.code_chunks.append(arg.to_bytes(8, byteorder=config.byteorder, signed=True))
                    elif isinstance(arg, float):
                        self.code_chunks.append(to_bytes(arg, config.byteorder))
                    else:
                        raise OasmSyntaxError(arg.token.meta, f'Unknown type: {arg}')

        self.code_section = b''.join(self.code_chunks)
