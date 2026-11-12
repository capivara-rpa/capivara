; Inno Setup — instalador "tudo empacotado" (Windows) da Control Room + Agente.
; Requer: Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
; Pré-requisito: buildar os binários com
;     pyinstaller --noconfirm packaging/control_room.spec
;     pyinstaller --noconfirm packaging/agente.spec
; Depois compilar: iscc packaging/inno_setup.iss
;
; Gera dist\instalador\control_room_instalador.exe, que instala:
;   - Control Room (control_room.exe)
;   - Agente (robo_agente.exe) — com opção de iniciar junto com o Windows
;   - Extensão TrackTab (pasta tracktab\)
;   - Scripts iniciar_control_room.cmd / iniciar_agente.cmd (definem RPA_PASTA_DADOS)

#define MeuAppNome "Control Room RPA Brasil"
#define MeuAppVersao "1.0.0"
#define MeuAppEditor "Comunidade Python RPA Brasil"
#define MeuAppExe "control_room.exe"
#define MeuAgenteExe "robo_agente.exe"
#define OrigemExe "..\dist\control_room.exe"
#define OrigemAgente "..\dist\robo_agente.exe"
#define OrigemTrackTab "..\tracktab"

[Setup]
AppId={{E14A4B57-0F3B-4A64-8B2C-73D9C2F0A1DE}
AppName={#MeuAppNome}
AppVersion={#MeuAppVersao}
AppPublisher={#MeuAppEditor}
DefaultDirName={autopf}\TemplatePythonRPA
DefaultGroupName={#MeuAppNome}
OutputDir=..\dist\instalador
OutputBaseFilename=control_room_instalador
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes
DisableProgramGroupPage=yes
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "agente_autostart"; Description: "Iniciar o Agente automaticamente com o Windows"; GroupDescription: "Agente (worker):"; Flags: checkedonce

[Dirs]
; Dados persistentes (bancos, logs e vault) ao lado do instalador
Name: "{app}\data"

[Files]
Source: "{#OrigemExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#OrigemAgente}"; DestDir: "{app}"; Flags: ignoreversion
Source: "iniciar_control_room.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "iniciar_agente.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\.env.example"; DestDir: "{app}"; DestName: ".env.example"; Flags: ignoreversion
; Extensão TrackTab (para carregar em chrome://extensions -> "Carregar sem compactação")
Source: "{#OrigemTrackTab}\*"; DestDir: "{app}\tracktab"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MeuAppNome}"; Filename: "{app}\iniciar_control_room.cmd"
Name: "{group}\Agente (manual)"; Filename: "{app}\iniciar_agente.cmd"
Name: "{group}\Extensão TrackTab (abrir pasta)"; Filename: "{app}\tracktab"
Name: "{group}\Desinstalar {#MeuAppNome}"; Filename: "{uninstallexe}"
; Atalho na inicialização do usuário (equivale a "serviço" do agente)
Name: "{userstartup}\Agente RPA Brasil"; Filename: "{app}\iniciar_agente.cmd"; Tasks: agente_autostart

[Run]
Filename: "{app}\iniciar_control_room.cmd"; Description: "Iniciar a Control Room agora"; Flags: nowait postinstall skipifsilent
Filename: "{app}\iniciar_agente.cmd"; Description: "Iniciar o Agente agora"; Flags: nowait postinstall skipifsilent unchecked
