[Setup]
AppId={{E8A4F3A5-4C61-4BE2-9A2E-DBD0-DBEAST-0150}
AppName=DownloadBeast
AppVersion=1.5
DefaultDirName={autopf}\DownloadBeast
DefaultGroupName=DownloadBeast
UninstallDisplayIcon={app}\DownloadBeast.exe
SetupIconFile=C:\Build\Beast\beast_icon.ico
OutputDir=C:\Build\Installer
OutputBaseFilename=DownloadBeast-Setup-v1.5
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "C:\Build\Beast\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checkablealone

[Icons]
Name: "{group}\DownloadBeast"; Filename: "{app}\DownloadBeast.exe"; IconFilename: "C:\Build\Beast\beast_icon.ico"
Name: "{commondesktop}\DownloadBeast"; Filename: "{app}\DownloadBeast.exe"; Tasks: desktopicon; IconFilename: "C:\Build\Beast\beast_icon.ico"

[Run]
Filename: "{app}\DownloadBeast.exe"; Description: "Launch DownloadBeast"; Flags: nowait postinstall skipifsilent
