"""Exercise the real authorization-code/PKCE flow using trusted HTTPS and cookies."""
import http.cookiejar,urllib.request,urllib.parse,urllib.error,secrets
from html.parser import HTMLParser
from rancher_api import ROOT,BASE
from keycloak_api import SSO
class LoginForm(HTMLParser):
 def __init__(self):super().__init__();self.action=None;self.fields={}
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='form' and a.get('id')=='kc-form-login':self.action=a.get('action')
  if tag=='input' and a.get('name') and a.get('type')=='hidden':self.fields[a['name']]=a.get('value','')
class StopCallback(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if newurl.startswith(BASE+'/verify-auth'):return None
  if not newurl.startswith((BASE+'/',SSO+'/')):raise RuntimeError('Unexpected redirect origin')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def authorization_code(api,redirect,username):
 opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=api.context),urllib.request.HTTPCookieProcessor(api.cookies),StopCallback())
 state=secrets.token_urlsafe(24)
 # Rancher's entry handler generates PKCE cookie; scope/state are propagated.
 sep='&' if '?' in redirect else '?'
 redirect+=sep+urllib.parse.urlencode({'scope':'openid profile email','state':state})
 with opener.open(redirect,timeout=30) as r:page=r.read().decode()
 f=LoginForm();f.feed(page)
 if not f.action or not f.action.startswith(SSO+'/'):raise RuntimeError('Keycloak login form not found')
 f.fields.update(username=username,password=(ROOT/f'secrets/keycloak/{username}-password').read_text().strip())
 request=urllib.request.Request(f.action,data=urllib.parse.urlencode(f.fields).encode(),headers={'Content-Type':'application/x-www-form-urlencoded'})
 try:
  with opener.open(request,timeout=30) as r:
   raise RuntimeError('Login did not reach OIDC callback; check required actions')
 except urllib.error.HTTPError as e:
  if e.code!=302:raise RuntimeError('Login HTTP '+str(e.code)) from None
  target=e.headers['Location'];parsed=urllib.parse.urlparse(target)
  assert target.startswith(BASE+'/verify-auth?')
  q=urllib.parse.parse_qs(parsed.query)
  assert q.get('state')==[state], 'OIDC state mismatch'
  if 'code' not in q:raise RuntimeError('No OIDC code returned')
  return q['code'][0]
