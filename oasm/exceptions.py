from .meta import MetaData

class OasmException(Exception):
    def __init__(self, meta: MetaData, message: str):
        super().__init__(f'[{meta.to_str()}]: {message}')


class OasmIndexError(OasmException, IndexError):
    def __init__(self, meta: MetaData, message=None):
        if message is None:
            message = ''
        else:
            message = '\n' + format_error(meta, message)
        super().__init__(meta, f'IndexError{message}')


class OasmNameError(OasmException, NameError):
    def __init__(self, meta: MetaData, message=None):
        if message is None:
            message = ''
        else:
            message = '\n' + format_error(meta, message)
        super().__init__(meta, f'NameError{message}')


class OasmSyntaxError(OasmException, SyntaxError):
    def __init__(self, meta: MetaData, message=None):
        if message is None:
            message = ''
        else:
            message = '\n' + format_error(meta, message)
        super().__init__(meta, f'SyntaxError{message}')


class OasmTypeError(OasmException, TypeError):
    def __init__(self, meta: MetaData, message=None):
        if message is None:
            message = ''
        else:
            message = '\n' + format_error(meta, message)
        super().__init__(meta, f'TypeError{message}')


class OasmValueError(OasmException, ValueError):
    def __init__(self, meta: MetaData, message=None):
        if message is None:
            message = ''
        else:
            message = '\n' + format_error(meta, message)
        super().__init__(meta, f'ValueError{message}')


class OasmZeroDivisionError(OasmException, ZeroDivisionError):
    def __init__(self, meta: MetaData, message=None):
        if message is None:
            message = ''
        else:
            message = '\n' + format_error(meta, message)
        super().__init__(meta, f'ZeroDivisionError{message}')


def format_error(meta: MetaData, message: str):
    formated_err = f'{meta.file.content.split('\n')[meta.line - 1]}\n'
    formated_err += ' ' * (meta.column - 1) + '^\n'
    formated_err += message

    return formated_err
