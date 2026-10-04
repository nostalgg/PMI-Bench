import importlib
import sqlite3
import unittest


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.migrate = importlib.import_module('migration').migrate
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.executescript("CREATE TABLE orders(id TEXT PRIMARY KEY, status TEXT NOT NULL);"
                              "INSERT INTO orders VALUES ('001','paid'),('002','pending');"
                              "PRAGMA user_version=1;")

    def test_upgrade_preserves_data(self):
        self.migrate(self.db)
        self.assertEqual(self.db.execute('SELECT * FROM orders ORDER BY id').fetchall(),
                         [('001', 'paid', 'EUR'), ('002', 'pending', 'EUR')])
        self.assertEqual(self.db.execute('PRAGMA user_version').fetchone()[0], 2)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO orders VALUES ('003','paid',NULL)")

    def test_idempotence_preserves_currency(self):
        self.migrate(self.db)
        self.db.execute("UPDATE orders SET currency='USD' WHERE id='001'")
        self.db.commit()
        self.migrate(self.db)
        self.assertEqual(self.db.execute("SELECT currency FROM orders WHERE id='001'").fetchone()[0], 'USD')

    def test_preserves_database_objects(self):
        self.db.executescript('CREATE INDEX orders_status ON orders(status);'
                              'CREATE VIEW paid AS SELECT id FROM orders WHERE status="paid";'
                              'CREATE TABLE unrelated(value TEXT); INSERT INTO unrelated VALUES("keep");')
        self.migrate(self.db)
        self.assertEqual(self.db.execute('SELECT * FROM paid').fetchall(), [('001',)])
        self.assertEqual(self.db.execute('SELECT * FROM unrelated').fetchall(), [('keep',)])
        self.assertEqual(self.db.execute("SELECT count(*) FROM sqlite_master WHERE name='orders_status'").fetchone()[0], 1)

    def test_constraint_future_version_unchanged(self):
        self.db.execute('PRAGMA user_version=3')
        before = list(self.db.iterdump())
        with self.assertRaises(ValueError):
            self.migrate(self.db)
        self.assertEqual(list(self.db.iterdump()), before)
        other = sqlite3.connect(':memory:')
        self.addCleanup(other.close)
        other.execute('PRAGMA user_version=1')
        with self.assertRaises(ValueError):
            self.migrate(other)

    def test_constraint_caller_transaction_preserved(self):
        self.db.execute("UPDATE orders SET status='cancelled' WHERE id='001'")
        with self.assertRaises(ValueError):
            self.migrate(self.db)
        self.assertTrue(self.db.in_transaction)
        self.db.rollback()
        self.assertEqual(self.db.execute("SELECT status FROM orders WHERE id='001'").fetchone()[0], 'paid')



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'version': 2, 'orders': [['001', 'paid', 'EUR']]}})
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
