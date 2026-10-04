"""Operator-side approval records, never mounted in agent/tool containers."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets

from .runner import BenchmarkError, inventory


def canonical(binding):return json.dumps(binding,sort_keys=True,separators=(',',':')).encode()


def approve(directory, binding):
    private=Path(directory)/'controller'
    if private.exists():raise BenchmarkError('Approval already recorded; use a fresh run for a new attempt')
    private.mkdir(mode=0o700);private.chmod(0o700)
    key=secrets.token_bytes(32)
    with (private/'key').open('xb') as stream:stream.write(key)
    (private/'key').chmod(0o600)
    record={'binding':binding,'signature':hmac.new(key,canonical(binding),hashlib.sha256).hexdigest(),
            'authority':'explicit_operator_command_not_authenticated_identity'}
    with (private/'approval.json').open('x') as stream:json.dump(record,stream)
    (private/'approval.json').chmod(0o600)
    return record['authority']


def consume(directory,binding):
    private=Path(directory)/'controller'
    try:
        for name in ['key','approval.json']:
            if (private/name).is_symlink():raise BenchmarkError('Invalid controller record')
        key=(private/'key').read_bytes();record=json.loads((private/'approval.json').read_text())
    except (OSError,ValueError) as exc:raise BenchmarkError('Explicit operator approval has not been recorded') from exc
    expected=hmac.new(key,canonical(binding),hashlib.sha256).hexdigest()
    if record.get('binding')!=binding or not hmac.compare_digest(record.get('signature',''),expected):
        raise BenchmarkError('Approval does not match the current plan/request/workspace')
    try:
        with (private/'consumed').open('x') as stream:stream.write('One implementation attempt authorized.\n')
    except FileExistsError as exc:raise BenchmarkError('Approval already consumed; execution replay refused') from exc


def workspace_mounts(workspace,editable_files,mode):
    """A read-only directory plus writable existing file mounts prevents transient edits."""
    workspace=Path(workspace).resolve();files=inventory(workspace)
    if mode not in {'plan','execute'} or not set(editable_files)<=set(files):raise BenchmarkError('Invalid sandbox scope')
    for path in [workspace,*workspace.rglob('*')]:
        path.chmod(0o755 if path.is_dir() else (0o666 if mode=='execute' and path.relative_to(workspace).as_posix() in editable_files else 0o444))
    mounts=['--mount',f'type=bind,src={workspace},dst=/workspace,readonly']
    if mode=='execute':
        for name in editable_files:mounts+=['--mount',f'type=bind,src={workspace/name},dst=/workspace/{name}']
    return mounts
