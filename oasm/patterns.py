import re

IDENTIFIER = re.compile(r'[a-zA-Z_]\w*', re.ASCII)
SECTION = re.compile(r'section\s+(?:\.code|\.data)', re.IGNORECASE)
LABEL = re.compile(rf'{IDENTIFIER.pattern}:', re.ASCII)


FLOAT = re.compile(r'(?:\d+\.\d*|\.\d+)(?:[Ee][+-]?\d+)?')
HEX_INT = re.compile(r'0x[a-fA-F0-9]+')
INT = re.compile(r'\d+')

CHAR = re.compile(r"'(?:[\x20-\x26\x28-\x5B\x5D-\x7E]|\\[\x20-\x7F])'")
STRING = re.compile(r'"(?:[^"\\\n]|\\[\x20-\x7F])+"')

L_PAREN = re.compile(r'\(')
R_PAREN = re.compile(r'\)')
L_BRACKET = re.compile(r'\[')
R_BRACKET = re.compile(r']')
OP = re.compile(r'[+\-*/]')
ASSIGN = re.compile(r'=')
COMMA = re.compile(r',')

NEWLINE = re.compile(r'\n')
SKIP = re.compile(r'[ \t]+|;.*')
UNCLOSED_STRING = re.compile(r'"[^"\n]*')
MISMATCH = re.compile(r'.')
