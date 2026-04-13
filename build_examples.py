import os
import sys
import subprocess

if not os.path.exists('./bin'):
    os.makedirs('./bin')

for file in os.listdir('./examples'):
    if file.endswith('.oasm'):
        source = os.path.join('examples', file)
        target = os.path.join('bin', file.split('.')[0] + '.ovm')
        result = subprocess.run(
                [sys.executable, '-m', 'oasm', source, target, '--rewrite', *sys.argv[1::]],
                capture_output=True,
                text=True
            )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Error in {file}:\n{result.stderr}")
