"""Fail when pinned shared actions no longer match expected public interfaces."""
import re, urllib.request
for repo,tag,commit,inputs,outputs in (
 ('Portable-Package-Builder','v1.0.0','0112c35580e83b37eb8757ebcb949274e1631a04',('source-dir','output-dir','engine','running-exe','timeout-seconds','package-revision'),('installer-file','installer-sha256','app-id','app-version')),
 ('portable-release-publisher','v1.1.1','cb64f86ac2d8c67506db5832de07f9ff58cbeaeb',('files','tag','release-title','tag-prefix','keep-releases','prune','dry-run'),()),
):
 url=f'https://raw.githubusercontent.com/vhick/{repo}/{tag}/action.yml'
 request=urllib.request.Request(url,headers={'User-Agent':'EasyWGPortable-Builder/b1r2'})
 with urllib.request.urlopen(request,timeout=60) as r:tag_bytes=r.read()
 pin_url=f'https://raw.githubusercontent.com/vhick/{repo}/{commit}/action.yml'
 with urllib.request.urlopen(urllib.request.Request(pin_url,headers={'User-Agent':'EasyWGPortable-Builder/b1r2'}),timeout=60) as r:pin_bytes=r.read()
 if tag_bytes != pin_bytes:raise RuntimeError(f'Pinned tag no longer maps to expected immutable action bytes: {repo}@{tag}')
 body=pin_bytes.decode('utf-8')
 for field in inputs+outputs:
  if not re.search(r'^\s{2}'+re.escape(field)+r':\s*$',body,re.M):
   raise RuntimeError(f'Action contract unexpected: {repo}@{tag}: {field}')
 print('Verified pinned action.yml contract:',repo,tag)
