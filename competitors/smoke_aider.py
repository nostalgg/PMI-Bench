"""Replay a fixture through Aider's real edit engine; no inference/performance score."""
import argparse
import subprocess
import tempfile
from pathlib import Path

from run import aider_command


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python', type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='pmi-aider-smoke-') as temporary:
        root = Path(temporary)
        workspace, logs = root / 'workspace', root / 'logs'
        workspace.mkdir()
        logs.mkdir()
        (workspace / 'probe.py').write_text('value = 1\n')
        (workspace / 'PROJECT.md').write_text('Edit only probe.py.\n')
        (logs / 'empty-config.yml').write_text('{}\n')
        settings = logs / 'model-settings.yml'
        settings.write_text('[]\n')
        replay = logs / 'fixture.txt'
        replay.write_text('probe.py\n```python\n<<<<<<< SEARCH\nvalue = 1\n=======\nvalue = 2\n>>>>>>> REPLACE\n```\n')
        # Bundled metadata label only: --apply invokes no model API.
        command = aider_command(args.python.absolute(), 'gpt-4o-mini', workspace,
                                {'editable_files': ['probe.py']}, replay, logs, settings, 'execute')
        index = command.index('--message-file')
        command[index:index+2] = ['--apply', str(replay)]
        result = subprocess.run(command, cwd=workspace, text=True, capture_output=True, timeout=60)
        if result.returncode or (workspace / 'probe.py').read_text() != 'value = 2\n':
            raise RuntimeError('Aider replay failed: ' + result.stdout[-2000:] + result.stderr[-2000:])
        assert (workspace / 'PROJECT.md').read_text() == 'Edit only probe.py.\n'
        assert sorted(p.name for p in workspace.iterdir()) == ['PROJECT.md', 'probe.py']
    print('Aider integration passed: fixture applied by real edit engine; protected context preserved; no inference.')


if __name__ == '__main__':
    main()
