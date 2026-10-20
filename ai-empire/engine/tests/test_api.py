import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Importing the app initializes the local SQLite schema.
from empire.api import app

class ApiTests(unittest.TestCase):
    def test_health_endpoint(self):
        client = TestClient(app)
        response = client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])

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
