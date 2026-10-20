import os
import unittest
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

    def test_system_status_reports_local_model(self):
        response_obj = Mock()
        response_obj.json.return_value = {'models': [{'name': 'qwen2.5-coder:3b'}]}
        with patch('empire.api.requests.get', return_value=response_obj):
            response = TestClient(app).get('/system/status')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ollama']['reachable'])
        self.assertTrue(response.json()['ollama']['model_available'])

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
