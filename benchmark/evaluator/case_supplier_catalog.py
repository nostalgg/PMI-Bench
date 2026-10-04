import csv
import importlib
import sqlite3
import tempfile
import unittest
from pathlib import Path


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.importer = importlib.import_module('catalog').import_catalog
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source, self.db = self.root/'supplier.csv', self.root/'catalog.db'
        with sqlite3.connect(self.db) as conn:
            conn.executescript(Path('/submission/schema.sql').read_text())
            conn.execute("INSERT INTO products VALUES('001','Old',100,999,1)")
            conn.execute("INSERT INTO products VALUES('keep','Manual',200,500,1)")

    def write(self, rows):
        with self.source.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.writer(stream, delimiter=';')
            writer.writerow(['sku','description','cost_cents','active'])
            writer.writerows(rows)

    def rows(self):
        with sqlite3.connect(self.db) as conn:
            return conn.execute('SELECT * FROM products ORDER BY sku').fetchall()

    def test_bom_dialect_and_string_sku(self):
        self.write([('0002','Part; "B"','29','1')])
        self.assertEqual(self.importer(self.source,self.db),1)
        self.assertIn(('0002','Part; "B"',29,None,1),self.rows())

    def test_manual_price_preserved(self):
        self.write([('001','New', '250','0')])
        self.importer(self.source,self.db)
        self.assertIn(('001','New',250,999,0),self.rows())

    def test_absent_products_preserved(self):
        self.write([('001','New','100','1')])
        self.importer(self.source,self.db)
        self.assertIn(('keep','Manual',200,500,1),self.rows())

    def test_constraint_bad_batch_atomic(self):
        before=self.rows()
        for bad in [('bad','X','-1','1'),('bad','X','1','true'),('001','X','1','1'),('bad','X',str(2**63),'1')]:
            self.write([('001','Changed','1','0'),bad])
            with self.assertRaises(ValueError):
                self.importer(self.source,self.db)
            self.assertEqual(self.rows(),before)

    def test_repeat_is_idempotent(self):
        self.write([('001','New','400','1'),("q'","quoted",'0','0')])
        self.importer(self.source,self.db)
        before=self.rows()
        self.assertEqual(self.importer(self.source,self.db),2)
        self.assertEqual(self.rows(),before)

    def test_constraint_header_validation(self):
        self.source.write_text('sku;cost_cents\nX;1\n')
        before=self.rows()
        with self.assertRaises(ValueError):
            self.importer(self.source,self.db)
        self.assertEqual(self.rows(),before)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'imported': 1, 'products': [['001', 'Replacement', 250, 999, 0], ['keep', 'Manual-only', 200, 500, 1]]}})
            self.assertEqual(json.loads((Path(temporary)/'result.json').read_text()), canonical)

    def test_constraint_workflow_failure_preserves_last_result(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary)/'result.json'
            artifact.write_text('last-valid-result')
            job = json.loads(Path('/submission/fixtures/rejected-job.json').read_text())
            receipt = consume(job, temporary)
            self.assertEqual(receipt, {'job_id': job['job_id'], 'status': 'failed', 'result': None})
            self.assertEqual(artifact.read_text(), 'last-valid-result')

    def test_constraint_workflow_failed_followup(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            good = json.loads(Path('/submission/fixtures/job.json').read_text())
            bad = json.loads(Path('/submission/fixtures/rejected-job.json').read_text())
            self.assertEqual(consume(good, temporary)['status'], 'completed')
            artifact = Path(temporary)/'result.json'
            previous = artifact.read_bytes()
            self.assertEqual(consume(bad, temporary), {'job_id': bad['job_id'], 'status': 'failed', 'result': None})
            self.assertEqual(artifact.read_bytes(), previous)
