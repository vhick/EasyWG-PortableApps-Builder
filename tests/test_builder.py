"""Offline non-destructive regression fixtures: does not claim real Windows runtime."""
import importlib.util, pathlib, struct, sys, tempfile, unittest, zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('easywg_release',ROOT/'scripts/release.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class BuilderTests(unittest.TestCase):
 def test_version_numeric_4_parts(self):
  self.assertGreater(module.stable('v0.2.8.10'),module.stable('v0.2.8.8'))
  self.assertGreater(module.stable('v0.2.9.2'),module.stable('v0.2.8.10'))
  self.assertIsNone(module.stable('core-v1'))
  self.assertIsNone(module.stable('v0.2.9.2-rc1'))
  self.assertIsNone(module.stable('nightly'))
 def test_pe_parser(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp)/'fixture.exe'
   b=bytearray(256);b[:2]=b'MZ';struct.pack_into('<I',b,0x3c,0x80);b[0x80:0x84]=b'PE\0\0'
   struct.pack_into('<H',b,0x84,0x8664);p.write_bytes(b)
   self.assertEqual(module.pe(p),0x8664)
   b[0x80]=0;p.write_bytes(b)
   with self.assertRaises(RuntimeError):module.pe(p)
 def test_release_source_contract_present(self):
  text=(ROOT/'scripts/release.py').read_text('utf-8')
  for value in ('EasyWG.exe','GetModuleDirectory()', 'SetAutostartRegistry','official_binary_sha256','tagged_source_zip_sha256'):
   self.assertIn(value,text)
 def test_launcher_safety_guards(self):
  text=(ROOT/'src/EasyWGPortable.cpp').read_text('utf-8')
  for value in ('Data', 'Runtime', 'runningRuntime', 'FILE_ATTRIBUTE_REPARSE_POINT', 'Run', 'MoveFileExW','CreateProcessW'):
   self.assertIn(value,text)
  self.assertNotIn('TerminateProcess(',text)
  self.assertNotIn('RegDeleteTree',text)
  self.assertNotIn('RemoveDirectoryW(',text)
 def test_workflow_safety(self):
  txt=(ROOT/'.github/workflows/build-easywg-portableapps.yml').read_text('utf-8')
  self.assertIn('vhick/Portable-Package-Builder@0112c35580e83b37eb8757ebcb949274e1631a04',txt)
  self.assertIn('vhick/portable-release-publisher@cb64f86ac2d8c67506db5832de07f9ff58cbeaeb',txt)
  self.assertIn('dry-run: \'true\'',txt)
  self.assertIn('dry-run: \'false\'',txt)
  self.assertIn('prune: \'false\'',txt)
  self.assertNotIn('ubuntu-latest',txt)
if __name__=='__main__':unittest.main()
