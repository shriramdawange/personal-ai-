import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

class DatabaseTests(unittest.TestCase):
    def test_task_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('empire.db.settings', SimpleNamespace(db_path=Path(tmp) / 'test.db')):
                from empire import db
                db.init_db()
                task_id = db.add_task('Test task', 'description')
                task = db.get_task(task_id)
                self.assertEqual(task['title'], 'Test task')
                self.assertEqual(task['status'], 'queued')
                db.update_task(task_id, status='succeeded')
                self.assertEqual(db.get_task(task_id)['status'], 'succeeded')

if __name__ == '__main__': unittest.main()
