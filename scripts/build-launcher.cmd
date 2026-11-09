@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" (echo ERROR: vswhere is missing & exit /b 1)
set "VSROOT="
for /f "usebackq delims=" %%V in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSROOT=%%V"
if not defined VSROOT (echo ERROR: no Visual C++ toolchain found & exit /b 2)
call "%VSROOT%\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 3
rc /nologo /I "src" /fo"build\EasyWGPortable.res" "src\EasyWGPortable.rc"
if errorlevel 1 exit /b 4
cl /nologo /std:c++17 /EHsc /utf-8 /O2 /W4 /MT /DUNICODE /D_UNICODE "src\EasyWGPortable.cpp" "build\EasyWGPortable.res" /link /SUBSYSTEM:WINDOWS /OUT:"build\EasyWGPortable\EasyWGPortable.exe"
if errorlevel 1 exit /b 5
if not exist "build\EasyWGPortable\EasyWGPortable.exe" exit /b 6
exit /b 0
