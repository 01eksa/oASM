# oASM

An assembler for the [oVM](https://github.com/01eksa/oVM) virtual machine. Takes `.oasm` source files and produces
`.ovm` binaries ready to execute.

Note: This only covers the specifics of the assembler implementation. Detailed documentation on the virtual machine can
be found at the link above.

---

## Table of Contents

- [Hello World example](#Hello-World-example)
- [File Structure](#file-structure)
- [Comments](#comments)
- [Literals](#literals)
- [Expressions](#expressions)
- [Data Section](#data-section)
    - [Variable Types](#variable-types)
    - [Array Indexing](#array-indexing)
    - [Built-in Functions](#built-in-functions)
- [Code Section](#code-section)
    - [Labels](#labels)
    - [Registers](#registers)
    - [Instructions](#instructions)
    - [Overloaded Mnemonics](#overloaded-mnemonics)
- [Examples](#Examples)

---

### Hello World example

A vmcall is invoked by setting `FR` to the vmcall ID and executing `VMCALL`. Arguments are passed via `ARG1`–`ARG8`.
Refer to the oVM documentation for the full vmcall table.

```asm
section .data
	msg = "Hello, World!\n\0"

section .code
	mov		fr,		1	    ; syscall code: printstr
	lea 	arg1,   msg	    ; Load pointer to the string into argument register
	mov		arg2,	0       ; string size (0 = print as c-string, all chars until '\0')
	vmcall
	exit
```

---

## File Structure

An oASM source file is divided into sections declared with the `section` directive. Two sections are available and each
may appear at most once.

```asm
section .data
    ; variable declarations

section .code
    ; instructions and labels
```

---

## Comments

A semicolon (`;`) starts a comment that runs to the end of the line. Comments may appear anywhere.

```asm
; full-line comment
push    42     ; inline comment
```

---

## Literals

| Kind    | Syntax                  | Examples                       | Notes                             |
|---------|-------------------------|--------------------------------|-----------------------------------|
| Integer | decimal digits          | `0`, `42`, `1000`              | Stored as signed `int64_t`        |
| Hex int | `0x` prefix             | `0xFF`, `0x1A2B`               | Case-insensitive digits           |
| Char    | single-quoted character | `'A'`, `'\n'`, `'\x41'`        | Stored as `int64_t`               |
| Float   | decimal with `.` or `e` | `3.14`, `.5`, `1e10`, `2.5e-3` | Stored as IEEE 754 `double`       |
| String  | double-quoted sequence  | `"hello"`, `"line\n"`          | UTF-8; escape sequences supported |

String and char literals support the standard C-style escape sequences (`\n`, `\t`, `\r`, `\\`, `\"`, `\'`, etc.). Empty
strings (`""`) are not permitted.

---

## Expressions

Expressions can appear anywhere a value is expected: in the `.data` section and as instruction arguments. The supported
operators are:

| Operator  | Description                | Associativity |
|-----------|----------------------------|---------------|
| `+`       | Addition                   | Left          |
| `-`       | Subtraction                | Left          |
| `*`       | Multiplication             | Left          |
| `/`       | Division (result is float) | Left          |
| `//`      | Division (result is int)   | Left          |
| unary `+` | Identity                   | —             |
| unary `-` | Negation                   | —             |

Standard precedence applies (`*`, `/` and `//` bind tighter than `+` and `-`). Parentheses override precedence.

Expressions are evaluated at **assembly time**, not at runtime. Operands may be:

- Any numeric literal (integer, hex, float, char)
- A previously declared variable name — produces a data-segment pointer to that variable
- A constant name (reserved for a future `const` directive; not yet in use)
- A built-in function call: `sizeof(name)`, `lenof(name)`
- An indexed variable: `name[index_expr]` — produces a pointer to the element at the given index

---

## Data Section

Each line in `.data` declares one variable:

```asm
section .data
    name = expression
```

`name` must be a valid identifier and must not duplicate another variable name, constant, or macro. The identifier, `=`,
and the expression must all be on the same line.

```asm
section .data
    answer      = 42
    pi          = 3.14159
    greeting    = "Hello, World!\n"
    buffer      = [0] * 10
    buf_size    = sizeof(buffer)
```

Variable names are case-sensitive.

### Variable Types

The type of variable is inferred from its initializer expression:

| Expression result | Stored type | Size in data segment                                                          |
|-------------------|-------------|-------------------------------------------------------------------------------|
| Integer           | `i64`       | 8 bytes (little-endian)                                                       |
| Float             | `f64`       | 8 bytes (IEEE 754 double)                                                     |
| String            | `str`       | UTF-8 byte length (no null terminator stored — add `'\0'` manually if needed) |
| List `[…]`        | `list`      | N × 8 bytes (each element is an `i64` or `f64`)                               |

All variables occupy a contiguous block in the `.ovm` data segment in declaration order.

### Array Indexing

When passing a variable to an instruction, you can offset into it using bracket syntax. The index is an expression
evaluated at assembly time.

```asm
section .data
    nums = [10, 20, 30, 40]

section .code
    load    nums[0]    ; loads 10
    push    nums[2]    ; loads 30 - see Overloaded Mnemonics section
    pea     nums[1]    ; pushes pointer to the second element
```

For `list` variables the index is an **element index** (each element is 8 bytes). For `str` variables the index is a
**byte index**.

### Built-in Functions

Built-in functions can be used inside expressions in both sections.

#### `sizeof(name)`

Returns the total byte size of the variable `name` in the data segment.

```asm
section .data
    message  = "Hello"
    msg_size = sizeof(message)   ; 5
    table    = [1, 2, 3, 4]
    tbl_size = sizeof(table)     ; 32  (4 × 8 bytes)
```

`sizeof` is also useful as an instruction argument:

```asm
    mov     arg2, sizeof(message)
    vmcall                        ; e.g. printstr with exact byte count
```

#### `lenof(name)`

Returns the element count for `list`, character count for strings, 1 for i64 and f64.
Important: `lenof` and `sizeof` behave the same for strings. Some utf-8 symbols are stored as 2 characters.

```asm
section .data
    items       = [100, 200, 300]
    item_count  = lenof(items)      ; 3
```

---

## Code Section

Instructions and labels appear in the `.code` section, one per line. Identifiers that are command names or register
names are **reserved** and cannot be used as variable names.

### Labels

A label is an identifier followed immediately by `:`, on a line by itself. It marks the current byte offset in the
code segment and can be used as the target of any jump or call instruction.

```asm
section .code
    mov     cr, 5
    
_loop:
    push    cr
    printint
    printendl
    loop    _loop:
    
    exit
```

Label names follow the same identifier rules as variable names and occupy their own namespace — a label may share its
name with a variable.
Label names are case-sensitive.

### Registers

Register names are case-insensitive. The available registers are:

| Name        | Purpose                           |
|-------------|-----------------------------------|
| `FR`        | Function register — vmcall ID     |
| `ARG1–ARG8` | Call arguments (caller-populated) |
| `CR`        | Counter register (used by `LOOP`) |
| `REG1–REG8` | General-purpose registers         |

`FR`, `ARG1`–`ARG8`, `CR`, and `REG1`–`REG8` are all valid as operands to register instructions.

### Instructions

Instructions follow this general syntax:

```
MNEMONIC
MNEMONIC arg
MNEMONIC arg1, arg2
```

Arguments are expressions. An argument that resolves to a **register name token** is treated as a register reference;
one that resolves to a **variable name** (or indexed variable) becomes a data-segment offset; a **label name** becomes
a code-segment offset; everything else is an immediate integer or float.

Mnemonics are case-insensitive. I recommend to use lowercase.

### Overloaded Mnemonics

Several mnemonics are **overloaded** — the assembler selects the correct underlying opcode based on the types of the
arguments supplied:

| Written form   | Argument types | Assembled as |
|----------------|----------------|--------------|
| `PUSH val`     | immediate      | `PUSH`       |
| `PUSH reg`     | register       | `PUSHR`      |
| `PUSH var`     | data ref       | `LOAD`       |
| `POP`          | (none)         | `POP`        |
| `POP reg`      | register       | `POPR`       |
| `POP var`      | data ref       | `STORE`      |
| `MOV dst, src` | reg, reg       | `MOV`        |
| `MOV dst, val` | reg, immediate | `SETR`       |
| `MOV dst, var` | reg, data ref  | `LOADR`      |
| `MOV var, src` | data ref, reg  | `STORER`     |
| `INC reg`      | register       | `INCR`       |
| `INC`          | (none)         | `INC`        |
| `DEC reg`      | register       | `DECR`       |
| `DEC`          | (none)         | `DEC`        |

The underlying opcodes (`PUSHR`, `PEA`, `POPR`, `SETR`, `INCR`, `DECR`) can also be written directly.

---

## CLI Usage

```
py -m oasm [source] [target] [options]
```

| Argument / Option     | Description                                                       |
|-----------------------|-------------------------------------------------------------------|
| `source`              | Path to the `.oasm` source file                                   |
| `target`              | Path for the output `.ovm` file (prompted if omitted)             |
| `--big`               | Write all multi-byte values in big-endian order (default: little) |
| `--rewrite`           | Overwrite the target file without prompting                       |
| `--stack-size N`      | Set the data stack capacity in elements (0 = VM default: 512)     |
| `--call-stack-size N` | Set the call stack capacity in frames (0 = VM default: 64)        |

If `source` is omitted, oASM starts an interactive loop that prompts for a file name, assembles it, and asks whether
to continue.

**Examples:**

```bash
# Assemble and write to output.ovm
py -m oasm program.oasm output.ovm

# Overwrite existing output without prompting
py -m oasm program.oasm output.ovm --rewrite

# Use a 1024-element stack; write in big-endian
py -m oasm program.oasm output.ovm --stack-size 1024 --big

# Interactive mode
py -m oasm
```

## Examples

The code examples are in `/examples/`.
There is script to build them:

```bash
py build_examples.py
```

This script assembles all .oasm files into the `/bin/` folder.