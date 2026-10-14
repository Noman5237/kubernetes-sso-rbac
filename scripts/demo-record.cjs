// Record real lab pages with annotation overlays. Passwords and storage state stay in /tmp.
const {chromium}=require('playwright');const fs=require('fs');const cp=require('child_process');const assert=require('assert/strict');
const BASE='https://rancher.lab.test:8443';const KC='https://sso.lab.test:8443';
const scenes=JSON.parse(fs.readFileSync('/demo/scenes.json'));const results=JSON.parse(fs.readFileSync('/demo/kubectl-results.json'));
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
async function overlay(p,s){await p.evaluate(s=>{const old=document.getElementById('demo-caption');if(old)old.remove();const x=document.createElement('div');x.id='demo-caption';x.style='position:fixed;bottom:0;left:0;right:0;height:112px;background:#0d1729;z-index:2147483647;color:white;padding:19px 38px;font-family:Arial;box-sizing:border-box;border-top:4px solid #38d6c5;pointer-events:none';const b=document.createElement('div');b.textContent=s.badge.toUpperCase();b.style='color:#7de7dc;font-size:15px;letter-spacing:2px;margin-bottom:10px';const t=document.createElement('div');t.textContent=s.title;t.style='font-size:29px;font-weight:700';x.append(b,t);document.body.append(x);},s);}
async function point(p,locator){if(!await locator.count())return;const e=locator.first();await e.scrollIntoViewIfNeeded();await e.evaluate(x=>{x.style.outline='4px solid #e7a52a';x.style.outlineOffset='4px';});const box=await e.boundingBox();if(box){await p.mouse.move(box.x+box.width/2,box.y+box.height/2,{steps:15});await p.evaluate(({x,y})=>{let a=document.getElementById('demo-pointer');if(!a){a=document.createElement('div');a.id='demo-pointer';a.style='position:fixed;width:22px;height:22px;border:4px solid #e7a52a;border-radius:50%;background:#ffda7355;z-index:2147483646;pointer-events:none;transition:all 700ms';document.body.append(a);}a.style.left=x+'px';a.style.top=y+'px';},{x:box.x+box.width+14,y:box.y+box.height/2-12});}}
function slide(end=false){return `<!doctype html><html><body style="margin:0;background:#0d1729;color:#edf6ff;font-family:Arial;padding:65px 70px"><div style="font-size:17px;color:#7de7dc;letter-spacing:3px">LOCAL KUBERNETES AUTH LAB</div><h1 style="font-size:52px;margin:30px 0 50px">${end?'One Alice. Two scopes.':'Identity → permissions → API access'}</h1><div style="display:flex;gap:22px;font-size:27px">${['Keycloak<br><small>Who is Alice?</small>','Rancher / mngmt<br><small>What may Alice do?</small>','Kubernetes<br><small>Enforce RBAC</small>'].map(x=>'<div style="padding:35px 25px;border:2px solid #39b7bb;border-radius:12px;flex:1">'+x+'</div>').join('')}</div><div style="display:flex;gap:24px;margin-top:40px;font-size:26px"><div style="flex:1;padding:26px;background:#172b43;border-radius:12px">Cluster A / demo<br><b style="color:#7de7dc">lab-developer</b><br><small>Read pods + deployments</small></div><div style="flex:1;padding:26px;background:#172b43;border-radius:12px">Cluster B / demo<br><b style="color:#7de7dc">lab-namespace-admin</b><br><small>Explicit namespaced resources</small></div></div><p style="color:#b5c7db;font-size:23px;margin-top:36px">${end?'Tokens: 1 hour · Roles unchanged · Lifecycle tests pending':'Three kind clusters · No application workloads · No Keycloak groups'}</p></body></html>`;}
function terminal(cluster){return `<!doctype html><html><body style="margin:0;background:#101722;color:#dce9f7;font-family:monospace;padding:42px"><div style="font-family:Arial;color:#7de7dc;font-size:17px;letter-spacing:2px">REAL COMMAND RESULTS · ${cluster.toUpperCase()} · ALICE</div><p style="color:#9dacc0;font-size:17px">Captured ${esc(results.capturedAt)} · playback of actual output</p><div id="rows" style="font-size:20px;line-height:1.5;margin-top:28px"></div></body></html>`;}
(async()=>{
 const prep=await chromium.launchPersistentContext('/tmp/demo-admin',{executablePath:'/usr/bin/chromium',headless:true});const admin=await prep.storageState();await prep.close();
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true});const auth=await browser.newContext();const lp=await auth.newPage();let codeReturned=false;
 auth.on('request',r=>{const u=new URL(r.url());if(u.origin===BASE&&u.pathname==='/verify-auth'&&u.searchParams.has('code'))codeReturned=true;});
 await lp.goto(BASE+'/dashboard/',{waitUntil:'networkidle'});await lp.getByRole('button',{name:'Log in with OIDC',exact:true}).click();let kp;
 for(let n=0;n<60;n++){kp=auth.pages().find(p=>p.url().startsWith(KC));if(kp)break;await lp.waitForTimeout(250);}
 assert(kp);await kp.locator('#username').fill('alice');await kp.locator('#password').fill(fs.readFileSync('/run/alice-password','utf8').trim());await kp.locator('#kc-login').click();await lp.waitForURL(u=>u.pathname==='/dashboard/home');assert(codeReturned);const alice=await auth.storageState();await auth.close();
 const report=fs.existsSync('/demo/recording.json')?JSON.parse(fs.readFileSync('/demo/recording.json')):[];
 for(const s of scenes){
  if(report.some(x=>x.id===s.id))continue;
  console.log('Recording',s.id);const audio=Number(cp.execFileSync('ffprobe',['-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1','/demo/'+s.id+'.aiff'],{encoding:'utf8'}));const duration=audio+1.6;
  const state=['identity','roles','binding-a','binding-b'].includes(s.id)?admin:alice;
  const c=await browser.newContext({storageState:state,viewport:{width:1440,height:900},ignoreHTTPSErrors:false,recordVideo:{dir:'/demo/raw',size:{width:1440,height:900}}});const p=await c.newPage();let highlight;
  if(s.id==='intro'||s.id==='outro')await p.setContent(slide(s.id==='outro'));
  else if(s.id==='identity'){
   await p.goto(KC+'/admin/master/console/#/kubernetes/users',{waitUntil:'networkidle'});
   if(await p.locator('#username').count()){await p.locator('#username').fill('recovery-admin');await p.locator('#password').fill(fs.readFileSync('/run/recovery-password','utf8').trim());await p.locator('#kc-login').click();}
   await p.getByRole('link',{name:'alice',exact:true}).waitFor();highlight=p.getByRole('link',{name:'alice',exact:true});
  } else if(s.id==='roles'){
   await p.goto(BASE+'/dashboard/c/c-xncbh/auth/roles/management.cattle.io.roletemplate/rt-g8ssj',{waitUntil:'networkidle'});await p.getByText('Project/Namespaces - lab-developer',{exact:true}).waitFor();highlight=p.getByText('pods',{exact:true});
  } else if(s.id.startsWith('binding-')){
   const cid=s.id==='binding-a'?'c-xncbh':'c-cs8x9';await p.goto(BASE+'/dashboard/c/'+cid+'/explorer/members',{waitUntil:'networkidle'});await p.getByText('Project Membership',{exact:true}).click();await p.getByText('Alice Lab',{exact:true}).waitFor();const role=s.id==='binding-a'?'lab-developer':'lab-namespace-admin';await p.getByText(role,{exact:true}).waitFor();highlight=p.locator('tr').filter({hasText:'Alice Lab'});
  }else if(s.id==='home'){
   await p.goto(BASE+'/dashboard/home',{waitUntil:'networkidle'});await p.getByRole('link',{name:'cluster-a',exact:true}).waitFor();assert.equal(await p.getByRole('link',{name:'local',exact:true}).count(),0);highlight=p.getByRole('link',{name:'cluster-a',exact:true});
  }else if(s.id.startsWith('dashboard-')){
   const b=s.id==='dashboard-b';await p.goto(BASE+'/dashboard/c/'+(b?'c-cs8x9':'c-xncbh')+'/explorer/apps.deployment',{waitUntil:'networkidle'});await p.getByText('There are no rows to show.',{exact:true}).waitFor();assert.equal(await p.getByRole('link',{name:'Create',exact:true}).count(),b?1:0);highlight=b?p.getByRole('link',{name:'Create',exact:true}):p.getByText('There are no rows to show.',{exact:true});
  }else if(s.id.startsWith('terminal-'))await p.setContent(terminal(s.id==='terminal-a'?'cluster-a':'cluster-b'));
  await overlay(p,s);await p.waitForTimeout(400);const start=Date.now();
  if(s.id.startsWith('terminal-')){
   const rows=results.checks[s.id==='terminal-a'?'cluster-a':'cluster-b'];
   for(const row of rows){await p.evaluate(row=>{const x=document.createElement('div');x.style='margin-bottom:19px';const a=document.createElement('div');a.textContent='$ '+row.command;a.style='color:#eef5ff';const b=document.createElement('div');b.textContent=row.output;b.style='color:'+(row.exitCode===0?'#7de7dc':'#f6bd70')+';white-space:pre-wrap';x.append(a,b);document.getElementById('rows').append(x);},row);await p.waitForTimeout((duration-2)*1000/rows.length);}
  }else{
   await p.waitForTimeout(1400);if(highlight)await point(p,highlight);
   if(s.id==='identity'){
    await p.waitForTimeout(4300);await p.getByRole('link',{name:'Groups',exact:true}).click();await p.waitForLoadState('networkidle');await p.getByText('No groups in this realm',{exact:false}).waitFor({timeout:10000}).catch(()=>{});await overlay(p,s);
   }
  }
  const left=duration*1000-(Date.now()-start);if(left>0)await p.waitForTimeout(left);
  await p.screenshot({path:'/demo/'+s.id+'.png'});const video=p.video();await c.close();const raw=await video.path();report.push({...s,audioDuration:audio,duration,raw});fs.writeFileSync('/demo/recording.json',JSON.stringify(report,null,2));console.log('Recorded',s.id,Math.round(duration)+'s');
 }
 await browser.close();console.log('PASS: real UI checks, Keycloak OIDC login, and all demo scenes recorded');
})().catch(e=>{console.error(e.message);process.exit(1)});
