import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from empire.delivery import materialize_files, validate_artifacts

class DeliveryTests(unittest.TestCase):
    def test_materializes_explicit_python_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('empire.delivery.settings', SimpleNamespace(workspace=Path(tmp))):
                output = "FILE: hello.py\n```python\nprint('hello')\n```"
                result = materialize_files(7, output)
                self.assertEqual(len(result['files']), 1)
                path = Path(result['files'][0])
                self.assertTrue(path.exists())
                self.assertEqual(validate_artifacts([str(path)])[0]['status'], 'pass')

    def test_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('empire.delivery.settings', SimpleNamespace(workspace=Path(tmp))):
                output = "FILE: ../outside.py\n```python\nprint('no')\n```"
                with self.assertRaises(ValueError):
                    materialize_files(1, output)

if __name__ == '__main__': unittest.main()
