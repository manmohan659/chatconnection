"""Exercise the actual query function with a fake transport, never the provider."""
import ast
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

class ProviderConfigTests(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).resolve().parents[1] / 'llama_connect.py'
        tree = ast.parse(source.read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'query_llama')
        self.transport = Mock()
        namespace = {'os': os, 'requests': self.transport, 'API_URL': 'https://provider.invalid'}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
        self.query = namespace['query_llama']

    def test_missing_key_does_not_call_transport(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'HF_TOKEN is required'):
                self.query('synthetic')
        self.transport.post.assert_not_called()

    def test_environment_key_and_timeout_are_used(self):
        self.transport.post.return_value.status_code = 200
        self.transport.post.return_value.json.return_value = [{'generated_text': 'ok'}]
        with patch.dict(os.environ, {'HF_TOKEN': 'synthetic-test-placeholder'}, clear=True):
            self.assertEqual(self.query('synthetic'), 'ok')
        kwargs = self.transport.post.call_args.kwargs
        self.assertEqual(kwargs['headers']['Authorization'], 'Bearer synthetic-test-placeholder')
        self.assertEqual(kwargs['timeout'], 30)

    def test_provider_error_body_is_not_disclosed(self):
        self.transport.post.return_value.status_code = 401
        self.transport.post.return_value.text = 'sensitive response body'
        with patch.dict(os.environ, {'HF_TOKEN': 'synthetic-test-placeholder'}, clear=True):
            with self.assertRaisesRegex(RuntimeError, '^Provider request failed with status 401$'):
                self.query('synthetic')

if __name__ == '__main__':
    unittest.main()
