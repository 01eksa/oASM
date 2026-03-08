class OasmException(Exception):
    pass

class OasmIndexError(OasmException, IndexError):
    def __init__(self, line:int, message: str):
        super().__init__(f'IndexError in line {line}: {message}')

class OasmNameError(OasmException, NameError):
    def __init__(self, line:int, message: str):
        super().__init__(f'NameError in line {line}: {message}')

class OasmSyntaxError(OasmException, SyntaxError):
    def __init__(self, line:int, message: str):
        super().__init__(f'SyntaxError in line {line}: {message}')

class OasmTypeError(OasmException, TypeError):
    def __init__(self, line:int, message: str):
        super().__init__(f'TypeError in line {line}: {message}')
