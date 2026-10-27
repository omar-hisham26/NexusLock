; Script generated for NexusLock
; Inno Setup Script - Creates a professional Windows Setup Wizard with Next/Browse/Install/Uninstall

#define MyAppName "NexusLock"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "omar-hisham26"
#define MyAppURL "https://github.com/omar-hisham26/NexusLock"
#define MyAppExeName "NexusLock.exe"

[Setup]
AppId={{C6B4E5F7-4E7B-49C2-B835-64DF8B46C9E1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Destination Folder (User can change directory with Browse button)
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
AllowNoIcons=yes

; Administrator privileges required for firewall management
PrivilegesRequired=admin
WizardStyle=modern
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\assets\icon.ico

; High compression
Compression=lzma2/ultra64
SolidCompression=yes

; Output file settings
OutputDir=.
OutputBaseFilename=NexusLock-Setup

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
