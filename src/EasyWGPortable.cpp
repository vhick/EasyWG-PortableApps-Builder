// EasyWGPortable launcher - transparent Windows C++17 application-specific wrapper.
// Upstream EasyWG.exe is officially released by Terence0816. Its source GetIniPath()
// and imported-config code use GetModuleDirectory(), thus execution inside Data/Runtime
// keeps all module-relative writable state under portable Data, before launch.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <tlhelp32.h>
#include <shlwapi.h>
#include <shellapi.h>
#include <functional>
#include <cstring>
#include <stdexcept>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>
#include <cwctype>
// Windows MessageBoxW is implemented by User32.lib, not the C++ runtime.
#pragma comment(lib, "user32.lib")
#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "advapi32.lib")
namespace fs = std::filesystem;

static void Alert(const std::wstring& message) {
    MessageBoxW(nullptr, message.c_str(), L"EasyWG Portable (Community Package)", MB_OK | MB_ICONWARNING);
}
static std::wstring quote(const std::wstring& s) {
    std::wstring o=L"\""; size_t slash=0;
    for (wchar_t c: s) {
        if (c==L'\\') { ++slash; continue; }
        if (c==L'\"') {o.append(slash*2+1,L'\\'); o+=c;}
        else {o.append(slash,L'\\'); o+=c;}
        slash=0;
    }
    o.append(slash*2,L'\\'); o+=L'\"'; return o;
}
static fs::path moduleDir() {
    std::vector<wchar_t> b(32768); DWORD n=GetModuleFileNameW(nullptr,b.data(),(DWORD)b.size());
    if (!n || n>=b.size()) throw std::runtime_error("Unable to resolve module path");
    return fs::path(std::wstring(b.data(),n)).parent_path();
}
static bool samePath(const fs::path& a, const fs::path& b) {
    std::wstring x=a.lexically_normal().wstring(), y=b.lexically_normal().wstring();
    return _wcsicmp(x.c_str(),y.c_str())==0;
}
static bool isReparse(const fs::path& p) {
    DWORD a=GetFileAttributesW(p.c_str()); return a!=INVALID_FILE_ATTRIBUTES && (a&FILE_ATTRIBUTE_REPARSE_POINT)!=0;
}
static bool filesEqual(const fs::path& a,const fs::path& b) {
    if (!fs::exists(a) || !fs::exists(b) || fs::file_size(a)!=fs::file_size(b)) return false;
    std::ifstream one(a,std::ios::binary), two(b,std::ios::binary);
    char x[65536],y[65536];
    while(one && two) {
        one.read(x,sizeof(x)); two.read(y,sizeof(y));
        auto n=one.gcount(); if(n!=two.gcount() || memcmp(x,y,(size_t)n)!=0) return false;
    }
    return true;
}
static bool runningRuntime(const fs::path& target) {
    HANDLE snap=CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0); if(snap==INVALID_HANDLE_VALUE)return false;
    PROCESSENTRY32W e{}; e.dwSize=sizeof(e); bool found=false;
    if (Process32FirstW(snap,&e)) do {
        if (_wcsicmp(e.szExeFile,L"EasyWG.exe")!=0) continue;
        HANDLE h=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,FALSE,e.th32ProcessID);
        if (!h) continue;
        std::vector<wchar_t> buf(32768); DWORD n=(DWORD)buf.size();
        if(QueryFullProcessImageNameW(h,0,buf.data(),&n)) {
            if(samePath(fs::path(std::wstring(buf.data(),n)),target)) found=true;
        }
        CloseHandle(h); if(found)break;
    }while(Process32NextW(snap,&e));
    CloseHandle(snap); return found;
}
static std::wstring getRunValue() {
    HKEY key=nullptr; if(RegOpenKeyExW(HKEY_CURRENT_USER,L"Software\\Microsoft\\Windows\\CurrentVersion\\Run",0,KEY_QUERY_VALUE,&key)!=ERROR_SUCCESS)return L"";
    DWORD type=0,sz=0; LONG rc=RegQueryValueExW(key,L"EasyWG Portable",nullptr,&type,nullptr,&sz);
    if(rc!=ERROR_SUCCESS || type!=REG_SZ || sz==0 || sz>32768) { RegCloseKey(key);return L""; }
    std::vector<BYTE> buf(sz+sizeof(wchar_t),0); rc=RegQueryValueExW(key,L"EasyWG Portable",nullptr,&type,buf.data(),&sz);
    RegCloseKey(key); if(rc!=ERROR_SUCCESS)return L"";
    return std::wstring((wchar_t*)buf.data());
}
static bool setRunValue(const std::wstring& text) {
    HKEY key=nullptr; if(RegCreateKeyExW(HKEY_CURRENT_USER,L"Software\\Microsoft\\Windows\\CurrentVersion\\Run",0,nullptr,0,KEY_SET_VALUE,nullptr,&key,nullptr)!=ERROR_SUCCESS)return false;
    const LONG r=RegSetValueExW(key,L"EasyWG Portable",0,REG_SZ,(const BYTE*)text.c_str(),(DWORD)((text.size()+1)*sizeof(wchar_t)));
    RegCloseKey(key); return r==ERROR_SUCCESS;
}
static void logLine(const fs::path& data,const std::wstring& msg) {
    // Avoid persisting credential-bearing profile data or raw command-line arguments.
    std::wofstream f(data/L"launcher.log",std::ios::app); if(f)f<<msg<<L"\n";
}
static std::wstring makeCmd(const fs::path& app, const std::vector<std::wstring>& args) {
    std::wstring cmd=quote(app.wstring()); for(auto& arg:args)cmd+=L" "+quote(arg);return cmd;
}
static int run(HINSTANCE, int) {
    const fs::path root=moduleDir();
    const fs::path src=root/L"App"/L"EasyWG"/L"EasyWG.exe";
    const fs::path data=root/L"Data"; const fs::path runtime=data/L"Runtime";
    const fs::path target=runtime/L"EasyWG.exe";
    if (!fs::is_regular_file(src)) {Alert(L"The official EasyWG.exe is missing from App\\EasyWG. Package is incomplete.");return 2;}
    // Keep the only mutable copy of EasyWG.exe and ALL its companion files in Data.
    if (isReparse(data) || isReparse(runtime)) {Alert(L"Data or Data\\Runtime is a junction/symlink. Refusing unsafe redirection.");return 3;}
    fs::create_directories(runtime);
    const std::wstring mutexName=L"Local\\EasyWGPAFLauncher_"+std::to_wstring(std::hash<std::wstring>{}(root.wstring()));
    HANDLE mutex=CreateMutexW(nullptr,TRUE,mutexName.c_str());
    if(!mutex || GetLastError()==ERROR_ALREADY_EXISTS){Alert(L"This portable package is already being launched. Use the existing window/tray icon.");if(mutex)CloseHandle(mutex);return 4;}
    if(runningRuntime(target)){Alert(L"EasyWG is already running from this portable Data folder. Exit its tray icon first.");ReleaseMutex(mutex);CloseHandle(mutex);return 5;}
    if (!filesEqual(src,target)) {
        // Preserve the previous executable for recovery, and never remove user configs or DLLs.
        if(fs::exists(target)) {
            fs::create_directories(data/L"Backups");
            fs::path backup=data/L"Backups"/L"EasyWG.previous.exe";
            if(!fs::exists(backup))fs::copy_file(target,backup,fs::copy_options::none);
        }
        fs::path tmp=runtime/L"EasyWG.stage.exe";
        if(fs::exists(tmp))fs::remove(tmp);
        fs::copy_file(src,tmp,fs::copy_options::none);
        if (!filesEqual(src,tmp)) {fs::remove(tmp);throw std::runtime_error("Staged executable failed byte comparison");}
        if(!MoveFileExW(tmp.c_str(),target.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))
            throw std::runtime_error("Cannot replace runtime binary; close EasyWG before upgrading");
    }
    // Snapshot the ONLY source-evidenced HKCU Run value. Never touch unrelated keys.
    const std::wstring prior=getRunValue();
    std::vector<std::wstring> args;
    int argc=0; LPWSTR* argv=CommandLineToArgvW(GetCommandLineW(),&argc);
    if(argv) {for(int i=1;i<argc;++i)args.emplace_back(argv[i]); LocalFree(argv);}
    std::wstring cmd=makeCmd(target,args); std::vector<wchar_t> mutableCmd(cmd.begin(),cmd.end()); mutableCmd.push_back(L'\0');
    STARTUPINFOW si{}; si.cb=sizeof(si); PROCESS_INFORMATION pi{};
    std::wstring working=runtime.wstring();
    if (!CreateProcessW(target.c_str(),mutableCmd.data(),nullptr,nullptr,FALSE,0,nullptr,working.c_str(),&si,&pi)) {
        Alert(L"Cannot launch EasyWG.exe from Data\\Runtime. Check Windows Security and the package files.");
        ReleaseMutex(mutex);CloseHandle(mutex);return 6;
    }
    CloseHandle(pi.hThread);
    DWORD wait=WaitForSingleObject(pi.hProcess,INFINITE), code=1;
    if(wait==WAIT_OBJECT_0)GetExitCodeProcess(pi.hProcess,&code);
    CloseHandle(pi.hProcess);
    // Upstream can hand off to /restart-helper and /restarted. Keep launcher alive
    // while another accessible EasyWG.exe from the SAME Data runtime is present.
    int quiet=0;
    for (int i=0;i<3600 && quiet<5;++i) {
        Sleep(1000);
        if(runningRuntime(target))quiet=0; else ++quiet;
    }
    // Upstream AutoStart option is intentional HKCU integration. If it wrote
    // its OWN runtime exe, rewrite to root launcher (correct upgrades/login).
    // If a different pre-existing app owns this same value name, restore it
    // only when current value exactly equals the app-owned expected command.
    const std::wstring current=getRunValue();
    const std::wstring rawOwned=quote(target.wstring())+L" /autostart";
    if (_wcsicmp(current.c_str(),rawOwned.c_str())==0) {
        if(!prior.empty() && _wcsicmp(prior.c_str(),rawOwned.c_str())!=0 &&
            _wcsicmp(prior.c_str(),(quote((root/L"EasyWGPortable.exe").wstring())+L" /autostart").c_str())!=0) {
            if(!setRunValue(prior))logLine(data,L"WARNING: Could not restore previous same-name HKCU Run value");
        } else {
            if(!setRunValue(quote((root/L"EasyWGPortable.exe").wstring())+L" /autostart"))
                logLine(data,L"WARNING: Could not adjust approved autostart entry to root launcher");
        }
    } else if(current.empty() && !prior.empty()) {
        // Respect the user's explicit choice to DISABLE portable autostart.
        // Restore only a Run value belonging to some OTHER pre-existing app.
        const std::wstring ourRoot=quote((root/L"EasyWGPortable.exe").wstring())+L" /autostart";
        if (_wcsicmp(prior.c_str(),ourRoot.c_str())!=0 &&
            _wcsicmp(prior.c_str(),rawOwned.c_str())!=0) {
            if(!setRunValue(prior)) logLine(data,L"WARNING: Could not restore prior HKCU Run entry");
        }
    }
    ReleaseMutex(mutex);CloseHandle(mutex);
    return (int)code;
}
int WINAPI wWinMain(HINSTANCE h,HINSTANCE,LPWSTR,int show) {
    try {return run(h,show);}
    catch(const std::exception& e){Alert(L"Portable launcher stopped safely. Details: "+std::wstring(e.what(),e.what()+strlen(e.what())));return 1;}
}
