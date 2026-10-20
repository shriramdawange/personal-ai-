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
                self.assertTrue(db.claim_task(task_id))
                self.assertFalse(db.claim_task(task_id), 'A running task must not be claimed twice')
                db.update_task(task_id, status='succeeded')
                self.assertEqual(db.get_task(task_id)['status'], 'succeeded')

    def test_lead_project_invoice_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('empire.db.settings', SimpleNamespace(db_path=Path(tmp) / 'test.db')):
                from empire import db
                db.init_db()
                db.save_lead({'name':'Example','url':'https://example.org','fit_score':72,'rationale':'Evidence','outreach_draft':'Hello'})
                lead = db.list_leads()[0]
                self.assertTrue(db.update_lead_status(lead['id'], 'qualified', 'Reviewed manually'))
                project_id = db.create_project('Pilot website', 'Build and test a landing page', lead['id'], 2500000)
                self.assertEqual(db.list_projects()[0]['status'], 'proposed')
                self.assertTrue(db.update_project_status(project_id, 'active'))
                invoice_id = db.create_invoice(project_id, 'Pilot milestone', 500000, '2026-11-01')
                self.assertIsNotNone(invoice_id)
                self.assertEqual(db.list_invoices()[0]['amount_paise'], 500000)

if __name__ == '__main__':
    unittest.main()
