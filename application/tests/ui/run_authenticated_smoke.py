"""Disposable local server + real browser smoke; no Gemini or model required.
Install Playwright for Node; set BROWSER_EXECUTABLE if using a custom Chromium.
"""
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as directory:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port=sock.getsockname()[1]
    env=dict(os.environ,JWT_SECRET_KEY=secrets.token_urlsafe(48),AUTH_DB_PATH=str(Path(directory)/'users.db'),ALLOW_REGISTRATION='false',SMOKE_EMAIL='browser@example.com',SMOKE_PASSWORD=secrets.token_urlsafe(24),SMOKE_URL=f'http://127.0.0.1:{port}',SMOKE_PORT=str(port))
    source="import os,auth,uvicorn; auth.create_user(os.environ['SMOKE_EMAIL'],'Browser Test',os.environ['SMOKE_PASSWORD']); uvicorn.run('app:app',host='127.0.0.1',port=int(os.environ['SMOKE_PORT']),log_level='warning')"
    server=subprocess.Popen([sys.executable,'-c',source],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(80):
            if server.poll() is not None:raise RuntimeError('Disposable test server failed to start')
            try:
                urllib.request.urlopen(env['SMOKE_URL']+'/health',timeout=.5)
                break
            except Exception:time.sleep(.1)
        else:raise RuntimeError('Disposable test server startup timed out')
        result=subprocess.run(['node','tests/ui/authenticated_smoke.cjs'],cwd=ROOT,env=env,capture_output=True,text=True,timeout=70)
        (ROOT/'research/review3/ui_real_smoke.txt').write_text(result.stdout+result.stderr)
        print(result.stdout+result.stderr)
        if result.returncode:raise SystemExit(result.returncode)
    finally:
        server.terminate()
        server.wait(timeout=10)
