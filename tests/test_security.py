"""Boundary attacks against real middleware, no actor-to-token convenience client."""
import hashlib
import json
from fastapi.testclient import TestClient
from cassandre_cc.api.main import app

client = TestClient(app)

def configured(monkeypatch, actor='secure.maker', roles=('reader','maker'), institution='SIM-BANK-001'):
    token='random-security-test-token-with-sufficient-entropy'
    monkeypatch.setenv('CASSANDRE_AUTH_CREDENTIALS', json.dumps([{'actor':actor,'roles':list(roles),'institution_id':institution,'token_sha256':hashlib.sha256(token.encode()).hexdigest()}]))
    monkeypatch.delenv('CASSANDRE_AUTH_FILE', raising=False)
    return {'Authorization':'Bearer '+token}

def test_fail_closed_without_credentials(monkeypatch):
    monkeypatch.setenv('CASSANDRE_AUTH_CREDENTIALS','[]')
    assert client.get('/v1/facilities').status_code == 401
    assert client.get('/healthz').json() == {'status':'ok','mode':'synthetic'}

def test_reader_cannot_mutate(monkeypatch):
    h=configured(monkeypatch, roles=('reader',))
    assert client.post('/v1/facilities/SIM-FAC-A001/calculations:recompute',headers=h).status_code == 403

def test_client_actor_cannot_impersonate_checker(monkeypatch):
    h=configured(monkeypatch)
    response=client.post('/v1/facilities/SIM-FAC-A001/rule-versions',headers=h,json={'stock_margin':'0.2','receivable_margin':'0.3','debtor_ageing_cutoff_days':90,'submitted_by':'forged.checker'})
    assert response.status_code == 200
    rule=response.json()
    assert rule['submitted_by']=='secure.maker'
    h=configured(monkeypatch, roles=('reader','maker','checker'))
    response=client.post('/v1/rule-versions/'+rule['rule_set_id']+':approve',headers=h,json={'approver':'forged.checker','effective_from':'2028-01-01'})
    assert response.status_code == 409
    assert response.json()['detail']['failure']=='SELF_APPROVAL_DENIED'

def test_foreign_tenant_cannot_enumerate_or_fetch(monkeypatch):
    h=configured(monkeypatch,institution='OTHER-BANK')
    for path in ('facilities','imports','waivers','renewals','cases','audit-events'):
        assert client.get('/v1/'+path,headers=h).json()==[]
    assert client.get('/v1/facilities/SIM-FAC-A001',headers=h).status_code==404
    assert client.post('/v1/imports:financials',headers=h,json={'facility_id':'SIM-FAC-A001','period':'2028-01'}).status_code==404

def test_invalid_inputs_no_echo(monkeypatch):
    h=configured(monkeypatch)
    for number in ('NaN','Infinity','-1'):
        response=client.post('/v1/imports:financials',headers=h,json={'facility_id':'SIM-FAC-A001','period':'2028-01','outstanding_crore':number})
        assert response.status_code==422
    assert client.get('/v1/facilities/SIM-FAC-A001?period=2026-99',headers=h).status_code==422
    response=client.post('/v1/facilities/SIM-FAC-A001/documents',headers=h,json={'document_type':'x','evidence_period':'bad','content':'sensitive-secret-marker'})
    assert response.status_code==422
    assert 'sensitive-secret-marker' not in response.text

def test_body_limit_without_content_length(monkeypatch):
    h=configured(monkeypatch)
    response=client.post('/v1/facilities/SIM-FAC-A001/documents',headers=h,content=(b'x'*300000))
    assert response.status_code==413

def test_document_replacement_cannot_cross_facility(monkeypatch):
    h=configured(monkeypatch)
    original=client.post('/v1/facilities/SIM-FAC-A001/documents',headers=h,json={'document_type':'statement','evidence_period':'2028-01','content':'example'}).json()
    response=client.post('/v1/facilities/SIM-FAC-B002/documents',headers=h,json={'document_type':'statement','evidence_period':'2028-01','content':'replacement','supersedes_document_id':original['document_id']})
    assert response.status_code==422

def test_sensitive_routes_no_cache(monkeypatch):
    h=configured(monkeypatch)
    response=client.get('/v1/facilities',headers=h)
    assert response.headers['cache-control']=='no-store'
    assert 'frame-ancestors' in response.headers['content-security-policy']

def test_browser_html_escaping_covers_user_fields():
    """Execute the shipped JS escaper and check every previously vulnerable sink."""
    import shutil
    import subprocess
    from pathlib import Path
    import pytest
    if not shutil.which('node'):
        pytest.skip('Node required for frontend escaping regression')
    script=Path('src/cassandre_cc/web/static/app.js').read_text()
    line=next(line for line in script.splitlines() if 'function escapeHTML' in line)
    attack='<img src=x onerror="steal()">\'&'
    result=subprocess.run(['node','-e',line+'; process.stdout.write(escapeHTML('+json.dumps(attack)+'));'],capture_output=True,text=True,check=True).stdout
    assert '<' not in result and '>' not in result
    assert '&lt;img' in result and '&quot;' in result and '&#39;' in result
    for expression in ('w.test_id','e.field_name.replace(/_/g, " ")','e.reviewer || "—"','c.case_id','r.decided_by || "—"'):
        assert '${escapeHTML('+expression+')}' in script

def test_original_bytes_authorised_by_document_not_hash(monkeypatch):
    h=configured(monkeypatch)
    response=client.post('/v1/facilities/SIM-FAC-A001/documents',headers=h,json={'document_type':'synthetic','evidence_period':'2028-02','content':'Original evidence bytes'})
    assert response.status_code==200
    doc=response.json()
    path='/v1/facilities/SIM-FAC-A001/documents/'+doc['document_id']+'/content'
    assert client.get(path,headers=h).content==b'Original evidence bytes'
    assert client.get(path.replace('SIM-FAC-A001','SIM-FAC-B002'),headers=h).status_code==404
    foreign=configured(monkeypatch,institution='OTHER-BANK')
    assert client.get(path,headers=foreign).status_code==404
    assert client.get('/v1/facilities/SIM-FAC-A001/documents/'+doc['source_hash']+'/content',headers=h).status_code==404

def test_malformed_credentials_fail_closed(monkeypatch):
    for config in ([None],[{'actor':'a'}],[{'actor':'a','institution_id':'SIM-BANK-001','roles':{},'token_sha256':'a'*64}]):
        monkeypatch.setenv('CASSANDRE_AUTH_CREDENTIALS',json.dumps(config))
        monkeypatch.delenv('CASSANDRE_AUTH_FILE',raising=False)
        assert client.get('/v1/facilities').status_code==503
