"""Headless NSIS integrity checks; does NOT claim interactive installation passed."""
import hashlib,pathlib,subprocess,sys,re,shutil,os
from release import pe
f=pathlib.Path(sys.argv[1]); expected=sys.argv[2].lower()
if not f.is_file() or f.suffix.lower()!='.exe':raise RuntimeError('Installer missing')
if pe(f) not in (0x14c,0x8664):raise RuntimeError('Unexpected installer PE architecture')
actual=hashlib.sha256(f.read_bytes()).hexdigest()
if actual!=expected:raise RuntimeError('Shared builder installer digest mismatch')
print(f'VALIDATED installer PE and SHA256: {f.name} {actual}')
seven=shutil.which('7z') or next((str(p) for p in [pathlib.Path(os.environ.get('ProgramFiles','C:/Program Files'))/'7-Zip/7z.exe',pathlib.Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'7-Zip/7z.exe'] if p.exists()),None)
if not seven:raise RuntimeError('Cannot locate installed 7z for embedded installer inspection')
p=subprocess.run([seven,'l','-slt',str(f)],capture_output=True,text=True,errors='replace',timeout=120)
if p.returncode!=0:raise RuntimeError('Cannot verify installer embedded payload using 7z; refuse publication')
body=p.stdout.replace('\\','/').lower()
for item in ('easywgportable.exe','appinfo.ini','easywg.exe'):
 if item not in body:raise RuntimeError('Installer payload missing '+item)
print('VALIDATED embedded installer file names (not actual installation behavior)')
