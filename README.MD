# oASM

An assembler for the [oVM](https://github.com/01eksa/oVM) virtual machine. Takes `.oasm` source files and produces
`.ovm` binaries ready to execute.

Note: This only covers the specifics of the assembler implementation. Detailed documentation on the virtual machine can
be found at the link above.

---

## Table of Contents

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
- [Instruction Reference](#instruction-reference)
- [CLI Usage](#cli-usage)
- [Examples](#Examples)

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
PUSH 42     ; inline comment
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
    LOAD nums[0]    ; loads 10
    LOAD nums[2]    ; loads 30
    PUSH nums[1]  ; pushes pointer to the second element
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

## Instruction Reference

For a full description of each instruction's runtime semantics see the oVM documentation. The table below lists the
source-level syntax accepted by the assembler.

Instructions with no arguments are written as a bare mnemonic. The `Size` column shows the compiled byte size (opcode +
operands).

### Control Flow

| Mnemonic     | Size | Argument  | Description                          |
|--------------|------|-----------|--------------------------------------|
| `EXIT`       | 1    | —         | Terminate execution                  |
| `VMCALL`     | 1    | —         | Call vmcall identified by `FR`       |
| `CALL label` | 9    | label ref | Push return address, jump to `label` |
| `RET`        | 1    | —         | Return to caller                     |
| `JMP label`  | 9    | label ref | Unconditional jump                   |
| `JIF label`  | 9    | label ref | Jump if `BF == true`                 |
| `JNIF label` | 9    | label ref | Jump if `BF == false`                |
| `JEF label`  | 9    | label ref | Jump if `EF == true`                 |
| `JNEF label` | 9    | label ref | Jump if `EF == false`                |
| `LOOP label` | 9    | label ref | Decrement `CR`; jump if `CR > 0`     |
| `DEBUG`      | 1    | —         | Enter interactive debug console      |

### Stack Operations

| Mnemonic    | Size | Argument  | Description                                  |
|-------------|------|-----------|----------------------------------------------|
| `PUSH val`  | 9    | immediate | Push 64-bit immediate                        |
| `PUSH reg`  | 2    | register  | Push value of register (`PUSHR`)             |
| `PUSH var`  | 9    | data ref  | Push pointer to data segment (`PEA`)         |
| `POP`       | 1    | —         | Discard top of stack                         |
| `POP reg`   | 2    | register  | Pop into register (`POPR`)                   |
| `DUP`       | 1    | —         | Duplicate top of stack                       |
| `PEA var`   | 9    | data ref  | Push pointer to data segment (explicit form) |
| `LOAD var`  | 9    | data ref  | Read 8 bytes from data segment, push         |
| `STORE var` | 9    | data ref  | Pop, write 8 bytes to data segment           |

### Call Stack Operations

| Mnemonic | Size | Description                     |
|----------|------|---------------------------------|
| `PUSHCP` | 1    | Push current `CP` to call stack |
| `POPCP`  | 1    | Pop call stack into `CP`        |

### Register Operations

| Mnemonic        | Size | Arguments      | Description                               |
|-----------------|------|----------------|-------------------------------------------|
| `MOV dst, val`  | 10   | reg, immediate | Set register to immediate (`SETR`)        |
| `MOV dst, src`  | 3    | reg, reg       | Copy register value                       |
| `SETR reg, val` | 10   | reg, immediate | Set register to immediate (explicit form) |
| `PUSHR reg`     | 2    | register       | Push register value (explicit form)       |
| `POPR reg`      | 2    | register       | Pop into register (explicit form)         |
| `INC reg`       | 2    | register       | Increment register (`INCR`)               |
| `DEC reg`       | 2    | register       | Decrement register (`DECR`)               |
| `INCR reg`      | 2    | register       | Increment register (explicit form)        |
| `DECR reg`      | 2    | register       | Decrement register (explicit form)        |
| `CHECKEF`       | 1    | —              | `BF = EF`                                 |
| `CLEAREF`       | 1    | —              | `EF = false`                              |

### Memory Operations

| Mnemonic | Size | Description                                            |
|----------|------|--------------------------------------------------------|
| `ALLOC`  | 1    | Pop `a`; push pointer to a new heap block of `a` bytes |
| `FREE`   | 1    | Free heap block at address `a`                         |
| `WRITE`  | 1    | Write `b` (8 bytes) to address `a`                     |
| `READ`   | 1    | Push 8 bytes read from address `a`                     |
| `WRITEB` | 1    | Write low byte of `b` to address `a`                   |
| `READB`  | 1    | Push byte at address `a`, zero-extended                |

### Integer Arithmetic

| Mnemonic | Size | Description                                   |
|----------|------|-----------------------------------------------|
| `INC`    | 1    | `a + 1`                                       |
| `DEC`    | 1    | `a - 1`                                       |
| `ADD`    | 1    | `a + b`                                       |
| `SUB`    | 1    | `a - b`                                       |
| `MUL`    | 1    | `a * b`                                       |
| `DIV`    | 1    | `a / b`; sets `EF` and pushes `0` if `b == 0` |
| `MOD`    | 1    | `a % b`; sets `EF` and pushes `0` if `b == 0` |
| `POW`    | 1    | `pow(a, b)` truncated to `int64_t`            |

### Floating-Point Arithmetic

| Mnemonic | Size | Description                                          |
|----------|------|------------------------------------------------------|
| `INCF`   | 1    | `a + 1.0`                                            |
| `DECF`   | 1    | `a - 1.0`                                            |
| `ADDF`   | 1    | `a + b`                                              |
| `SUBF`   | 1    | `a - b`                                              |
| `MULF`   | 1    | `a * b`                                              |
| `DIVF`   | 1    | `a / b`; sets `EF` and pushes `0` if `b == 0.0`      |
| `MODF`   | 1    | `fmod(a, b)`; sets `EF` and pushes `0` if `b == 0.0` |
| `POWF`   | 1    | `pow(a, b)`                                          |

### Bitwise Operations

| Mnemonic | Size | Description |
|----------|------|-------------|
| `AND`    | 1    | `a & b`     |
| `OR`     | 1    | `a \| b`    |
| `XOR`    | 1    | `a ^ b`     |
| `INV`    | 1    | `~a`        |
| `SHL`    | 1    | `a << b`    |
| `SHR`    | 1    | `a >> b`    |

### Logic & Comparison

| Mnemonic | Size | Description               |
|----------|------|---------------------------|
| `NOT`    | 1    | `BF = !BF`                |
| `CMP`    | 1    | `BF = (a == b)` (integer) |
| `CMPLT`  | 1    | `BF = (a < b)` (integer)  |
| `CMPGT`  | 1    | `BF = (a > b)` (integer)  |
| `CMPF`   | 1    | `BF = (a == b)` (float)   |
| `CMPLTF` | 1    | `BF = (a < b)` (float)    |
| `CMPGTF` | 1    | `BF = (a > b)` (float)    |

### I/O

| Mnemonic     | Size | Description                                                                   |
|--------------|------|-------------------------------------------------------------------------------|
| `PRINTENDL`  | 1    | Print a newline to stdout                                                     |
| `PRINTINT`   | 1    | Print `a` as `int64_t`                                                        |
| `SCANINT`    | 1    | Read `int64_t` from stdin and push; sets `EF` and pushes `0` on invalid input |
| `PRINTFLOAT` | 1    | Print `a` as `double`                                                         |
| `SCANFLOAT`  | 1    | Read `double` from stdin and push; sets `EF` and pushes `0` on invalid input  |
| `ITOF`       | 1    | Convert `a` from `int64_t` to `double`, push                                  |
| `FTOI`       | 1    | Convert `a` from `double` to `int64_t` (truncates), push                      |

### VMCalls

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