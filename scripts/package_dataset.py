"""Create a deterministic, hash-verified publication-draft ZIP without uploading."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from pmi_bench import runner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    manifest = runner.read_json(args.directory / 'export-manifest.json')
    current = runner.dataset_inventory(args.directory)
    actual_manifest_hash = current.pop('export-manifest.json')
    if manifest['files'] != current:
        raise runner.BenchmarkError('Export contents differ from their manifest')
    if args.output.exists():
        raise runner.BenchmarkError('ZIP already exists; refusing overwrite')
    if any('/references/' in name or name.startswith(('references/', 'evaluator/')) for name in current):
        raise runner.BenchmarkError('Export contains evaluation answers or code')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    names = sorted([*current, 'export-manifest.json'])
    with zipfile.ZipFile(args.output, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            info = zipfile.ZipInfo(name, date_time=(2026,10,4,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            data = (args.directory / name).read_bytes()
            expected = actual_manifest_hash if name == 'export-manifest.json' else current[name]
            if hashlib.sha256(data).hexdigest() != expected:
                raise runner.BenchmarkError('Export changed during packaging')
            archive.writestr(info, data)
    print(json.dumps({'zip':str(args.output),'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),
                      'files':len(names),'published':False}))


if __name__ == '__main__':
    main()
