"""Exercise the actual server process and socket across a clean restart."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


def test_accepted_import_and_calculation_survive_real_server_restart(tmp_path):
    token = 'integration-only-issued-token-32characters-minimum'
    auth = tmp_path / 'auth.json'
    auth.write_text(json.dumps([{'actor':'restart.maker','institution_id':'SIM-BANK-001',
        'roles':['reader','maker'],'token_sha256':hashlib.sha256(token.encode()).hexdigest()}]))
    env = dict(os.environ, CASSANDRE_CC_STORE_PATH=str(tmp_path / 'snapshot.json'),
               CASSANDRE_AUTH_FILE=str(auth), PYTHONPATH=str(Path('src').resolve()))
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port = sock.getsockname()[1]
    base = f'http://127.0.0.1:{port}'

    def request(path, payload=None):
        req = urllib.request.Request(base+path,
            data=None if payload is None else json.dumps(payload).encode(),
            headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=3) as response:
            return json.load(response)

    def start():
        process = subprocess.Popen([sys.executable,'-m','uvicorn','cassandre_cc.api.main:app',
            '--host','127.0.0.1','--port',str(port),'--workers','1','--no-access-log'],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            if process.poll() is not None:
                raise AssertionError('Server exited before becoming healthy')
            try:
                request('/healthz')
                return process
            except (OSError, urllib.error.URLError):
                time.sleep(.05)
        process.terminate()
        process.wait(timeout=5)
        raise AssertionError('Server startup timed out')

    def stop(process):
        process.terminate()
        process.wait(timeout=5)

    process = start()
    try:
        payload={'facility_id':'SIM-FAC-A001','period':'2027-01',
            'reported_stock_crore':'4','stock_exclusions_crore':'0.5',
            'reported_receivables_crore':'3','receivable_exclusions_crore':'0.8',
            'outstanding_crore':'3.6'}
        batch = request('/v1/imports:financials',payload)
        run = request('/v1/facilities/SIM-FAC-A001/calculations:recompute?period=2027-01',{})
        assert run['run_id']
    finally:
        stop(process)
    process = start()
    try:
        assert request('/v1/imports:financials',payload)['batch_id'] == batch['batch_id']
        assert not request('/v1/imports:financials',payload)['was_new']
        runs = request('/v1/facilities/SIM-FAC-A001/calculation-runs')
        assert any(item['run_id'] == run['run_id'] for item in runs)
        assert request('/v1/facilities/SIM-FAC-A001?period=2027-01')['calculation']['result_state']=='calculated'
    finally:
        stop(process)
