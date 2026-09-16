; Inno Setup script — compile on Windows with ISCC.exe when you want Setup.exe.
; Daily use after install is still START_FILM_LAB.bat (no PowerShell).
; PrivilegesRequired=lowest so it installs per-user like a game in AppData.

#define MyAppName "Film Lab"
#define MyAppVersion "1.0"
#define MyAppPublisher "Film Lab"
#define MyAppURL "http://127.0.0.1:43123"
#define MyAppExe "START_FILM_LAB.bat"

[Setup]
AppId={{8F1A0C3E-4B2D-4E9A-9C11-A1B2C3D4E5F6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={localappdata}\Film Lab
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Install_Film_Lab
SetupIconFile=..\assets\film_lab.ico
UninstallDisplayIcon={app}\assets\film_lab.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=..\LICENSE.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop icon"; GroupDescription: "Icons:"; Flags: checkedonce

[Files]
Source: "..\START_FILM_LAB.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\START.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\REPAIR.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\INSTALL_FILM_LAB.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Install Film Lab.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\UNINSTALL_FILM_LAB.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\START_HERE.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\HOME.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs
Source: "..\film_lab\*"; DestDir: "{app}\film_lab"; Flags: ignoreversion recursesubdirs
Source: "..\scripts\*"; DestDir: "{app}\scripts"; Flags: ignoreversion recursesubdirs
Source: "..\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs
Source: "..\workflows\*"; DestDir: "{app}\workflows"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\data\characters\*"; DestDir: "{app}\data\characters"; Flags: ignoreversion recursesubdirs skipifsourcedoesntexist

[Icons]
Name: "{autodesktop}\Film Lab"; Filename: "{app}\{#MyAppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\film_lab.ico"; Tasks: desktopicon
Name: "{group}\Film Lab"; Filename: "{app}\{#MyAppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\film_lab.ico"
Name: "{group}\Repair"; Filename: "{app}\REPAIR.bat"; WorkingDir: "{app}"; IconFilename: "{app}\assets\film_lab.ico"
Name: "{group}\Uninstall Film Lab"; Filename: "{app}\UNINSTALL_FILM_LAB.bat"; WorkingDir: "{app}"; IconFilename: "{app}\assets\film_lab.ico"

[Run]
Filename: "{app}\INSTALL_FILM_LAB.bat"; Description: "Install Python packages + pin Desktop icon"; Flags: postinstall skipifsilent shelledit
Filename: "{app}\{#MyAppExe}"; Description: "Start Film Lab"; Flags: nowait postinstall skipifsilent unchecked
