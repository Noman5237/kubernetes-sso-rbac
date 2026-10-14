const {chromium}=require('playwright');
const fs=require('fs');
const assert=require('assert/strict');
const BASE='https://rancher.lab.test:8443';
async function login(context,user) {
 const page=context.pages()[0]||await context.newPage();let loginStatus;let codeReturned=false;
 context.on("request",r=>{const u=new URL(r.url());if(u.origin===BASE && u.pathname==="/verify-auth" && u.searchParams.has("code"))codeReturned=true;});
 const watch=p=>p.on('response',r=>{if(r.url().includes('/v3-public/')&&r.url().includes('action=login'))loginStatus=r.status();});
 watch(page);context.on('page',watch);
 console.log('Checking browser login:',user);
 await page.goto(BASE+'/dashboard/',{waitUntil:'networkidle'});
 console.log('Login page ready:',user);
 await page.getByRole('button',{name:'Log in with OIDC',exact:true}).click();
 console.log('OIDC redirect started:',user);
 let auth;
 for(let i=0;i<60;i++){auth=context.pages().find(p=>p.url().startsWith('https://sso.lab.test:8443/'));if(auth)break;await page.waitForTimeout(500);}
 assert(auth,'Keycloak page must open');
 await auth.locator('#username').fill(user);
 await auth.locator('#password').fill(fs.readFileSync('/run/'+user+'-password','utf8').trim());
 await auth.locator('#kc-login').click();
 console.log('Keycloak form submitted:',user);
 if(user==='alice') {
  await page.waitForURL(url=>url.pathname==='/dashboard/home',{timeout:30000});
  loginStatus="allowed";
 } else {
  await page.waitForTimeout(3000);
  const text=await page.locator('body').innerText();
  console.log('No-role page:',text.slice(0,2000));
  assert(/unauthorized|not authorized|not allowed|denied|authentication failed|Invalid username or password/i.test(text),'Expected visible login denial');
  loginStatus="denied";
 }
 console.log('Browser login result:',user,loginStatus);
 assert(codeReturned,"Keycloak must return an authorization code before Rancher admission check");
 return {page,status:loginStatus};
}
(async()=>{
 const contexts=[];
 async function makeContext(){const c=await chromium.launchPersistentContext(fs.mkdtempSync('/tmp/lab-ui-'),{executablePath:'/usr/bin/chromium',headless:true,ignoreHTTPSErrors:false,viewport:{width:1440,height:1000}});contexts.push(c);return c;}
 try {
  const context=await makeContext();
  const {page,status}=await login(context,'alice');assert.equal(status,"allowed");

  await page.goto(BASE+'/dashboard/home',{waitUntil:'networkidle'});
  await page.getByRole('link',{name:'cluster-a',exact:true}).waitFor();
  const links=await page.locator('a[href]').evaluateAll(xs=>xs.map(a=>({text:a.innerText.trim(),href:a.getAttribute('href')})));
  const clusters=links.filter(a=>/^\/dashboard\/c\/[^/]+\/explorer$/.test(a.href));
  assert.deepEqual(clusters.map(c=>c.text).sort(),['cluster-a','cluster-b']);
  await page.screenshot({path:'/artifacts/alice-home.png',fullPage:true});
  const results=[];
  for(const cluster of clusters){
   await page.goto(BASE+cluster.href+'/apps.deployment',{waitUntil:'networkidle'});
   await page.getByText('There are no rows to show.',{exact:true}).waitFor();
   const create=await page.getByRole('link',{name:'Create',exact:true}).count();
   assert.equal(create,cluster.text==='cluster-b'?1:0);
   const cid=cluster.href.split('/')[3];
   const checks=await page.evaluate(async ({cid})=>{
    const result={};for(const [name,path] of Object.entries({demo:'/api/v1/namespaces/demo/pods',outside:'/api/v1/namespaces/kube-system/pods',secrets:'/api/v1/namespaces/demo/secrets'})){
     const r=await fetch('/k8s/clusters/'+cid+path,{credentials:'same-origin'});result[name]=r.status;
    }return result;
   },{cid});
   assert.equal(checks.demo,200);assert.equal(checks.outside,403);assert.equal(checks.secrets,cluster.text==='cluster-b'?200:403);
   await page.getByText('There are no rows to show.',{exact:true}).waitFor();
   await page.waitForTimeout(500);
   await page.screenshot({path:'/artifacts/'+cluster.text+'-deployments.png',fullPage:true});
   results.push({cluster:cluster.text,createActionVisible:create===1,...checks});
   console.log('PASS:',cluster.text,'rendered deployment permissions and browser-session API boundaries');
  }
  const management=await page.evaluate(async()=> (await fetch('/k8s/clusters/local/api/v1/namespaces',{credentials:'same-origin'})).status);
  assert.equal(management,403);
  console.log('PASS: management cluster absent and API access denied');
  await context.close();
  const deniedContext=await makeContext();
  const denied=await login(deniedContext,'no-role');assert.equal(denied.status,"denied");
  await denied.page.screenshot({path:'/artifacts/no-role-denied.png',fullPage:true});
  console.log('PASS: no-role real browser OIDC login denied by Rancher');
  fs.writeFileSync('/artifacts/browser-results.json',JSON.stringify({aliceLogin:true,tlsVerification:true,clusters:results,managementStatus:management,noRoleDenied:denied.status==="denied"},null,2));
  await deniedContext.close();
 } finally { for(const c of contexts)await c.close().catch(()=>{}); }
})().catch(e=>{console.error(e.message);process.exit(1)});
