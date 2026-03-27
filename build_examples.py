import os
import subprocess

for file in os.listdir('./examples'):
    print(
        subprocess.run(
            ['py', '-m', 'oasm', f'examples/{file}', f'bin/{file.split('.')[0]}.ovm', '--rewrite'],
            capture_output=True,
            text=True
        ).stdout
    )
