$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$root = Resolve-Path (Join-Path $PSScriptRoot '..')
$exe = Join-Path $root 'build\EasyWG.exe'
$dest = Join-Path $root 'build\EasyWGPortable\App\AppInfo'
if (-not (Test-Path -LiteralPath $exe)) { throw 'Missing official EasyWG executable' }
$icon = [System.Drawing.Icon]::ExtractAssociatedIcon($exe)
if ($null -eq $icon) { throw 'Unable to extract authentic upstream application icon' }
try {
    $file = [System.IO.File]::Open((Join-Path $dest 'appicon.ico'), [System.IO.FileMode]::Create)
    try { $icon.Save($file) } finally { $file.Dispose() }
    $sourceBitmap = $icon.ToBitmap()
    try {
        foreach ($size in @(16, 32)) {
            $bmp = [System.Drawing.Bitmap]::new($sourceBitmap, [int]$size, [int]$size)
            try { $bmp.Save((Join-Path $dest "appicon_$size.png"), [System.Drawing.Imaging.ImageFormat]::Png) }
            finally { $bmp.Dispose() }
        }
    } finally { $sourceBitmap.Dispose() }
    Copy-Item -LiteralPath (Join-Path $dest 'appicon.ico') -Destination (Join-Path $root 'src\appicon.ico') -Force
} finally { $icon.Dispose() }
