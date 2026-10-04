"""Supplementary candidate tests against real PostgreSQL/pandas/sklearn dependencies."""
import contextlib
import importlib
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, '/evaluator')
tempfile.tempdir = '/scratch'
from isolated_client import install
install(json.loads(Path('/control/task.json').read_text()))
TASK = sys.argv[1]


class PostgreSQL:
    """Small documented SQLite-style binding adapter; not a general SQL translator."""
    def __init__(self, schema):
        import psycopg
        administrator = psycopg.connect('host=pmi-database dbname=benchmark user=benchmark password=synthetic-fixture-only', autocommit=True)
        with administrator:
            administrator.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public')
            administrator.execute(schema)
            if administrator.execute("SELECT 1 FROM pg_roles WHERE rolname='candidate_fixture'").fetchone() is None:
                administrator.execute("CREATE ROLE candidate_fixture LOGIN PASSWORD 'synthetic-restricted-fixture'")
            administrator.execute('REVOKE CREATE ON SCHEMA public FROM PUBLIC; GRANT USAGE ON SCHEMA public TO candidate_fixture; GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO candidate_fixture')
        self.connection = psycopg.connect('host=pmi-database dbname=benchmark user=candidate_fixture password=synthetic-restricted-fixture',
                                          autocommit=True, options='-c statement_timeout=5000 -c lock_timeout=5000')

    @property
    def in_transaction(self):
        from psycopg.pq import TransactionStatus
        return self.connection.info.transaction_status != TransactionStatus.IDLE

    def validate_sql(self, sql):
        import re
        if ';' in sql or not re.match(r'^\s*(SELECT|INSERT|UPDATE|DELETE|BEGIN|COMMIT|ROLLBACK)\b',sql,re.I):
            from isolated_client import session
            session.violations.append('Unauthorized PostgreSQL fixture SQL capability')
            raise ValueError('Fixture SQL operation is outside the profile contract')

    def execute(self, sql, parameters=None):
        self.validate_sql(sql)
        return self.connection.execute(sql.replace('?', '%s'), parameters)

    def executemany(self, sql, parameters):
        self.validate_sql(sql)
        with self.connection.cursor() as cursor:
            cursor.executemany(sql.replace('?', '%s'), parameters)

    def commit(self):
        self.connection.execute('COMMIT')

    def rollback(self):
        self.connection.execute('ROLLBACK')

    def close(self):
        self.connection.close()


class Inventory(unittest.TestCase):
    def setUp(self):
        self.db = PostgreSQL('CREATE TABLE stock(sku TEXT PRIMARY KEY,quantity BIGINT NOT NULL); CREATE TABLE movements(event_id TEXT PRIMARY KEY,sku TEXT,delta BIGINT); INSERT INTO stock VALUES(\'001\',10)')
        self.addCleanup(self.db.close)
        self.apply = importlib.import_module('ledger').apply_movements
        self.move = {'event_id':'delivery','sku':'001','delta':5}

    def test_replay(self):
        self.assertEqual(self.apply(self.db,[self.move]),1)
        self.assertEqual(self.apply(self.db,[self.move]),0)
        self.assertEqual(self.db.execute('SELECT quantity FROM stock').fetchone(),(15,))

    def test_conflict(self):
        self.apply(self.db,[self.move])
        with self.assertRaises(ValueError): self.apply(self.db,[{**self.move,'delta':6}])
        self.assertEqual(self.db.execute('SELECT quantity FROM stock').fetchone(),(15,))

    def test_rollback(self):
        with self.assertRaises(ValueError): self.apply(self.db,[self.move,{**self.move,'event_id':'invalid','sku':'missing'}])
        self.assertEqual(self.db.execute('SELECT quantity FROM stock').fetchone(),(10,))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM movements').fetchone(),(0,))


