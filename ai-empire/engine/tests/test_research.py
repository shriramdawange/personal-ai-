import unittest
from unittest.mock import patch
from empire.research import hunt_clients, search_web

class ResearchTests(unittest.TestCase):
    def test_resolves_duckduckgo_redirect(self):
        class FakeAnchor:
            def get(self, key, default=''):
                from urllib.parse import quote
                return 'https://duckduckgo.com/l/?uddg=' + quote('https://example.org/services')
            def get_text(self, *args, **kwargs): return 'Example Services'
        class FakeSnippet:
            def get_text(self, *args, **kwargs): return 'A small business service page'
        class FakeItem:
            def select_one(self, selector):
                return FakeAnchor() if selector == '.result__a' else FakeSnippet()
        class FakeSoup:
            def select(self, selector): return [FakeItem()]
        class FakeResponse:
            text = '<html></html>'
            def raise_for_status(self): pass
        with patch('empire.research.requests.get', return_value=FakeResponse()), patch('empire.research.BeautifulSoup', return_value=FakeSoup()):
            results = search_web('example', 3)
        self.assertEqual(results[0]['url'], 'https://example.org/services')

    def test_score_parser_handles_fraction(self):
        result = [{'title':'Example','url':'https://example.org','snippet':'A relevant business'}]
        with patch('empire.research.search_web', return_value=result), patch('empire.research.qualify_lead', return_value='FIT_SCORE: 72/100\nBUSINESS: Example\nOUTREACH_DRAFT: Hello'), patch('empire.research.save_lead'):
            leads = hunt_clients('test query', 1)
        self.assertEqual(leads[0]['fit_score'], 72)
        self.assertEqual(leads[0]['outreach_draft'], 'Hello')

if __name__ == '__main__':
    unittest.main()
