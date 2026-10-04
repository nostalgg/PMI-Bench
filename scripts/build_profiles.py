"""Download checksum-verified wheels and build supplementary runtime offline."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    config = json.loads((ROOT/'profiles/runtime.json').read_text())
    lock = ROOT/'profiles/requirements.lock'
    checksum = hashlib.sha256(lock.read_bytes()).hexdigest()
    if checksum != config['requirements_sha256']: raise RuntimeError('Profile dependency lock changed')
    subprocess.run(['docker','pull',config['postgres_image']],check=True)
    with tempfile.TemporaryDirectory(prefix='pmi-profile-build-') as temporary:
        folder = Path(temporary)
        for name in ['Dockerfile','requirements.lock']: shutil.copyfile(ROOT/'profiles'/name,folder/name)
        subprocess.run(['uv','run','--with','pip','python','-m','pip','download','--no-cache-dir','--require-hashes','-r',str(lock),'--only-binary=:all:','--dest',str(folder/'wheels')],cwd=ROOT,check=True)
        environment = os.environ.copy()
        # Buildx needs writable client state in restricted cloud workspaces.
        environment['DOCKER_CONFIG'] = str(folder/'docker-config')
        subprocess.run(['docker','build','--network=none','--build-arg','BASE_IMAGE='+config['base_image'],'--label','org.pmi-bench.requirements-sha256='+checksum,'--tag',config['profile_image'],str(folder)],env=environment,check=True)


if __name__ == '__main__': main()
