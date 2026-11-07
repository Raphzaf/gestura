; Inno Setup script for Gestura (https://jrsoftware.org/isinfo.php)
; 1. Build the app:      pyinstaller --noconfirm gestura.spec
; 2. Build the installer: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\gestura.iss
; Output: installer\Output\Gestura-Setup-<version>.exe  (per-user install, no admin rights)

#define AppName "Gestura"
#ifndef AppVersion
  #define AppVersion "0.2.0"
#endif
#define AppExe "Gestura.exe"

[Setup]
AppId={{6E3C9B7A-2F1D-4C8E-9B57-4C1E7A0D9F21}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Gestura contributors
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
OutputBaseFilename=Gestura-Setup-{#AppVersion}
SetupIconFile=..\gestura\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "..\dist\Gestura\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Remove the launch-at-login entry if the user enabled it
Filename: "reg.exe"; Parameters: "delete HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v Gestura /f"; Flags: runhidden; RunOnceId: "RemoveRunKey"
