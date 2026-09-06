; Inno Setup 6 script for XVG Plotter (SPEC §12).
; Input: dist\XVGPlotter.exe produced by packaging\build.py
; Output: packaging\windows\Output\XVGPlotter-Setup.exe
; Installs per-user (no admin), creates Start Menu + Desktop shortcuts,
; optionally registers .xvg file association.

#define MyAppName "XVG Plotter"
#define MyAppVersion "1.0.0"
#define MyAppExe "XVGPlotter.exe"

[Setup]
AppId={{7C1B6E4A-52D8-4B0F-9E3A-XVGPLOTTER01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=XVG Plotter
DefaultDirName={autopf}\XVGPlotter
DefaultGroupName={#MyAppName}
OutputBaseFilename=XVGPlotter-Setup
OutputDir=Output
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ChangesAssociations=yes
SetupIconFile=..\..\src\xvg_plotter\assets\icon.ico
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a &Desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "assoc"; Description: "Open .xvg files with {#MyAppName} by default"; \
    GroupDescription: "File association:"; Flags: unchecked

[Files]
Source: "..\..\dist\XVGPlotter.exe"; DestDir: "{app}"; Flags: ignoreversion

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
