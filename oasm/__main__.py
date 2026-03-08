import os
import sys
import traceback

from cli_tools import yes_no, get_input, styles as s

from .parser import Parser
from .codegen import CodeGenerator
from .exceptions import OasmException


def path_validator(inp: str):
    return os.path.exists(inp)


def load_file(file_name: str):
    with open(file_name, 'r') as f:
        file_contents = f.read()
    return file_contents

def save_file(file_name: str, file_contents: bytes):
    if os.path.exists(file_name):
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


def process_file(file_name, target_file_name = None):
    file = load_file(file_name)

    print(s.success('File successfully uploaded.'), 'Proceeding to bytecode translation...')

    parser = Parser(file)
    parser.parse()

    codegen = CodeGenerator(parser)
    file = codegen.gen_file()

    print(s.success('Translation to bytecode complete.'), 'Proceeding to save...')

    if target_file_name is None:
        target_file_name = get_input(
            'Enter target file name: ',
            pattern=r'.+',
            if_invalid=s.warning('File name cannot be empty')
        )

    save_file(target_file_name, file)
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
    args = sys.argv

    if len(args) < 2:
        live_session()
    elif len(args) == 2:
        try:
            process_file(args[1])
        except OasmException as e:
            print(s.error(str(e)))
        except Exception as e:
            print(s.error(f'Error: {e}'))
            if yes_no('Show traceback? [y/n]: '):
                traceback.print_exc()
    elif len(args) == 3:
        try:
            process_file(args[1], args[2])
        except OasmException as e:
            print(s.error(str(e)))
        except Exception as e:
            print(s.error(f'Error: {e}'))
            if yes_no('Show traceback? [y/n]: '):
                traceback.print_exc()
    else:
        print(s.error('Too much arguments'))
