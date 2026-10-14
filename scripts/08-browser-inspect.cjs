const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
 const context=await chromium.launchPersistentContext('/tmp/lab-browser-profile',{executablePath:"/usr/bin/chromium",headless:true,ignoreHTTPSErrors:false,viewport:{width:1440,height:1000}});
 const page=context.pages()[0]||await context.newPage();
 await page.goto(process.env.LAB_URL||'https://rancher.lab.test:8443/dashboard/',{waitUntil:'networkidle'});
 if (await page.getByRole('button',{name:'Log in with OIDC',exact:true}).isVisible()) {
  await page.getByRole('button',{name:'Log in with OIDC',exact:true}).click();
  let popup;
  for(let i=0;i<60;i++){ popup=context.pages().find(p=>p.url().startsWith('https://sso.lab.test:8443/'));if(popup)break;await page.waitForTimeout(500);}
  if(!popup)throw new Error('Keycloak page did not open');
  await popup.locator('#username').fill('alice');
  await popup.locator('#password').fill(fs.readFileSync('/run/alice-password','utf8').trim());
  await popup.locator('#kc-login').click();
  await page.waitForURL(url=>!url.pathname.includes('/auth/'),{timeout:60000});
  await page.waitForLoadState('networkidle');
 }
 console.log((await page.locator('body').innerText()).slice(0,14000));
 console.log('Links:',await page.locator('a[href]').evaluateAll(xs=>xs.map(a=>({text:a.innerText,href:a.getAttribute('href')})).filter(a=>a.href.startsWith('/'))));
 console.log('Buttons:',await page.getByRole('button').allTextContents());
 await page.screenshot({path:'/artifacts/dashboard-current.png',fullPage:true});
 await context.close();
})().catch(e=>{console.error(e.message);process.exit(1)});
