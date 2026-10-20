from urllib.parse import quote_plus, urlparse
import requests
from bs4 import BeautifulSoup
from .agents import qualify_lead
from .db import save_lead

HEADERS = {'User-Agent':'Mozilla/5.0 (compatible; AIEmpireResearch/0.1; +https://github.com/msitarzewski/agency-agents)'}

def search_web(query: str, limit: int = 10):
    """Best-effort public DuckDuckGo HTML search; results must be manually verified."""
    url = 'https://html.duckduckgo.com/html/?q=' + quote_plus(query)
    response = requests.get(url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    results=[]
    for item in soup.select('.result'):
        anchor = item.select_one('.result__a')
        snippet_node = item.select_one('.result__snippet')
        if not anchor: continue
        href = anchor.get('href','').strip()
        title = anchor.get_text(' ',strip=True)
        snippet = snippet_node.get_text(' ',strip=True) if snippet_node else ''
        if not href.startswith('http') or 'duckduckgo.com' in urlparse(href).netloc: continue
        results.append({'title':title,'url':href,'snippet':snippet})
        if len(results)>=limit: break
    return results

def hunt_clients(query: str, limit: int = 10):
    results = search_web(query, limit)
    saved=[]
    for item in results:
        try:
            assessment = qualify_lead(query,item['title'],item['url'],item['snippet'])
            score = 0
            for line in assessment.splitlines():
                if line.strip().upper().startswith('FIT_SCORE:'):
                    digits=''.join(c for c in line.split(':',1)[1] if c.isdigit())
                    if digits: score=max(0,min(100,int(digits)))
            name=item['title'][:300]
            for line in assessment.splitlines():
                if line.strip().upper().startswith('BUSINESS:'):
                    name=line.split(':',1)[1].strip()[:300] or name
            lead={'name':name,'url':item['url'],'snippet':item['snippet'],'fit_score':score,'rationale':assessment,'outreach_draft':assessment}
            save_lead(lead); saved.append(lead)
        except Exception as exc:
            saved.append({'name':item['title'],'url':item['url'],'fit_score':0,'error':str(exc)})
    return saved
