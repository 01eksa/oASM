import struct
from . import config as config

class CodeGenerator:
    def __init__(self, parser):
        self.commands = parser.commands
        self.variables = parser.variables
        self.labels = parser.labels

        self.code_section = b''
        self.data_section = b''

    def gen_data(self):
        for name in self.variables:
            var = self.variables[name]

            match var['type']:
                case 'string':
                    self.data_section += var['value'].encode('utf-8')
                case 'f64':
                    self.data_section += struct.pack('<d', var['value'])
                case 'i64':
                    self.data_section += var['value'].to_bytes(8, byteorder='little')
                case _:
                    raise Exception(f'Variable {name} has unknown type')

    def gen_code(self):
        for command in self.commands:
            if command['type'] == 'label':
                continue

            if command['type'] != 'command':
                raise RuntimeError(f'Unknown command type: {command}')

            self.code_section += config.commands[command['name']]['code'].to_bytes(1)

            if command['args']:
                for arg in command['args']:
                    arg_type = arg['type']
                    arg_val = arg['value']
                    match arg_type:
                        case 'reg':
                            reg = config.registers.get(arg_val)
                            if reg is None:
                                raise RuntimeError(f'Unknown register: {arg_val}')
                            self.code_section += reg.to_bytes(1)
                        case 'i64':
                            if isinstance(arg_val, int):
                                self.code_section += arg_val.to_bytes(8, byteorder='little', signed=True)
                            elif isinstance(arg_val, float):
                                self.code_section += struct.pack('<d', arg_val)
                            else:
                                raise RuntimeError(f'{arg_val} does not have a valid type')
                        case 'data':
                            self.code_section += arg_val.to_bytes(8, byteorder='little')
                        case 'label':
                            self.code_section += self.labels[arg_val].to_bytes(8, byteorder='little')
                        case _:
                            raise RuntimeError(f'Unknown type: {arg_type}')

    def gen_file(self, stack_size = 0, call_stack_size = 0):
        self.gen_data()
        self.gen_code()

        file = b''

        header = config.HEADER
        version = config.MAJOR.to_bytes(2, byteorder='little') + config.MINOR.to_bytes(2, byteorder='little')
        data_size = len(self.data_section).to_bytes(8, byteorder='little')
        code_size = len(self.code_section).to_bytes(8, byteorder='little')
        stack_size = stack_size.to_bytes(8, byteorder='little')
        call_stack_size = call_stack_size.to_bytes(8, byteorder='little')


        file += header + version + data_size + code_size + stack_size + call_stack_size + self.data_section + self.code_section
        return file
