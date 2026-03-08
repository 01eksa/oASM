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
            raise SyntaxError(f'Error in line {self._line}: {line}\n{name} is not a valid name')

        if name.upper() in config.reserved:
            raise SyntaxError(f'Error in line {self._line}: {line}\n{name} is reserved')

        if len(tokens) != 2:
            raise SyntaxError(f'Error in line {self._line}: {line}\nInvalid syntax')

        value = tokens[1]
        var_type = None
        var_size = None

        if p.INT.fullmatch(value):
            var_type = 'i64'
            value = int(value)
            var_size = 8
        elif p.INT16.fullmatch(value):
            var_type = 'i64'
            value = int(value, 16)
            var_size = 8
        elif p.FLOAT.fullmatch(value):
            var_type = 'f64'
            value = float(value)
            var_size = 8
        elif match := p.STRING.fullmatch(value):
            var_type = 'string'
            value = bytes(match.group(1), 'utf-8').decode('unicode_escape')
            var_size = len(value)
        else:
            raise SyntaxError(f'Error in line {self._line}: {line}\n{value} is not a valid value')

        self.variables[name] = {'value': value, 'size': var_size, 'type': var_type, 'addr': self._addr}
        self._addr += var_size


    def parse_code(self, line: str):
        tokens = line.split()

        if p.LABEL.fullmatch(tokens[0]):
            self.commands.append({'type': 'label', 'name': tokens[0]})
            self.labels[tokens[0]] = self._addr
            return

        name = tokens[0].upper()
        if name not in config.commands:
            raise SyntaxError(f'Error in line {self._line}: {line}\nUnknown command: {name}')

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
                        raise SyntaxError(f'Error in line {self._line}: {line}\n'
                                          f'Invalid syntax')
                    if (reg := token.upper()) in config.registers:
                        arg_type = 'reg'
                        arg_value = reg
                    elif token in self.variables:
                        arg_type = 'data'
                        arg_value = self.variables[token]['addr']
                    else:
                        raise NameError(f'Error in line {self._line}: {line}\n'
                                          f'Unknown identifier: {token}')
                elif p.LABEL.fullmatch(token):
                    arg_type = 'label'
                    arg_value = token
                elif func := p.FUNCTION.fullmatch(token):
                    func_name = func.group(1)
                    if func_name not in config.functions:
                        raise NameError(f'Error in line {self._line}: {line}\n'
                                        f'Unknown compile-time function: {func_name}')

                    match func_name:
                        case 'sizeof':
                            var = func.group(2)
                            if var not in self.variables:
                                raise NameError(f'Error in line {self._line}: {line}\n'
                                                f'Unknown variable: {var}')
                            arg_type = 'i64'
                            arg_value = self.variables[var]['size']
                        case _:
                            raise RuntimeError(
                                f'Error: function {func_name} exist in the config, but is not handled in the code.'
                                'Please report this to the developer.')
                else:
                    raise SyntaxError(f'Error in line {self._line}: {line}\n'
                                      f'Invalid syntax')

                command['args'].append({'type': arg_type, 'value': arg_value})
                arg_types.append(arg_type)

        if arg_types != config.commands[name]['args']:
            if name not in config.alias_commands:
                raise SyntaxError(f'Error in line {self._line}: {line}\n'
                                  f'Wrong arguments for command {name}')
            for alias in config.alias_commands[name]:
                if arg_types == config.commands[alias]['args']:
                    command['name'] = alias
                    break
            else:
                raise SyntaxError(f'Error in line {self._line}: {line}\n'
                                  f'Wrong arguments for command {name}')


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
                raise Exception(f'Error in line {line}\nWrong format')

            if self._section == '.data':
                self.parse_data(line)
            elif self._section == '.code':
                self.parse_code(line)
