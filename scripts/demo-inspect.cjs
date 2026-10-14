const {chromium}=require('playwright'); const fs=require('fs');
(async()=>{
const c=await chromium.launchPersistentContext('/tmp/demo-admin',{executablePath:'/usr/bin/chromium',headless:true,viewport:{width:1440,height:900}});const p=c.pages()[0];
const mode=process.env.MODE||'keycloak';
if(mode==='keycloak'){
 await p.goto('https://sso.lab.test:8443/admin/master/console/#/kubernetes/users',{waitUntil:'networkidle'});
 if(await p.locator('#username').count()){await p.locator('#username').fill('recovery-admin');await p.locator('#password').fill(fs.readFileSync('/run/recovery-password','utf8').trim());await p.locator('#kc-login').click();await p.waitForTimeout(2500);}
}else{
 await p.goto('https://rancher.lab.test:8443/dashboard/auth/login',{waitUntil:'networkidle'});
 if(await p.getByText('Use a local user',{exact:true}).count())await p.getByText('Use a local user',{exact:true}).click();
 console.log('INPUTS',await p.locator('input').evaluateAll(xs=>xs.map(x=>({type:x.type,placeholder:x.placeholder,name:x.name}))));
 if(await p.locator('input[type=password]').count()){
 await p.locator('input').filter({visible:true}).first().fill('admin');
 await p.locator('input[type=password]').fill(fs.readFileSync('/run/rancher-admin-password','utf8').trim());
 await p.getByRole('button',{name:/log in/i}).click();await p.waitForTimeout(2000);
 }
}
if(process.env.URL)await p.goto(process.env.URL,{waitUntil:'networkidle'});
if(process.env.CLICK)await p.getByText(process.env.CLICK,{exact:true}).click();await p.waitForTimeout(1500);console.log((await p.locator('body').innerText()).slice(0,16000));console.log(await p.locator('a').evaluateAll(xs=>xs.filter(x=>x.innerText.trim()).map(x=>({t:x.innerText.trim(),h:x.getAttribute('href')}))));await p.screenshot({path:'/demo/inspect-'+mode+'.png'});await c.close();
})().catch(e=>{console.error(e.message);process.exit(1)});
