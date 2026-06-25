[Setup]
AppName=Stampa SaaS
AppVersion=1.0
DefaultDirName={pf}\Stampa SaaS
DefaultGroupName=Stampa SaaS
UninstallDisplayName=DesinstaladorGeral - Stampa SaaS
OutputBaseFilename=StampaSaaSInstaller
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\StampaSaaS.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "LOGO.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Stampa SaaS"; Filename: "{app}\StampaSaaS.exe"; WorkingDir: "{app}"; IconFilename: "{app}\LOGO.ico"
Name: "{userdesktop}\Stampa SaaS"; Filename: "{app}\StampaSaaS.exe"; WorkingDir: "{app}"; IconFilename: "{app}\LOGO.ico"
Name: "{group}\DesinstaladorGeral"; Filename: "{uninstallexe}"; WorkingDir: "{app}"; IconFilename: "{app}\LOGO.ico"

[Run]
Filename: "{app}\StampaSaaS.exe"; Description: "Executar Stampa SaaS"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\Stampa_SaaS"
