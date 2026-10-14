// Condense verified demo footage into a silent, looping README GIF.
const {chromium}=require('playwright');const fs=require('fs');const cp=require('child_process');const assert=require('assert/strict');
const run=(args)=>cp.execFileSync(args[0],args.slice(1),{stdio:['ignore','pipe','pipe']});
const evidence=JSON.parse(fs.readFileSync('/output/evidence.json','utf8'));
assert(evidence.testsCompleted&&evidence.restored&&evidence.testCredentialsRevoked);
const frames=[
 {id:'overview',duration:4,card:true},
 {id:'identity',duration:6,clip:1,start:0.8,take:12},
 {id:'roles',duration:4,clip:2,start:2,take:4},
 {id:'binding-a',duration:4,clip:3,start:2,take:4},
 {id:'binding-b',duration:4,clip:4,start:2,take:4},
 {id:'home',duration:4,clip:5,start:2,take:4},
 {id:'dashboard-a',duration:4,clip:6,start:2,take:4},
 {id:'dashboard-b',duration:4,clip:7,start:2,take:4},
 {id:'terminal-a',duration:5,clip:8,start:11,take:5},
 {id:'terminal-b',duration:5,clip:9,start:10,take:5},
 {id:'lifecycle',duration:7,card:true},
 {id:'boundaries',duration:5,card:true},
];
function html(id){
 const views={
 overview:{tag:'LOCAL AUTH LAB · 56-SECOND TOUR',title:'One identity. Two permission sets.',sub:'Three single-node kind clusters. No application workloads.',rows:[['Keycloak / Docker','Production mode · PostgreSQL · local-CA HTTPS'],['Rancher / management cluster','Keycloak login · reusable roles · direct Alice bindings'],['App clusters A + B','Same identity · different project permissions']],foot:'Real browser footage + actual kubectl output · No Keycloak groups'},
 lifecycle:{tag:'STEP 9 · VERIFIED LIFECYCLE RESULTS',title:'Credentials and permissions are separate.',sub:'Actual API tests. Original access restored afterward.',rows:[['Delete kubeconfig / expire token','kubectl access stops'],['Remove A project binding','A denied · B still works'],['Rancher logout','Session ends · separate kubeconfig still works'],['Disable Alice in Keycloak','New login denied · existing tokens worked for 20s']],foot:'Observation window: 20 seconds; long-term refresh behavior is not proven.'},
 boundaries:{tag:'VERIFIED BOUNDARIES · WHAT STAYS WORKING',title:'Scoped access. Recovery preserved.',sub:'Dashboard and command line agree.',rows:[['Alice','A: read-only · B: namespace admin within demo'],['Outside that scope','System namespace + nodes denied · management API denied'],['Recovery / admission','Native admin + ServiceAccount auth preserved · no-role denied']],foot:'Current admission also allows project members. Outage / restart tests: pending.'}
 };
 const v=views[id];return `<!doctype html><html><head><style>*{box-sizing:border-box}body{margin:0;background:#0d1729;color:#edf6ff;font-family:Arial,sans-serif;padding:44px 52px}.tag{color:#7de7dc;font-size:17px;letter-spacing:2px}h1{font-size:38px;line-height:1.15;margin:22px 0 13px}p{color:#bacbdf;font-size:21px;margin:0 0 25px}.row{display:flex;align-items:center;background:#192c44;border-left:4px solid #38d6c5;padding:17px 20px;margin:13px 0;gap:20px;border-radius:7px}.label{width:290px;flex-shrink:0;color:#7de7dc;font-size:21px;font-weight:bold}.value{font-size:21px;line-height:1.25}.foot{position:fixed;bottom:0;left:0;right:0;background:#142239;border-top:3px solid #38d6c5;padding:23px 52px;color:#c9d8e8;font-size:18px}</style></head><body><div class="tag">${v.tag}</div><h1>${v.title}</h1><p>${v.sub}</p>${v.rows.map(([a,b])=>`<div class="row"><div class="label">${a}</div><div class="value">${b}</div></div>`).join('')}<div class="foot">${v.foot}</div></body></html>`;
}
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true});const page=await browser.newPage({viewport:{width:1080,height:676}});
 for(const s of frames.filter(x=>x.card)){await page.setContent(html(s.id));await page.screenshot({path:'/output/'+s.id+'.png'});}
 await browser.close();
 for(let i=0;i<frames.length;i++){
  const s=frames[i],out='/output/part-'+String(i).padStart(2,'0')+'.mp4';let input,filter;
  if(s.card){input=['-loop','1','-framerate','5','-i','/output/'+s.id+'.png'];filter='fps=5,format=yuv420p';}
  else{input=['-ss',String(s.start),'-t',String(s.take),'-i','/source/clip-'+String(s.clip).padStart(2,'0')+'.mp4'];filter=`setpts=${s.duration/s.take}*(PTS-STARTPTS),fps=5,scale=1080:676:flags=lanczos,format=yuv420p`;}
  run(['ffmpeg','-y','-v','error',...input,'-an','-vf',filter,'-t',String(s.duration),'-c:v','libx264','-preset','veryfast','-crf','18','-threads','2',out]);console.log('Prepared',s.id);
 }
 fs.writeFileSync('/output/concat.txt',frames.map((_,i)=>`file '/output/part-${String(i).padStart(2,'0')}.mp4'`).join('\n')+'\n');
 run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i','/output/concat.txt','-c','copy','/output/overview.mp4']);
 run(['ffmpeg','-y','-v','error','-i','/output/overview.mp4','-vf','palettegen=max_colors=128:stats_mode=diff','-frames:v','1','/output/palette.png']);
 run(['ffmpeg','-y','-v','error','-i','/output/overview.mp4','-i','/output/palette.png','-lavfi','paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle','-loop','0','/output/unoptimized.gif']);
 run(['gifsicle','-O3','/output/unoptimized.gif','-o','/publish/poc-overview.gif']);
 const probe=JSON.parse(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json','/publish/poc-overview.gif']).toString());
 const duration=Number(probe.format.duration);assert(duration<=60&&duration>=55);assert.equal(probe.streams.length,1);assert.equal(probe.streams[0].codec_name,'gif');
 const bytes=fs.statSync('/publish/poc-overview.gif').size;assert(bytes<10*1024*1024,'GIF exceeds the README size target');
 run(['ffmpeg','-v','error','-i','/publish/poc-overview.gif','-f','null','-']);
 fs.writeFileSync('/output/verification.json',JSON.stringify({durationSeconds:duration,bytes,width:1080,height:676,audio:false,loop:'infinite',scenes:frames,fullDecodePassed:true},null,2));console.log('PASS:',duration+'s',bytes+' bytes','silent looping GIF');
})().catch(e=>{console.error(e.message);if(e.stderr)console.error(e.stderr.toString().slice(-2000));process.exit(1)});
