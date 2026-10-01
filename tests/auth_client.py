"""Explicit test-only issued credentials; the server has no test authentication bypass."""
import hashlib
import json
import os
from fastapi.testclient import TestClient as OriginalClient

IDENTITIES = ('test.operator', 'maker.priya', 'checker.arvind', 'rm.neha', 'credit.suresh', 'ops.rahul')
TOKENS = {actor: 'issued-test-credential-with-sufficient-entropy-' + actor for actor in IDENTITIES}
os.environ['CASSANDRE_AUTH_CREDENTIALS'] = json.dumps([
    {'actor':actor, 'token_sha256':hashlib.sha256(token.encode()).hexdigest(), 'institution_id':'SIM-BANK-001', 'roles':['reader','maker','checker']}
    for actor, token in TOKENS.items()
])

class TestClient(OriginalClient):
    def request(self, method, url, **kwargs):
        # Old workflow scenarios supply an actor to choose an issued test user;
        # security tests use OriginalClient and never use this convenience helper.
        body = kwargs.get('json') or {}
        actor = next((body[k] for k in ('submitted_by','approver','decided_by','actor') if body.get(k)), 'test.operator')
        headers = dict(kwargs.pop('headers', None) or {})
        headers.setdefault('Authorization', 'Bearer ' + TOKENS[actor])
        return super().request(method, url, headers=headers, **kwargs)
