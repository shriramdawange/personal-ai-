import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class OrchestratorIntegrationTests(unittest.TestCase):
    def _settings(self, tmp):
        return SimpleNamespace(
            db_path=Path(tmp) / "data" / "empire.db",
            workspace=Path(tmp) / "workspace",
            max_revisions=1,
            stale_task_minutes=60,
            poll_seconds=3,
            ollama_model="test-model",
        )

    def test_task_runs_through_plan_specialist_qa_and_saved_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self._settings(tmp)
            with patch("empire.db.settings", settings), patch(
                "empire.orchestrator.settings", settings
            ):
                from empire import db
                from empire.orchestrator import Orchestrator

                db.init_db()
                task_id = db.add_task("Build a demo", "Make a small test deliverable")
                with patch("empire.orchestrator.ceo_plan", return_value="Plan with acceptance checks"), patch(
                    "empire.orchestrator.execute_specialist", return_value="A completed deliverable"
                ), patch("empire.orchestrator.quality_review", return_value="QA_STATUS: PASS\nLooks good"), patch(
                    "empire.orchestrator.materialize_files", return_value={"files": [], "directory": "unused"}
                ), patch("empire.orchestrator.validate_artifacts", return_value=[]):
                    result = Orchestrator().run_task(task_id)

                self.assertEqual(result["status"], "succeeded")
                report = Path(result["result_path"])
                self.assertTrue(report.is_file())
                report_text = report.read_text(encoding="utf-8")
                self.assertIn("## CEO plan", report_text)
                self.assertIn("Plan with acceptance checks", report_text)
                self.assertIn("A completed deliverable", report_text)
                self.assertIn("QA_STATUS: PASS", report_text)
                self.assertEqual(db.events(task_id)[-1]["event"], "task_finished")

    def test_task_gets_one_bounded_revision_when_qa_requests_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self._settings(tmp)
            with patch("empire.db.settings", settings), patch(
                "empire.orchestrator.settings", settings
            ):
                from empire import db
                from empire.orchestrator import Orchestrator

                db.init_db()
                task_id = db.add_task("Revise a demo")
                reviews = [
                    "QA_STATUS: REVISE\nAdd acceptance criteria",
                    "QA_STATUS: PASS\nCriteria are present",
                ]
                with patch("empire.orchestrator.ceo_plan", return_value="Plan"), patch(
                    "empire.orchestrator.execute_specialist", return_value="First draft"
                ), patch("empire.orchestrator.quality_review", side_effect=reviews), patch(
                    "empire.orchestrator.revise_output", return_value="Revised draft"
                ) as revise, patch(
                    "empire.orchestrator.materialize_files", return_value={"files": [], "directory": "unused"}
                ), patch("empire.orchestrator.validate_artifacts", return_value=[]):
                    result = Orchestrator().run_task(task_id)

                self.assertEqual(result["status"], "succeeded")
                revise.assert_called_once()
                report = Path(result["result_path"]).read_text(encoding="utf-8")
                self.assertIn("Revised draft", report)
                self.assertTrue(any(e["event"] == "revision_ready" for e in db.events(task_id)))


if __name__ == "__main__":
    unittest.main()
