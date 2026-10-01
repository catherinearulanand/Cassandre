"""Fail-closed local prototype authentication. Replace with bank SSO before rollout."""
import hashlib
import hmac
import json
import os
import re
from pathlib import Path
from contextvars import ContextVar
from dataclasses import dataclass

from fastapi import HTTPException
from starlette.responses import JSONResponse

@dataclass(frozen=True)
class Principal:
    actor: str
    institution_id: str
    roles: frozenset[str]

current_principal = ContextVar('cassandre_principal', default=None)

def actor():
    principal = current_principal.get()
    if principal is None:
        raise HTTPException(401, 'Authentication required')
    return principal.actor

def visible(store, facility_id):
    p = current_principal.get()
    f = store.facilities.get(facility_id)
    return bool(p and f and f.institution_id == p.institution_id)

def require_facility(store, facility_id):
    if not visible(store, facility_id):
        raise HTTPException(404, 'No accessible facility for this id')

def install_security(app, get_store):
    @app.middleware('http')
    async def security_boundary(request, call_next):
        path = request.url.path
        if not path.startswith('/v1/'):
            response = await call_next(request)
        else:
            try:
                auth_file = os.environ.get('CASSANDRE_AUTH_FILE')
                credentials = json.loads(Path(auth_file).read_text() if auth_file else os.environ.get('CASSANDRE_AUTH_CREDENTIALS', '[]'))
                token = request.headers.get('authorization', '')
                digest = hashlib.sha256(token[7:].encode()).hexdigest() if token.startswith('Bearer ') and len(token[7:]) >= 32 else ''
                if not isinstance(credentials, list):
                    raise ValueError('Invalid credential configuration')
                digests = set()
                for c in credentials:
                    if not isinstance(c, dict):
                        raise ValueError('Invalid credential configuration')
                    if set(c) != {'actor','institution_id','roles','token_sha256'}:
                        raise ValueError('Invalid credential configuration')
                    if any(not isinstance(c.get(k),str) or not 1 <= len(c[k]) <= 128 or any(ord(ch)<32 for ch in c[k]) for k in ('actor','institution_id')):
                        raise ValueError('Invalid credential configuration')
                    if not isinstance(c['token_sha256'],str) or not re.fullmatch('[a-f0-9]{64}',c['token_sha256']) or c['token_sha256'] in digests:
                        raise ValueError('Invalid credential configuration')
                    digests.add(c['token_sha256'])
                    if not isinstance(c['roles'],list) or any(not isinstance(role,str) or role not in {'reader','maker','checker'} for role in c['roles']):
                        raise ValueError('Invalid credential configuration')
                record = next((c for c in credentials if hmac.compare_digest(c['token_sha256'], digest)), None)
                if record is None:
                    return JSONResponse({'detail': 'Authentication required'}, status_code=401, headers={'WWW-Authenticate':'Bearer'})
                p = Principal(record['actor'], record['institution_id'], frozenset(record['roles']))
            except (ValueError, KeyError, TypeError, OSError):
                return JSONResponse({'detail': 'Authentication configuration unavailable'}, status_code=503)
            required = 'reader'
            if request.method not in ('GET', 'HEAD'):
                required = 'checker' if path.endswith((':approve', ':decide', ':close')) else 'maker'
            if required not in p.roles:
                return JSONResponse({'detail': 'Role not permitted'}, status_code=403)
            marker = current_principal.set(p)
            try:
                store = get_store()
                match = re.match(r'/v1/facilities/([^/:]+)', path)
                if match:
                    require_facility(store, match.group(1))
                match = re.match(r'/v1/(rule-versions|waivers|renewals|cases)/([^/:]+)', path)
                if match:
                    collection = {'rule-versions':store.rule_sets, 'waivers':store.waivers, 'renewals':store.renewals, 'cases':store.approval_cases}[match.group(1)]
                    obj = collection.get(match.group(2))
                    if obj is not None:
                        fid = getattr(obj, 'facility_id', None)
                        if fid is None:
                            linked = store.rule_sets.get(obj.subject_id) or store.waivers.get(obj.subject_id)
                            fid = getattr(linked, 'facility_id', None)
                        if fid is None:
                            # Unlinked generic cases are deliberately inaccessible.
                            raise HTTPException(404, 'No accessible case')
                        require_facility(store, fid)
                if request.method not in ('GET','HEAD'):
                    limit = 262144
                    received = 0
                    chunks = []
                    async for chunk in request.stream():
                        received += len(chunk)
                        if received > limit:
                            return JSONResponse({'detail':'Request body too large'}, status_code=413)
                        chunks.append(chunk)
                    request._body = b''.join(chunks)
                response = await call_next(request)
            except HTTPException as exc:
                response = JSONResponse({'detail':exc.detail}, status_code=exc.status_code)
            finally:
                current_principal.reset(marker)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        return response
