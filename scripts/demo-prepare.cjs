// Establish a private administrator browser session; nothing is saved in mounted output.
const {chromium}=require('playwright');const fs=require('fs');
(async()=>{
 const c=await chromium.launchPersistentContext('/tmp/demo-admin',{executablePath:'/usr/bin/chromium',headless:true});
 try{
 const p=c.pages()[0];await p.goto('https://rancher.lab.test:8443/dashboard/auth/login',{waitUntil:'networkidle'});
 if(await p.getByText('Use a local user',{exact:true}).count())await p.getByText('Use a local user',{exact:true}).click();
 if(await p.locator('input[type=password]').count()){
  await p.locator('input[type=text]').fill('admin');await p.locator('input[type=password]').fill(fs.readFileSync('/run/rancher-admin-password','utf8').trim());await p.getByRole('button',{name:/log in/i}).click();await p.waitForURL(u=>u.pathname==='/dashboard/home');
 }
 console.log('Administrator browser session ready; credentials stay inside container');
 }finally{await c.close();}
})().catch(e=>{console.error(e.message);process.exit(1)});
