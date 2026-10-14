#!/usr/bin/env python3
"""Join actual browser recordings with locally synthesized narration."""
import json,subprocess,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'artifacts/demo';scenes=json.loads((out/'recording.json').read_text())
def run(args):
 p=subprocess.run(['docker','exec','sso-lab-demo',*args],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-3000:])
 return p.stdout
chapters=[];elapsed=0
for i,s in enumerate(scenes):
 dest=f'/demo/clip-{i:02}.mp4'
 run(['ffmpeg','-y','-v','error','-sseof',str(-s['duration']),'-i',s['raw'],'-i',f"/demo/{s['id']}.aiff",'-filter_complex','[0:v]setpts=PTS-STARTPTS,fps=24[v];[1:a]adelay=800:all=1,apad[a]','-map','[v]','-map','[a]','-t',str(s['duration']),'-c:v','libx264','-preset','veryfast','-crf','22','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-ar','48000','-ac','2','-movflags','+faststart',dest])
 chapters.append({'start':elapsed,'title':s['title'],'id':s['id']});elapsed+=float(run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',dest]))
 print('Rendered',s['id'],flush=True)
(out/'concat.txt').write_text(''.join(f"file '/demo/clip-{i:02}.mp4'\n" for i in range(len(scenes))))
run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i','/demo/concat.txt','-c','copy','-movflags','+faststart','/demo/kubernetes-sso-rbac-demo.mp4'])
(out/'chapters.json').write_text(json.dumps(chapters,indent=2)+'\n')
transcript=['# Demo transcript','', 'Real browser recording with local synthetic narration. Terminal panels replay actual captured kubectl output.','']
for s,c in zip(scenes,chapters):
 sec=int(c['start']);transcript.extend([f"## {sec//60:02}:{sec%60:02} — {s['title']}",'',s['narration'],''])
(out/'transcript.md').write_text('\n'.join(transcript))
probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json','/demo/kubernetes-sso-rbac-demo.mp4']))
assert any(s['codec_name']=='h264' for s in probe['streams']);assert any(s['codec_name']=='aac' for s in probe['streams'])
(out/'media-verification.json').write_text(json.dumps(probe,indent=2)+'\n')
# Decode the whole deliverable to verify it is not corrupt.
run(['ffmpeg','-v','error','-i','/demo/kubernetes-sso-rbac-demo.mp4','-f','null','-'])
print('PASS: H.264/AAC video, complete decode; duration',probe['format']['duration'],flush=True)

# Publish the verified deliverable in the project demo folder.
(root/'demo').mkdir(exist_ok=True)
shutil.move(out/'kubernetes-sso-rbac-demo.mp4',root/'demo/kubernetes-sso-rbac-demo.mp4')
print('Saved demo/kubernetes-sso-rbac-demo.mp4',flush=True)
