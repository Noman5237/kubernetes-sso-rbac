#!/usr/bin/env python3
"""Generate local voiceover; never record the Mac microphone or desktop."""
import json, subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'artifacts/demo';out.mkdir(exist_ok=True)
scenes=[
('intro','One identity. Different permissions.','Overview','Three tiny Kubernetes clusters. The management cluster runs Rancher. Keycloak knows who Alice is. Rancher decides what Alice can do in each application cluster. We will check the real dashboard and real cube control results.'),
('identity','Keycloak says: this is Alice.','Keycloak · administrator view','Here is Alice in Keycloak. Keycloak handles her login. There are no lab groups. We keep all cluster permission assignments in Rancher. These administrator screens show the configuration; they are not screens Alice can administer.'),
('roles','Reusable role: read pods + deployments.','Rancher · administrator view','Here is the reusable lab developer role template. It grants get, list, and watch for pods and deployments. There is no cluster assignment inside this template. The project member binding chooses where these permissions apply.'),
('binding-a','Alice → lab-developer → A / demo','Rancher · administrator view','In cluster A, open Cluster and Project Members, then Project Membership. Alice has the lab developer role in the demo project. The row says Local for this direct binding, but Alice authenticates through Keycloak. This binding supplies the scope. The reusable role name does not need a cluster name.'),
('binding-b','Same Alice → namespace admin → B / demo','Rancher · administrator view','In cluster B, the same Alice has lab namespace admin in demo. This is namespace administration, not cluster administration. The role uses an explicit resource list. Keycloak has no cluster role mapping to maintain.'),
('home','Alice sees two app clusters.','Rancher · Alice view','Now we are signed in as Alice through Keycloak. Rancher shows both application clusters. The management cluster is absent. Same identity, different permissions, controlled by Rancher project assignments.'),
('dashboard-a','Cluster A: read only. No Create action.','Rancher · Alice view','In cluster A, Alice can view deployments. The list is empty because we deployed no applications. There is no Create action. Empty means the read succeeded; it does not mean access was denied.'),
('dashboard-b','Cluster B: Create is available.','Rancher · Alice view','In cluster B, the Create action is available. Alice has the broader demo namespace role here. We do not deploy anything. Next, the command line checks whether the API agrees with the dashboard.'),
('terminal-a','Actual kubectl results · Cluster A','Terminal output playback','These are real cube control commands captured for this demo, using Alice\'s Rancher kubeconfig. In A, listing pods succeeds. Creating deployments and reading secrets are denied. System namespace pods and cluster nodes are also denied.'),
('terminal-b','Actual kubectl results · Cluster B','Terminal output playback','In B, listing pods succeeds. Creating deployments and reading secrets are allowed in demo. System namespace pods and cluster nodes remain denied. Permission checks do not create workloads. The dashboard and command line agree.'),
('outro','Keycloak = identity. Rancher = permissions.','Result','Keycloak says, this is Alice. Rancher assigns her project roles. Kubernetes enforces the resulting permissions. The current kubeconfig tokens last one hour and can be revoked. This demo leaves the roles unchanged. Lifecycle and outage tests are still a separate next step.')]
items=[]
for key,title,badge,text in scenes:
 (out/(key+'.txt')).write_text(text+'\n')
 subprocess.run(['say','-v','Daniel','-r','158','-f',str(out/(key+'.txt')),'-o',str(out/(key+'.aiff'))],check=True)
 items.append({'id':key,'title':title,'badge':badge,'narration':text})
(out/'scenes.json').write_text(json.dumps(items,indent=2)+'\n')
print('Generated voiceover segments using local macOS Daniel voice')
