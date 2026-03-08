import re

BLANK = re.compile(r'\s+')

INT = re.compile(r'[-+]?[0-9]+')
INT16 = re.compile(r'[-+]?0x[0-9a-fA-F]+')
FLOAT = re.compile(r'[-+]?[0-9]*\.[0-9]+')
STRING = re.compile(r'"((?:[^"\\]|\\.)+)"')
ARRAY = re.compile(r'\[(.+?)]')

REP_STRING = re.compile(r'"((?:[^"\\]|\\.)+)"\s*\*\s*([0-9]+)')
REP_ARRAY = re.compile(r'\[(.+?)]\s*\*\s*([0-9]+)')

ARRAY_INDEX = re.compile(r'([a-zA-Z_]\w*)\[([0-9]+)]', re.ASCII)

VAR = re.compile(r'[a-zA-Z_]\w*', re.ASCII)
LABEL = re.compile(r'[a-zA-Z_]\w*:', re.ASCII)
FUNCTION = re.compile(r'([a-zA-Z_]\w*)\((.*)\)', re.ASCII)
SECTION = re.compile(r'section\s+(\.code|\.data)', re.IGNORECASE)
