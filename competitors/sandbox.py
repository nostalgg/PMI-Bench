"""Native Aider model/edit process in Docker; no controller/evaluator mounts."""
from pathlib import Path
import uuid

from pmi_bench import control,runner


def aider_container_command(command,python,workspace,logs,task,mode,*,network='bridge'):
    dependencies=python.parent.parent/'lib/python3.12/site-packages'
    if not dependencies.is_dir():raise runner.BenchmarkError('Pinned Python 3.12 Aider venv required')
    # uv may install with a private umask; the nonroot Docker process needs read access.
    # Only trusted installed dependency permissions change, never source bytes.
    for path in [dependencies,*dependencies.rglob('*')]:
        if not path.is_symlink():path.chmod(0o755 if path.is_dir() else 0o644)
    translated=[]
    for argument in command:
        if argument==str(python):argument='/usr/local/bin/python'
        elif argument.startswith(str(workspace)+'/'):argument='/workspace/'+argument[len(str(workspace))+1:]
        elif argument.startswith(str(logs)+'/'):argument='/logs/'+argument[len(str(logs))+1:]
        translated.append(argument)
    logs.chmod(0o777)
    for path in logs.rglob('*'):
        path.chmod(0o777 if path.is_dir() else 0o666)
    result=['docker','run','--rm','--pull=never','--name','pmi-aider-'+uuid.uuid4().hex,'--read-only','--user','65534:65534',
            '--network='+network,'--cap-drop=ALL','--security-opt=no-new-privileges',
            '--pids-limit','128','--memory','768m','--memory-swap','768m','--cpus','1',
            '--tmpfs','/tmp:rw,nosuid,nodev,size=134217728,mode=1777',
            '--workdir','/workspace','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/dependencies',
            '--env','GIT_PYTHON_REFRESH=quiet',
            '--env','HOME=/tmp','--env','OPENROUTER_API_KEY',
            '--mount',f'type=bind,src={dependencies},dst=/dependencies,readonly',
            '--mount',f'type=bind,src={logs},dst=/logs',
            *control.workspace_mounts(workspace,task['editable_files'],mode)]
    # Proxy variables remain process environment values, never interpolated in shell/logs.
    import os
    for name in ['HTTPS_PROXY','HTTP_PROXY','ALL_PROXY','NO_PROXY']:
        if name in os.environ:result+=['--env',name]
    return result+[runner.read_json(runner.DEFAULT_ROOT/'runtime.json')['image'],*translated]
