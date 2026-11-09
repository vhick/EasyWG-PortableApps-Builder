"""EasyWG release selection, provenance, download, and PortableApps stage. Python 3.11+."""
import argparse, configparser, hashlib, io, json, os, pathlib, re, shutil, struct, sys, urllib.error, urllib.request, zipfile
from datetime import datetime, timezone
ROOT=pathlib.Path(__file__).resolve().parents[1]
BUILD=ROOT/'build'; STAGE=BUILD/'EasyWGPortable'; DIST=ROOT/'dist'
REPO='Terence0816/easy-wg-portable'
API=f'https://api.github.com/repos/{REPO}'
REV='b1r1'
# Observed on the official GitHub expanded-assets page for this exact stable release.
KNOWN_OFFICIAL_DIGESTS={'v0.2.9.2':'f65c059a8304d80733eb9fa8a81f942d4e45a848eeab43a7cf5d9f5739931dbc'}

def get(url, accept='application/vnd.github+json'):
    if not url.startswith('https://'): raise ValueError('Refuse non-HTTPS URL')
    hdr={'Accept':accept,'User-Agent':'EasyWGPortable-Builder/'+REV,'X-GitHub-Api-Version':'2022-11-28'}
    token=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token and ('api.github.com/' in url or 'github.com/' in url):hdr['Authorization']='Bearer '+token
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=hdr),timeout=90) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'HTTP {e.code} fetching {url} (API authentication/rate limit/asset issue)') from e

def jsonget(url): return json.loads(get(url).decode('utf-8'))
def sha(b): return hashlib.sha256(b).hexdigest()
def stable(t):
    m=re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?',t,re.I)
    return tuple(map(int,m.groups(default='0'))) if m else None

def find_releases(version):
    results=[]
    for page in range(1,6):
        pageitems=jsonget(f'{API}/releases?per_page=100&page={page}')
        if not isinstance(pageitems,list): raise RuntimeError('GitHub releases response not array')
        if not pageitems:break
        for item in pageitems:
            t=item.get('tag_name','')
            if item.get('draft') or item.get('prerelease') or not stable(t):continue
            if version!='latest' and t.lower().lstrip('v') != version.lower().lstrip('v'): continue
            results.append(item)
        if len(pageitems)<100:break
    if not results:raise RuntimeError('No matching stable EasyWG GitHub Release (not defaulting to main)')
    return max(results,key=lambda item:stable(item['tag_name']))