class Sync(unittest.TestCase):
    def setUp(self):
        self.db = PostgreSQL("CREATE TABLE replica(record_id TEXT PRIMARY KEY,value TEXT NOT NULL CHECK(value <> 'fail')); CREATE TABLE checkpoint(singleton INTEGER PRIMARY KEY,sequence BIGINT NOT NULL); INSERT INTO checkpoint VALUES(1,0)")
        self.addCleanup(self.db.close)
        self.apply = importlib.import_module('sync').apply_changes
        self.event = {'sequence':1,'record_id':'001','operation':'upsert','value':'ok'}

    def test_replay(self):
        self.assertEqual(self.apply(self.db,[self.event]),1)
        self.assertEqual(self.apply(self.db,[self.event]),0)

    def test_order_and_delete(self):
        self.assertEqual(self.apply(self.db,[{**self.event,'sequence':2,'operation':'delete','value':None},self.event]),2)
        self.assertEqual(self.db.execute('SELECT * FROM replica').fetchall(),[])
        self.assertEqual(self.db.execute('SELECT sequence FROM checkpoint').fetchone(),(2,))

    def test_checkpoint_rollback(self):
        with self.assertRaises(Exception): self.apply(self.db,[self.event,{**self.event,'sequence':2,'record_id':'002','value':'fail'}])
        self.assertEqual(self.db.execute('SELECT * FROM replica').fetchall(),[])
        self.assertEqual(self.db.execute('SELECT sequence FROM checkpoint').fetchone(),(0,))


class History(unittest.TestCase):
    def setUp(self):
        self.db = PostgreSQL("CREATE TABLE customer_history(customer_id TEXT,name TEXT,valid_from TEXT,valid_to TEXT); INSERT INTO customer_history VALUES('001','Workshop','2024-01-01',NULL)")
        self.addCleanup(self.db.close)
        self.apply = importlib.import_module('history').apply_snapshot

    def test_change(self):
        self.assertEqual(self.apply(self.db,[{'customer_id':'001','name':'New'}],'2024-02-01'),1)
        self.assertEqual(self.db.execute('SELECT name,valid_to FROM customer_history ORDER BY valid_from').fetchall(),[('Workshop','2024-02-01'),('New',None)])

    def test_close_absent(self):
        self.assertEqual(self.apply(self.db,[],'2024-02-01'),1)
        self.assertEqual(self.db.execute('SELECT valid_to FROM customer_history').fetchone(),('2024-02-01',))

    def test_replay_and_late(self):
        self.assertEqual(self.apply(self.db,[{'customer_id':'001','name':'Workshop'}],'2024-02-01'),0)
        with self.assertRaises(ValueError): self.apply(self.db,[],'2023-12-31')
        self.assertEqual(self.db.execute('SELECT valid_to FROM customer_history').fetchone(),(None,))


class Enrichment(unittest.TestCase):
    def setUp(self):
        self.db = PostgreSQL('CREATE TABLE enrichment(record_id TEXT PRIMARY KEY,input_sha256 TEXT,label TEXT,model TEXT)')
        self.addCleanup(self.db.close)
        self.apply = importlib.import_module('enrichment').enrich_documents
        self.rows = [{'record_id':'001','text':'invoice'},{'record_id':'002','text':'credit_note'}]

    def classify(self, rows):
        return {'model':'private','results':[{'record_id':r['record_id'],'label':r['text']} for r in reversed(rows)]}

    def test_alignment(self):
        self.assertEqual(self.apply(self.db,self.rows,self.classify,'private'),2)
        self.assertEqual(self.db.execute('SELECT record_id,label FROM enrichment ORDER BY record_id').fetchall(),[('001','invoice'),('002','credit_note')])

    def test_changed_input(self):
        self.apply(self.db,self.rows,self.classify,'private')
        self.assertEqual(self.apply(self.db,[{**self.rows[0],'text':'other'}],self.classify,'private'),1)
        self.assertEqual(self.db.execute("SELECT label FROM enrichment WHERE record_id='001'").fetchone(),('other',))

    def test_no_replay_call(self):
        self.apply(self.db,self.rows,self.classify,'private')
        def forbidden(_): raise AssertionError('cached rows must not call model')
        self.assertEqual(self.apply(self.db,self.rows,forbidden,'private'),0)


