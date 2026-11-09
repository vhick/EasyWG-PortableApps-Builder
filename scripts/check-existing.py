"""Check only the current builder repository's EXACT release tag."""
import json,os,urllib.error,urllib.request
repo=os.environ['GITHUB_REPOSITORY'];tag=os.environ['RELEASE_TAG'];token=os.environ['GITHUB_TOKEN']
url=f'https://api.github.com/repos/{repo}/releases/tags/{tag}'
req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+token,
  'X-GitHub-Api-Version':'2022-11-28','User-Agent':'EasyWGPortable-Builder/b1r2'})
try:
 with urllib.request.urlopen(req,timeout=45) as r:
  record=json.load(r)
  if record.get('draft') or '<!-- portable-release-publisher:managed:v2 -->' not in record.get('body',''):
   raise RuntimeError('Exact release tag is occupied by a draft or non-publisher release; manual review needed')
  exists=True
except urllib.error.HTTPError as e:
 if e.code==404:exists=False
 else:raise RuntimeError(f'Cannot check existing release safely: HTTP {e.code}') from e
with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as f:f.write(f'skip={str(exists).lower()}\n')
print('Exact release in current builder:',tag,'exists=',exists)
