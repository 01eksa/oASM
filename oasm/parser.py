import struct

from . import config
from . import patterns as p

class Parser:
    def __init__(self, source):
        self.source = source
        self.variables = {}
        self.commands = []
        self.labels = {}
        self._section = None
        self._addr = 0
        self._line = 0

    def parse_data(self, line: str):
        tokens = line.split('=')
        tokens = [token.strip() for token in tokens]

        name = tokens[0]

        match_name = p.VAR.fullmatch(name)
        if not match_name:
            raise SyntaxError(f'Error in line {self._line}: {name} is invalid')

        if name.upper() in config.reserved:
            raise SyntaxError(f'Error in line {self._line}: {name} is reserved')

        if len(tokens) != 2:
            raise SyntaxError(f'Error in line {self._line}: Invalid syntax')

        raw_value = tokens[1]
        var_type = None
        var_size = None

        if p.INT.fullmatch(raw_value):
            var_type = 'i64'
            var_value = int(raw_value)
            var_size = 8
        elif p.INT16.fullmatch(raw_value):
            var_type = 'i64'
            var_value = int(raw_value, 16)
            var_size = 8
        elif p.FLOAT.fullmatch(raw_value):
            var_type = 'f64'
            var_value = float(raw_value)
            var_size = 8
        elif string := p.STRING.fullmatch(raw_value):
            var_type = 'string'
            var_value = bytes(string.group(1), 'utf-8').decode('unicode_escape')
            var_size = len(var_value.encode('utf-8'))
        elif array := p.ARRAY.fullmatch(raw_value):
            elements = [e.strip() for e in array.group(1).split(',') if e.strip()]
            var_type = 'bytes'
            var_chunks = self.parse_array(elements)

            var_value = b''.join(var_chunks)
            var_size = len(var_value)
        elif match := p.REP_STRING.fullmatch(raw_value):
            var_type = 'string'
            var_value = bytes(match.group(1), 'utf-8').decode('unicode_escape')
            reps = int(match.group(2).strip())
            var_value *= reps
            var_size = len(var_value.encode('utf-8'))
        elif array := p.REP_ARRAY.fullmatch(raw_value):
            elements = [e.strip() for e in array.group(1).split(',') if e.strip()]
            reps = int(array.group(2).strip())

            var_type = 'bytes'
            var_chunks = self.parse_array(elements)

            var_chunks *= reps
            var_value = b''.join(var_chunks)
            var_size = len(var_value)
        else:
            raise SyntaxError(f'Error in line {self._line}: {raw_value} is not a valid value')

        self.variables[name] = {'value': var_value, 'size': var_size, 'type': var_type, 'addr': self._addr}
        self._addr += var_size


    def parse_code(self, line: str):
        tokens = line.split()

        if p.LABEL.fullmatch(tokens[0]):
            self.commands.append({'type': 'label', 'name': tokens[0]})
            self.labels[tokens[0]] = self._addr
            return

        name = tokens[0].upper()
        if name not in config.commands:
            raise SyntaxError(f'Error in line {self._line}: Unknown command: {name}')

        command = dict()
        command['type'] = 'command'
        command['name'] = name
        command['args'] = []
        arg_types = []

        if len(tokens) > 1:
            for token in tokens[1::]:
                arg_type = None
                arg_value = None

                if p.INT.fullmatch(token):
                    arg_type = 'i64'
                    arg_value = int(token)
                elif p.INT16.fullmatch(token):
                    arg_type = 'i64'
                    arg_value = int(token, 16)
                elif p.FLOAT.fullmatch(token):
                    arg_type = 'i64'
                    arg_value = float(token)
                elif p.VAR.fullmatch(token):
                    if token.upper() in config.commands:
                        raise SyntaxError(f'Error in line {self._line}: Invalid syntax')
                    if (reg := token.upper()) in config.registers:
                        arg_type = 'reg'
                        arg_value = reg
                    elif token in self.variables:
                        arg_type = 'data'
                        arg_value = self.variables[token]['addr']
                    else:
                        raise NameError(f'Error in line {self._line}: Unknown identifier: {token}')
                elif p.LABEL.fullmatch(token):
                    arg_type = 'label'
                    arg_value = token
                elif func := p.FUNCTION.fullmatch(token):
                    func_name = func.group(1)
                    if func_name not in config.functions:
                        raise NameError(f'Error in line {self._line}: Unknown compile-time function: {func_name}')

                    match func_name:
                        case 'sizeof':
                            var = func.group(2)
                            if var not in self.variables:
                                raise NameError(f'Error in line {self._line}: Unknown variable: {var}')
                            arg_type = 'i64'
                            arg_value = self.variables[var]['size']
                        case 'len':
                            var = func.group(2)
                            if var not in self.variables:
                                raise NameError(f'Error in line {self._line}: Unknown variable: {var}')
                            arg_type = 'i64'
                            if self.variables[var]['type'] == 'string':
                                arg_value = self.variables[var]['size']
                            else:
                                arg_value = self.variables[var]['size'] // 8
                        case _:
                            raise RuntimeError(
                                f'Error: function {func_name} exist in the config, but is not handled in the code.'
                                'Please report this to the developer.')
                else:
                    raise SyntaxError(f'Error in line {self._line}: Invalid syntax')

                command['args'].append({'type': arg_type, 'value': arg_value})
                arg_types.append(arg_type)

        if arg_types != config.commands[name]['args']:
            if name not in config.command_aliases:
                raise SyntaxError(f'Error in line {self._line}: wrong arguments for command {name}')
            for alias in config.command_aliases[name]:
                if arg_types == config.commands[alias]['args']:
                    command['name'] = alias
                    break
            else:
                raise SyntaxError(f'Error in line {self._line}: wrong arguments for command {name}')


        command['addr'] = self._addr
        self._addr += config.commands[command['name']]['size']

        self.commands.append(command)


    def parse(self):
        self._section = None
        self._addr = 0
        self._line = 0
        lines = self.source.split('\n')

        for line in lines:
            self._line += 1
            line = line.split(';')[0].strip()

            if not line or p.BLANK.fullmatch(line):
                continue

            match = p.SECTION.fullmatch(line)
            if match:
                self._section = match.group(1).lower()
                self._addr = 0
                continue

            if self._section is None:
                raise Exception(f'Error in line {self._line}: Wrong format')

            if self._section == '.data':
                self.parse_data(line)
            elif self._section == '.code':
                self.parse_code(line)

    def parse_array(self, elements: list[str]) -> list[bytes]:
        array = []

        for el in elements:
            el = el.strip()
            if p.INT.fullmatch(el):
                array.append(int(el).to_bytes(8, byteorder='little', signed=True))
            elif p.INT16.fullmatch(el):
                array.append(int(el, 16).to_bytes(8, byteorder='little', signed=True))
            elif p.FLOAT.fullmatch(el):
                array.append(struct.pack('<d', float(el)))
            else:
                raise SyntaxError(f'Error in line {self._line}: {el} is not a valid element for a list')

        return array