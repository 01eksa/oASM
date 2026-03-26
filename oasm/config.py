from typing import Literal

HEADER = "OVM>"
MAJOR = 0
MINOR = 1
byteorder: Literal['little', 'big'] = 'little'
stack_size: int = 0
call_stack_size: int = 0

commands = {
  "EXIT":      {"code": 0,   "size": 1,  "args": []},
  "VMCALL":    {"code": 1,   "size": 1,  "args": []},
  "CALL":      {"code": 2,   "size": 9,  "args": ["label"]},
  "RET":       {"code": 3,   "size": 1,  "args": []},
  "JMP":       {"code": 4,   "size": 9,  "args": ["label"]},
  "JIF":       {"code": 5,   "size": 9,  "args": ["label"]},
  "JNIF":      {"code": 6,   "size": 9,  "args": ["label"]},
  "JEF":       {"code": 7,   "size": 9,  "args": ["label"]},
  "JNEF":      {"code": 8,   "size": 9,  "args": ["label"]},
  "LOOP":      {"code": 9,   "size": 9,  "args": ["label"]},
  "DEBUG":     {"code": 10,  "size": 1,  "args": []},

  "PUSH":      {"code": 16,  "size": 9,  "args": ["i64"]},
  "POP":       {"code": 17,  "size": 1,  "args": []},
  "DUP":       {"code": 18,  "size": 1,  "args": []},
  "PUSHDATA":  {"code": 19,  "size": 9,  "args": ["data"]},
  "POPDATA":   {"code": 20,  "size": 9,  "args": ["data"]},

  "PUSHCP":    {"code": 32,  "size": 1,  "args": []},
  "POPCP":     {"code": 33,  "size": 1,  "args": []},

  "SETREG":    {"code": 48,  "size": 10, "args": ["reg", "i64"]},
  "PUSHREG":   {"code": 49,  "size": 2,  "args": ["reg"]},
  "POPREG":    {"code": 50,  "size": 2,  "args": ["reg"]},
  "INCREG":    {"code": 51,  "size": 2,  "args": ["reg"]},
  "DECREG":    {"code": 52,  "size": 2,  "args": ["reg"]},
  "CHECKEF":   {"code": 53,  "size": 1,  "args": []},
  "CLEAREF":   {"code": 54,  "size": 1,  "args": []},
  "MOV":       {"code": 55,  "size": 3,  "args": ["reg", "reg"]},

  "ALLOC":     {"code": 64,  "size": 1,  "args": []},
  "FREE":      {"code": 65,  "size": 1,  "args": []},
  "WRITE":     {"code": 66,  "size": 1,  "args": []},
  "READ":      {"code": 67,  "size": 1,  "args": []},
  "WRITEB":     {"code": 68,  "size": 1,  "args": []},
  "READB":      {"code": 69,  "size": 1,  "args": []},

  "INC":       {"code": 80,  "size": 1,  "args": []},
  "DEC":       {"code": 81,  "size": 1,  "args": []},
  "ADD":       {"code": 82,  "size": 1,  "args": []},
  "SUB":       {"code": 83,  "size": 1,  "args": []},
  "MUL":       {"code": 84,  "size": 1,  "args": []},
  "DIV":       {"code": 85,  "size": 1,  "args": []},
  "MOD":       {"code": 86,  "size": 1,  "args": []},
  "POW":       {"code": 87,  "size": 1,  "args": []},
  "INCF":      {"code": 88,  "size": 1,  "args": []},
  "DECF":      {"code": 89,  "size": 1,  "args": []},
  "ADDF":      {"code": 90,  "size": 1,  "args": []},
  "SUBF":      {"code": 91,  "size": 1,  "args": []},
  "MULF":      {"code": 92,  "size": 1,  "args": []},
  "DIVF":      {"code": 93,  "size": 1,  "args": []},
  "MODF":      {"code": 94,  "size": 1,  "args": []},
  "POWF":      {"code": 95,  "size": 1,  "args": []},

  "AND":       {"code": 96,  "size": 1,  "args": []},
  "OR":        {"code": 97,  "size": 1,  "args": []},
  "XOR":       {"code": 98,  "size": 1,  "args": []},
  "INV":       {"code": 99,  "size": 1,  "args": []},
  "SHL":       {"code": 100, "size": 1,  "args": []},
  "SHR":       {"code": 101, "size": 1,  "args": []},

  "NOT":       {"code": 102, "size": 1,  "args": []},
  "CMP":       {"code": 103, "size": 1,  "args": []},
  "CMPLT":     {"code": 104, "size": 1,  "args": []},
  "CMPGT":     {"code": 105, "size": 1,  "args": []},
  "CMPF":      {"code": 106, "size": 1,  "args": []},
  "CMPLTF":    {"code": 107, "size": 1,  "args": []},
  "CMPGTF":    {"code": 108, "size": 1,  "args": []},

  "PRINTENDL": {"code": 112, "size": 1,  "args": []},
  "PRINTINT":  {"code": 113, "size": 1,  "args": []},
  "SCANINT":   {"code": 114, "size": 1,  "args": []},
  "PRINTFLOAT":{"code": 115, "size": 1,  "args": []},
  "SCANFLOAT": {"code": 116, "size": 1,  "args": []},
  "ITOF":      {"code": 117, "size": 1, "args": []},
  "FTOI":      {"code": 118, "size": 1, "args": []},
}

command_aliases = {
  "PUSH": ["PUSHREG", "PUSHDATA"],
  "POP": ["POPREG", "POPDATA"],
  "MOV": ["SETREG"],
  "INC": ["INCREG"],
  "DEC": ["DECREG"],
}

registers = {
  "FR":   0,
  "ARG1": 1,
  "ARG2": 2,
  "ARG3": 3,
  "ARG4": 4,
  "REG1": 16,
  "REG2": 17,
  "REG3": 18,
  "REG4": 19,
  "CR":   32
}

functions = {
  "sizeof": {'args': ["data"], 'returns': 'i64'},
  "lenof": {'args': ["data"], 'returns': 'i64'},
}

sections = [
  ".data",
  ".code",
]

command_names = list(commands.keys())
register_names = list(registers.keys())
function_names = list(functions.keys())

keywords = command_names + register_names
reserved = keywords + function_names