class Supplier(unittest.TestCase):
    def setUp(self):
        import pandas as pd
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name); self.db = self.directory/'catalog.sqlite'
        with sqlite3.connect(self.db) as connection:
            connection.executescript(Path('/submission/schema.sql').read_text())
            connection.execute("INSERT INTO products VALUES('001','old',100,999,1)")
        self.csv = self.directory/'supplier.csv'
        # Existing spreadsheet/DataFrame producer preserves identifiers as strings.
        pd.DataFrame([{'sku':'001','description':'updated','cost_cents':'250','active':'0'}]).to_csv(self.csv,sep=';',index=False,encoding='utf-8-sig')
        self.apply = importlib.import_module('catalog').import_catalog

    def row(self):
        with sqlite3.connect(self.db) as connection: return connection.execute('SELECT * FROM products').fetchone()

    def test_dataframe_producer(self):
        self.assertEqual(self.apply(self.csv,self.db),1)
        self.assertEqual(self.row(),('001','updated',250,999,0))

    def test_replay(self):
        self.apply(self.csv,self.db); self.apply(self.csv,self.db)
        self.assertEqual(self.row()[0],'001'); self.assertEqual(self.row()[3],999)

    def test_bad_batch(self):
        import pandas as pd
        pd.DataFrame([{'sku':'001','description':'wrong','cost_cents':'-5','active':'0'}]).to_csv(self.csv,sep=';',index=False)
        with self.assertRaises(ValueError): self.apply(self.csv,self.db)
        self.assertEqual(self.row(),('001','old',100,999,1))


class Features(unittest.TestCase):
    def setUp(self):
        import pandas as pd
        self.frame = pd.DataFrame([
            {'id':'001','date':'2024-01-01','orders':2,'spend_cents':100,'target':10},
            {'id':'002','date':'2024-01-02','orders':4,'spend_cents':300,'target':20},
            {'id':'003','date':'2024-02-01','orders':None,'spend_cents':99999,'target':None},
        ],dtype=object)
        self.apply = importlib.import_module('features').prepare_features
        self.result = self.apply(self.frame.where(self.frame.notna(),None).to_dict('records'),'2024-02-01')

    def test_training_imputer_agreement(self):
        from sklearn.impute import SimpleImputer
        columns = ['orders','spend_cents']
        imputer = SimpleImputer(strategy='median').fit(self.frame.loc[self.frame.date < '2024-02-01',columns].astype(float))
        self.assertEqual(imputer.statistics_.tolist(),[self.result['medians'][c] for c in columns])
        expected = imputer.transform(self.frame.loc[self.frame.date >= '2024-02-01',columns].astype(float)).tolist()[0]
        self.assertEqual(expected,[self.result['test'][0]['features'][c] for c in columns])

    def test_downstream_pipeline(self):
        import pandas as pd
        from sklearn.dummy import DummyRegressor
        train = pd.DataFrame([r['features'] for r in self.result['train']])
        test = pd.DataFrame([r['features'] for r in self.result['test']])
        self.assertEqual(list(train.columns),['orders','spend_cents'])
        prediction = DummyRegressor(strategy='mean').fit(train,[r['target'] for r in self.result['train']]).predict(test)
        self.assertEqual(prediction.tolist(),[15.0])

    def test_cutoff_and_labels(self):
        self.assertEqual([r['id'] for r in self.result['train']],['001','002'])
        self.assertEqual(self.result['test'][0]['target'],None)
        self.assertNotIn('target',self.result['test'][0]['features'])


CLASSES = {'inventory_ledger':Inventory,'incremental_sync':Sync,'scd_history':History,'document_cache':Enrichment,'supplier_catalog':Supplier,'temporal_features':Features}
if TASK not in CLASSES: raise ValueError('Unsupported profile task')
result = unittest.TestResult()
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    unittest.defaultTestLoader.loadTestsFromTestCase(CLASSES[TASK]).run(result)
failures = [{'test':t.id().rsplit('.',1)[-1],'detail':detail[-1600:]} for t,detail in result.failures+result.errors]
from isolated_client import session
if session.violations: failures.append({'test':'test_constraint_judge_boundary','detail':'; '.join(session.violations)[:1000]})
accepted = result.testsRun==3 and result.wasSuccessful() and not session.violations
print(json.dumps({'task_id':TASK,'tests_run':result.testsRun+1,'failures':failures,'accepted':accepted}))
raise SystemExit(0 if accepted else 1)
