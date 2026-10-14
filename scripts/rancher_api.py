"""Lab API helper: explicit CA, local password, transient login token; no secret output."""
import json, ssl, urllib.request, urllib.error, http.cookiejar
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='https://rancher.lab.test:8443'
class Rancher:
    def __init__(self):
        self.context=ssl.create_default_context(cafile=str(ROOT/'secrets/ca/ca.crt'))
        self.token=None
        self.cookies=http.cookiejar.CookieJar()
        self.opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=self.context), urllib.request.HTTPCookieProcessor(self.cookies))
    def call(self,path,data=None,method=None,raw=False):
        url=path if path.startswith('https://') else BASE+path
        if not url.startswith(BASE+'/'): raise ValueError('Unexpected API origin')
        headers={'Content-Type':'application/json'}
        if self.token: headers['Authorization']='Bearer '+self.token
        req=urllib.request.Request(url,data=None if data is None else json.dumps(data).encode(),headers=headers,method=method)
        try:
            with self.opener.open(req,timeout=45) as r: body=r.read()
        except urllib.error.HTTPError as e:
            # URLs can contain registration credentials. Do not print the URL or response.
            raise RuntimeError('Rancher API HTTP status '+str(e.code)) from None
        return body if raw else (json.loads(body) if body else {})
    def __enter__(self):
        result=self.call('/v3-public/localProviders/local?action=login',{'username':'admin','password':(ROOT/'secrets/rancher/admin-password').read_text().strip(),'responseType':'json','ttl':3600000})
        self.token=result['token']
        current=[t for t in self.call('/v3/tokens')['data'] if t.get('current')]
        assert len(current)==1, 'Cannot identify current API session'
        self.token_id=current[0]['id']
        return self
    def __exit__(self,*args):
        try:
            self.call('/v3/tokens?action=logout',data={},method='POST')
        except RuntimeError:
            raise RuntimeError('Could not revoke API session '+self.token_id) from None
        self.token=None
