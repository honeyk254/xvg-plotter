; Inno Setup 6 script for XVG Plotter (SPEC §12).
; Inputs (all optional, passed by packaging\build.py):
;   /DAPP_VERSION=<ver>   version string (default: keep in sync with version.py)
;   /DONEDIR              installer wraps dist\XVGPlotter\ (onedir build)
;   /DMACHINE             per-machine installer variant (admin; default: per-user)
; Output: packaging\windows\Output\XVGPlotter-Setup-<ver>[-machine].exe
; Per-user install (no admin) by default; creates Start Menu + Desktop
; shortcuts; optionally registers the .xvg file association (unchecked task).

#define MyAppName "XVG Plotter"
#ifndef APP_VERSION
#define APP_VERSION "1.0.1"
#endif
#define MyAppExe "XVGPlotter.exe"

[Setup]
AppId={{7C1B6E4A-52D8-4B0F-9E3A-XVGPLOTTER01}
AppName={#MyAppName}
AppVersion={#APP_VERSION}
AppPublisher=XVG Plotter
DefaultDirName={autopf}\XVGPlotter
DefaultGroupName={#MyAppName}
#ifdef MACHINE
OutputBaseFilename=XVGPlotter-Setup-{#APP_VERSION}-machine
#else
OutputBaseFilename=XVGPlotter-Setup-{#APP_VERSION}
#endif
OutputDir=Output
Compression=lzma2
SolidCompression=yes
#ifdef MACHINE
PrivilegesRequired=admin
#else
PrivilegesRequired=lowest
#endif
ChangesAssociations=yes
SetupIconFile=..\..\src\xvg_plotter\assets\icon.ico
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a &Desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "assoc"; Description: "Open .xvg files with {#MyAppName} by default"; \
    GroupDescription: "File association:"; Flags: unchecked

#ifdef ONEDIR
[Files]
Source: "..\..\dist\XVGPlotter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#else
[Files]
Source: "..\..\dist\XVGPlotter.exe"; DestDir: "{app}"; Flags: ignoreversion
#endif

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Classes\XVGPlotter.xvg"; ValueType: string; \
    ValueData: "GROMACS XVG plot"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\XVGPlotter.xvg\DefaultIcon"; ValueType: string; \
    ValueData: "{app}\{#MyAppExe},0"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\XVGPlotter.xvg\shell\open\command"; ValueType: string; \
    ValueData: """{app}\{#MyAppExe}"" ""%1"""; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\.xvg\OpenWithProgids"; ValueType: string; \
    ValueName: "XVGPlotter.xvg"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assoc

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "Launch {#MyAppName}"; \
    Flags: nowait postinstall skipifsilent
