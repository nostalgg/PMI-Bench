"""Validate published seed databases/JSON/CSV inside the pinned offline container."""
import json
import subprocess
import tempfile
import uuid
from pathlib import Path

from pmi_bench import runner


PROBE = '''import csv,json,sqlite3
from pathlib import Path
root=Path('/submission')
databases=[]
for schema in sorted(root.glob('*/workspace/schema.sql')):
    with sqlite3.connect(':memory:') as connection:
        connection.executescript(schema.read_text())
        seed=schema.parent/'seed.sql'
        if seed.is_file():
            connection.executescript(seed.read_text())
        databases.append(schema.parent.parent.name)
stores=[]
for schema in sorted(root.glob('*/workspace/fixtures/store.sql')):
    with sqlite3.connect(':memory:') as connection:
        connection.executescript(schema.read_text())
    stores.append(schema.parent.parent.parent.name)
json_files=list(root.glob('*/workspace/**/*.json'))
for path in json_files:
    json.loads(path.read_text())
for task,delimiter,columns in [('supplier_catalog',';',['sku','description','cost_cents','active']),
                               ('cli_csv_export',',',['id','amount_cents'])]:
    with (root/task/'workspace/sample.csv').open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream,delimiter=delimiter)
        assert reader.fieldnames==columns
        assert len(list(reader))>0
with (root/'invoice_import/workspace/sample.csv').open(newline='') as stream:
    reader=csv.DictReader(stream)
    assert {'invoice_id','customer_id','amount_cents','status'}<=set(reader.fieldnames)
    assert len(list(reader))>0
print(json.dumps({'seed_databases':databases,'integrated_store_fixtures':stores,'json_files_validated':len(json_files),'source_csv_files_validated':3}))
'''


def main():
    runtime = runner.read_json(runner.DEFAULT_ROOT / 'runtime.json')
    with tempfile.TemporaryDirectory(prefix='pmi-fixture-check-') as temporary:
        root = Path(temporary)
        root.chmod(0o755)
        runner.stage_readonly(runner.DEFAULT_ROOT / 'tasks', root / 'submission')
        evaluator = root / 'evaluator'
        evaluator.mkdir(mode=0o755)
        evaluator.chmod(0o755)
        (evaluator / 'worker.py').write_text(PROBE)
        (evaluator / 'worker.py').chmod(0o444)
        name = 'pmi-fixtures-' + uuid.uuid4().hex
        try:
            result = subprocess.run(runner.docker_command(runtime, name, root / 'submission', evaluator),
                                    capture_output=True, text=True, timeout=45)
            if result.returncode:
                raise RuntimeError(result.stderr[-2000:])
            evidence = json.loads(result.stdout)
            assert len(evidence['seed_databases']) == 8
            assert len(evidence['integrated_store_fixtures']) == len(runner.list_tasks(runner.DEFAULT_ROOT))
            expected_json = list((runner.DEFAULT_ROOT/'tasks').glob('*/workspace/**/*.json'))
            assert evidence['json_files_validated'] == len(expected_json)
            print(json.dumps(evidence))
        finally:
            subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=10)


if __name__ == '__main__':
    main()
