import argparse
import os
import traceback

from cli_tools import yes_no, get_input, styles as s

from . import config
from .exceptions import OasmException
from .meta import File
from .parser import Parser
from .resolver import Resolver
from .tokenizer import Tokenizer
from .translator import Translator


def get_bin(file: File) -> bytes:
    tokenizer = Tokenizer(file)
    tokens = tokenizer.work()

    parser = Parser(tokens)
    macros, consts, variables, commands = parser.work()

    resolver = Resolver(macros, consts, variables, commands)
    resolved_context = resolver.work()

    translator = Translator(*resolved_context)
    bin_file = translator.gen_file()
    return bin_file

def path_validator(inp: str):
    return os.path.exists(inp)

def load_file(file_name: str):
    with open(file_name, 'r') as f:
        file_contents = f.read().replace('\t', '    ')
    return File(file_name, file_contents)

def save_file(file_name: str, file_contents: bytes, rewrite: bool = False):
    if not rewrite and os.path.exists(file_name):
        if not yes_no('File already exist. Overwrite? [y/n]: '):
            file_name = get_input(
                'Enter target file name: ',
                pattern=r'.+',
                if_invalid=s.warning('File name cannot be empty')
            )
            save_file(file_name, file_contents)
            return

    with open(file_name, 'wb') as f:
        f.write(file_contents)


def process_file(file_name: str, target_file_name: str = None, rewrite: bool = False):
    file = load_file(file_name)

    print(s.success('File successfully uploaded.'))
    bin_file = get_bin(file)
    print(s.success('Translation to bytecode complete.'))

    if target_file_name is None:
        target_file_name = get_input(
            'Enter target file name: ',
            pattern=r'.+',
            if_invalid=s.warning('File name cannot be empty')
        )

    save_file(target_file_name, bin_file, rewrite)
    print(s.success(f'File {target_file_name} saved'))


def live_session():
    while True:
        file_name = get_input(
            'Enter source file name: ',
            validator=path_validator,
            if_invalid=s.error('File not found')
        )

        try:
            process_file(file_name)
        except OasmException as e:
            print(s.error(str(e)))
        except Exception as e:
            print(s.error(f'Error: {e}'))
            if yes_no('Show traceback? [y/n]: '):
                traceback.print_exc()

        if not yes_no('Repeat? [y/n]: '):
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='oASM',
        description='Assembler for oVM',
    )

    parser.add_argument('source', nargs='?', help='Source (*.oasm file)', default=None)
    parser.add_argument('target', nargs='?', help='Target (*.ovm file)', default=None)
    parser.add_argument(
        '--big',
        action='store_true',
        help='Use this flag to save all numbers in big-endian'
    )
    parser.add_argument(
        '--rewrite',
        action='store_true',
        help='Use this flag to rewrite existing file without asking'
    )
    parser.add_argument(
        '--stack-size',
        type=int,
        default=0,
        help='Size of stack in elements (not bytes). 0 = default'
    )
    parser.add_argument(
        '--call-stack-size',
        type=int,
        default=0,
        help='Size of call stackin elements (number of nested calls). 0 = default'
    )

    args = parser.parse_args()

    if args.big:
        config.byteorder = 'big'
    config.stack_size = args.stack_size
    config.call_stack_size = args.call_stack_size

    if args.source:
        try:
            process_file(args.source, args.target, args.rewrite)
        except OasmException as e:
            print(s.error(str(e)))
        except Exception as e:
            print(s.error(f'Error: {e}'))
            if yes_no('Show traceback? [y/n]: '):
                traceback.print_exc()
    else:
        live_session()