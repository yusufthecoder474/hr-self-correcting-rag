"""Single-process prototype limits. Deploy a shared gateway limiter for multiple workers."""
import time,uuid,threading
from collections import defaultdict,deque
from starlette.responses import JSONResponse
class SecurityMiddleware:
    def __init__(self,app,max_body=8192):
        self.app=app;self.max_body=max_body;self.hits=defaultdict(deque);self.lock=threading.Lock()
    async def __call__(self,scope,receive,send):
        if scope['type']!='http': return await self.app(scope,receive,send)
        rid=uuid.uuid4().hex
        async def wrapped(message):
            if message['type']=='http.response.start':
                message.setdefault('headers',[]).extend([(b'x-request-id',rid.encode()),(b'x-content-type-options',b'nosniff'),(b'x-frame-options',b'DENY'),(b'cache-control',b'no-store')])
            await send(message)
        path=scope['path'];now=time.monotonic()
        if path in ['/ask','/auth/login','/auth/register']:
            key=(scope.get('client',('unknown',))[0],path)
            with self.lock:
                # Bound retained identity buckets; do not trust X-Forwarded-For.
                for k in list(self.hits):
                    if not self.hits[k] or self.hits[k][-1]<now-60:del self.hits[k]
                q=self.hits[key]
                while q and q[0]<now-60:q.popleft()
                limited=len(q)>=(10 if path.startswith('/auth') else 20) or len(self.hits)>10000
                if not limited:q.append(now)
            if limited:return await JSONResponse({'detail':'Request limit reached.'},429)(scope,receive,wrapped)
        data=b''
        if scope['method'] in ['POST','PUT','PATCH']:
            while True:
                msg=await receive()
                if msg['type']=='http.disconnect':return
                data+=msg.get('body',b'')
                if len(data)>self.max_body:return await JSONResponse({'detail':'Request too large.'},413)(scope,receive,wrapped)
                if not msg.get('more_body'):break
            delivered=False
            async def bounded():
                nonlocal delivered
                if not delivered:delivered=True;return {'type':'http.request','body':data,'more_body':False}
                return await receive()
            await self.app(scope,bounded,wrapped)
        else:await self.app(scope,receive,wrapped)
