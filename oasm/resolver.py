import struct

from . import config
from .ast_nodes import LabelNode
from .evaluator import Interpreter
from .utils import to_bytes


class Resolver:
    def __init__(self, macros, consts, variables, commands):
        self.macros = macros
        self.consts = consts
        self.variables = variables
        self.commands = commands
        self.labels = {}
        self.interpreter = Interpreter(self)

    def work(self):
        self.solve_data()
        self.solve_commands()
        return self.macros, self.consts, self.variables, self.commands, self.labels

    def solve_data(self):
        offset = 0
        for name in self.variables:
            value = self.interpreter.visit(self.variables[name]['ast'])
            if isinstance(value, str):
                byte_value = value.encode('utf-8')
                size = len(byte_value)
                var_type = 'str'
            elif isinstance(value, int):
                byte_value = to_bytes(value, byteorder=config.byteorder)
                size = 8
                var_type = 'i64'
            elif isinstance(value, float):
                byte_value = struct.pack('<d', value)
                size = 8
                var_type = 'f64'
            elif isinstance(value, list):
                byte_value = to_bytes(value, byteorder=config.byteorder)
                size = len(byte_value)
                var_type = 'list'
            else:
                raise RuntimeError(f'Variable {name} has unknown type')

            self.variables[name]['value'] = value
            self.variables[name]['size'] = size
            self.variables[name]['type'] = var_type
            self.variables[name]['bytes'] = byte_value
            self.variables[name]['offset'] = offset
            del self.variables[name]['ast']

            offset += size

    def solve_commands(self):
        offset = 0
        for command in self.commands:
            if isinstance(command, LabelNode):
                self.labels[command.name] = offset
                continue
            self.interpreter.visit(command)
            offset += config.commands[command.name]['size']

