from typing import Literal
import struct


def to_bytes(value: int | float | str | list, byteorder: Literal['little', 'big'] = 'little') -> bytes:
    if isinstance(value, int):
        return value.to_bytes(8, byteorder=byteorder, signed=True)

    elif isinstance(value, float):
        fmt = '<d' if byteorder == 'little' else '>d'
        return struct.pack(fmt, value)

    elif isinstance(value, str):
        return value.encode('utf-8')

    elif isinstance(value, list):
        return b''.join([to_bytes(el, byteorder) for el in value])

    else:
        raise TypeError(f'Cannot convert {type(value)} to bytes')
