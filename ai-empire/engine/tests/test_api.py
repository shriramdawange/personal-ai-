import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Importing the app initializes the local SQLite schema.
from empire.api import app

class ApiTests(unittest.TestCase):
    def test_health_endpoint(self):
        client = TestClient(app)
        response = client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])

    def test_dashboard_is_served_from_api(self):
        response = TestClient(app).get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('AI EMPIRE', response.text)

    def test_artifact_endpoint_serves_workspace_file(self):
        from empire import api
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            workspace.mkdir()
            artifact = workspace / "result.md"
            artifact.write_text("# Test deliverable", encoding="utf-8")
            with patch("empire.api.settings", SimpleNamespace(workspace=workspace)), patch(
                "empire.api.get_task",
                return_value={"id": 77, "result_path": str(artifact)},
            ):
                response = TestClient(app).get("/tasks/77/artifact")
            self.assertEqual(response.status_code, 200)
            self.assertIn("# Test deliverable", response.text)
            self.assertIn("attachment", response.headers.get("content-disposition", ""))

    def test_artifact_endpoint_rejects_path_outside_workspace(self):
        from empire import api
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            workspace.mkdir()
            outside = Path(tmp) / "secret.txt"
            outside.write_text("not an artifact", encoding="utf-8")
            with patch("empire.api.settings", SimpleNamespace(workspace=workspace)), patch(
                "empire.api.get_task",
                return_value={"id": 78, "result_path": str(outside)},
            ):
                response = TestClient(app).get("/tasks/78/artifact")
            self.assertEqual(response.status_code, 403)

    def test_system_status_reports_local_model(self):
        response_obj = Mock()
        response_obj.json.return_value = {'models': [{'name': 'qwen2.5-coder:3b'}]}
        with patch('empire.api.requests.get', return_value=response_obj):
            response = TestClient(app).get('/system/status')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ollama']['reachable'])
        self.assertTrue(response.json()['ollama']['model_available'])

    def test_model_smoke_test_runs_real_inference_adapter(self):
        with patch("empire.api.chat", return_value="EMPIRE_MODEL_OK"):
            response = TestClient(app).post("/system/model-test", json={})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(response.json()["model"], "qwen2.5-coder:3b")

    def test_model_smoke_test_reports_unavailable_model(self):
        with patch("empire.api.chat", side_effect=RuntimeError("Ollama unavailable")):
            response = TestClient(app).post("/system/model-test", json={})
        self.assertEqual(response.status_code, 502)
        self.assertIn("Ollama unavailable", response.json()["detail"])

    def test_remote_bind_requires_strong_token(self):
        from empire.api import verify_access
        with patch.dict(os.environ, {'EMPIRE_API_HOST': '0.0.0.0', 'EMPIRE_API_TOKEN': 'short'}):
            with self.assertRaises(Exception) as caught:
                verify_access(None)
            self.assertEqual(getattr(caught.exception, 'status_code', None), 503)

    def test_remote_bind_rejects_missing_bearer(self):
        from empire.api import verify_access
        with patch.dict(os.environ, {'EMPIRE_API_HOST': '0.0.0.0', 'EMPIRE_API_TOKEN': 'this-is-a-long-test-token-123456'}):
            with self.assertRaises(Exception) as caught:
                verify_access(None)
            self.assertEqual(getattr(caught.exception, 'status_code', None), 401)

if __name__ == '__main__':
    unittest.main()