def resolve(version):
    release=find_releases(version); tag=release['tag_name']
    commit=jsonget(f'{API}/commits/{tag}')['sha']
    if not re.fullmatch('[0-9a-f]{40}',commit):raise RuntimeError('GitHub returned invalid commit')
    assets=release.get('assets') or []
    exe=[a for a in assets if a['name'].lower()=='easywg.exe']
    if len(exe)!=1:raise RuntimeError('Official stable release does not expose exactly one EasyWG.exe asset; no substitute/mirror')
    asset=exe[0]; url=asset.get('browser_download_url','')
    if not url.startswith(f'https://github.com/{REPO}/releases/download/{tag}/'):
        raise RuntimeError('Unexpected EasyWG download host/path')
    content=get(url,'application/octet-stream')
    if len(content)<8192 or content[:2]!=b'MZ':raise RuntimeError('EasyWG.exe download missing/invalid Windows PE')
    digest=sha(content); verification='official HTTPS release asset; independent checksum unavailable'
    if tag in KNOWN_OFFICIAL_DIGESTS:
        if digest!=KNOWN_OFFICIAL_DIGESTS[tag]: raise RuntimeError('Pinned official release asset hash mismatch for '+tag)
        verification='Verified official release published SHA-256 digest (pinned in builder)'
    if asset.get('digest'):
        expected=asset['digest'];
        if expected.startswith('sha256:'):
            if expected.split(':',1)[1].lower()!=digest:raise RuntimeError('GitHub asset digest mismatch')
            verification='GitHub release asset SHA256 digest verified'
    # Independently published checksum assets take precedence when recognizable.
    sums=[a for a in assets if re.search(r'(sha256|checksums)',a['name'],re.I) and a['id']!=asset['id']]
    for check in sums:
        txt=get(check['browser_download_url']).decode('utf-8-sig',errors='replace')
        m=re.search(r'\b([0-9a-fA-F]{64})\s+\*?(?:EasyWG\.exe|easywg\.exe)\b',txt,re.I)
        if not m and check['name'].lower().startswith('easywg.exe'):
            m=re.search(r'\b([0-9a-fA-F]{64})\b',txt)
        if m:
            if m.group(1).lower()!=digest:raise RuntimeError('Published EasyWG.exe SHA256 mismatch')
            verification='Upstream-published SHA256 checksum asset verified';break
    builder_commit=os.environ.get('GITHUB_SHA','local')
    if builder_commit!='local' and not re.fullmatch(r'[0-9a-f]{40}',builder_commit):
        raise RuntimeError('Invalid builder GITHUB_SHA')
    # Obtain the EXACT stable tagged source, rather than unaudited main.
    source_url=f'https://codeload.github.com/{REPO}/zip/refs/tags/{tag}'
    srcdata=get(source_url,'application/zip')
    with zipfile.ZipFile(io.BytesIO(srcdata)) as z:
        names=z.namelist()
        main=[n for n in names if n.endswith('/src/main.cpp')]
        lic=[n for n in names if n.endswith('/LICENSE')]
        if len(main)!=1 or len(lic)!=1:raise RuntimeError('Tagged source missing main.cpp/LICENSE')
        code=z.read(main[0]); license_text=z.read(lic[0]);
        for proof in (b'GetModuleDirectory()',b'EasyWG.ini',b'SetAutostartRegistry',b'GetTempPathW'):
            if proof not in code:raise RuntimeError(f'Upstream source changed: required portability audit evidence absent: {proof!r}')
    BUILD.mkdir(exist_ok=True)
    (BUILD/'EasyWG.exe').write_bytes(content)
    (BUILD/'UPSTREAM-LICENSE.txt').write_bytes(license_text)
    (BUILD/'upstream-main.cpp').write_bytes(code)
    manifest={'project':REPO,'upstream_tag':tag,'upstream_commit':commit,'upstream_main_cpp_sha256':sha(code),
      'tagged_source_zip_sha256':sha(srcdata),'official_binary_sha256':digest,'official_binary_size':len(content),
      'source_release_asset_url':url,'binary_verification':verification,'builder_revision':REV,'builder_commit':builder_commit,'package_revision':'r1',
      'mode':'PORTABLEAPPS','package_version':tag.lstrip('vV'),'release_tag':f'portable-{tag}-{REV}-{commit[:8]}-{digest[:10]}-{builder_commit[:8]}',
      'shared_installer':'vhick/Portable-Package-Builder@0112c35580e83b37eb8757ebcb949274e1631a04',
      'shared_publisher':'vhick/portable-release-publisher@cb64f86ac2d8c67506db5832de07f9ff58cbeaeb'}
    (BUILD/'identity.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
    out=os.environ.get('GITHUB_OUTPUT')
    if out:
      with open(out,'a',encoding='utf-8') as f:
        for k,v in {'release_tag':manifest['release_tag'],'version':manifest['package_version'],'upstream_sha':commit}.items():f.write(k+'='+v+'\n')

def stage():
    meta=json.loads((BUILD/'identity.json').read_text('utf-8'))
    if STAGE.exists():shutil.rmtree(STAGE)
    for p in ('App/AppInfo','App/EasyWG','Data/Runtime','Other/Source'):(STAGE/p).mkdir(parents=True,exist_ok=True)
    shutil.copy2(BUILD/'EasyWG.exe',STAGE/'App/EasyWG/EasyWG.exe')
    shutil.copy2(BUILD/'UPSTREAM-LICENSE.txt',STAGE/'Other/Source/UPSTREAM-LICENSE.txt')
    shutil.copy2(ROOT/'src/EasyWGPortable.cpp',STAGE/'Other/Source/EasyWGPortable.cpp')
    shutil.copy2(ROOT/'src/EasyWGPortable.rc',STAGE/'Other/Source/EasyWGPortable.rc')
    (STAGE/'Other/Source/BUILD-IDENTITY.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (STAGE/'README.txt').write_text((ROOT/'docs/PORTABLE-RUNTIME.txt').read_text('utf-8'),encoding='utf-8')
    cfg=f'''[Format]\nType=PortableApps.comFormat\nVersion=3.8\n\n[Details]\nName=EasyWG Portable (Unofficial Community Package)\nAppID=EasyWGPortableUnofficial\nPublisher=Terence0816 / independent community package\nHomepage=https://github.com/Terence0816/easy-wg-portable\nCategory=Utilities\nDescription=Portable WireGuard quick-connect client; requires admin for tunnel service\nLanguage=Multilingual\nTrademarks=WireGuard is a trademark of Jason A. Donenfeld; not an official WireGuard release\n\n[License]\nShareable=true\nOpenSource=true\nFreeware=true\nCommercialUse=true\n\n[Version]\nPackageVersion={meta['package_version']}\nDisplayVersion={meta['package_version']} ({REV})\n\n[Control]\nIcons=1\nStart=EasyWGPortable.exe\n\n[Associations]\n; No automatic file or protocol registration\n'''
    (STAGE/'App/AppInfo/appinfo.ini').write_text(cfg,encoding='utf-8')
    print('STAGED',STAGE)

def pe(path):
    b=path.read_bytes();
    if len(b)<0x100 or b[:2]!=b'MZ':raise RuntimeError(f'Invalid PE MZ: {path}')
    off=struct.unpack_from('<I',b,0x3c)[0]
    if off+6>len(b) or b[off:off+4]!=b'PE\0\0':raise RuntimeError(f'Invalid PE signature: {path}')
    arch=struct.unpack_from('<H',b,off+4)[0]
    if arch not in (0x14c,0x8664):raise RuntimeError(f'Unexpected architecture 0x{arch:04x}: {path}')
    return arch

def validate():
    meta=json.loads((BUILD/'identity.json').read_text('utf-8'))
    required=[STAGE/'EasyWGPortable.exe',STAGE/'App/EasyWG/EasyWG.exe',STAGE/'App/AppInfo/appinfo.ini',
              STAGE/'App/AppInfo/appicon.ico',STAGE/'App/AppInfo/appicon_16.png',STAGE/'App/AppInfo/appicon_32.png',
              STAGE/'Other/Source/UPSTREAM-LICENSE.txt',STAGE/'Other/Source/BUILD-IDENTITY.json']
    for p in required:
        if not p.is_file() or p.stat().st_size==0:raise RuntimeError(f'Missing/empty {p}')
    if not (STAGE/'Data/Runtime').is_dir():raise RuntimeError('Data/Runtime missing')
    if pe(required[0]) != 0x8664:raise RuntimeError('Launcher is not x64')
    if pe(required[1]) != 0x8664:raise RuntimeError('Upstream EasyWG binary is not x64')
    if sha(required[1].read_bytes())!=meta['official_binary_sha256']:raise RuntimeError('Upstream PE bytes changed')
    ini=configparser.ConfigParser(interpolation=None);ini.read(required[2],encoding='utf-8')
    if ini['Control'].get('Start')!='EasyWGPortable.exe' or ini['Version'].get('PackageVersion')!=meta['package_version']:
        raise RuntimeError('Invalid PortableApps metadata')
    if required[3].read_bytes()[:4]!=b'\0\0\1\0':raise RuntimeError('Invalid ico header')
    for p,sz in [(required[4],16),(required[5],32)]:
        b=p.read_bytes()
        if b[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack_from('>II',b,16)!=(sz,sz):
            raise RuntimeError(f'Icon PNG invalid size: {p}')
    if list((STAGE/'Data').rglob('*.conf')):raise RuntimeError('Unexpected private WireGuard profile in package')
    DIST.mkdir(exist_ok=True)
    out=DIST/f'EasyWGPortable-{meta["upstream_tag"]}-{REV}.zip'
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(STAGE.rglob('*')):
            arc=STAGE.name+'/'+str(p.relative_to(STAGE)).replace('\\','/')
            if p.is_dir():z.writestr(arc.rstrip('/')+'/',b'')
            else:z.write(p,arc)
    with zipfile.ZipFile(out) as z:
        bad=z.testzip();
        if bad:raise RuntimeError('ZIP CRC error in '+bad)
        names=set(z.namelist())
        if f'{STAGE.name}/EasyWGPortable.exe' not in names or f'{STAGE.name}/Data/Runtime/' not in names:
            raise RuntimeError('ZIP root/layout invalid')
    print('VALIDATED ZIP',out,sha(out.read_bytes()))
    (DIST/'zip.sha256').write_text(f'{sha(out.read_bytes())}  {out.name}\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['resolve','stage','validate']);ap.add_argument('--version',default='latest');a=ap.parse_args()
    if a.phase=='resolve':resolve(a.version)
    elif a.phase=='stage':stage()
    else:validate()
if __name__=='__main__':main()
