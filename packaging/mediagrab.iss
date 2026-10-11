; Inno Setup script for the self-contained Windows build (v2.4.0 work).
;
;   python packaging/build_windows.py
;   ISCC /DAppVersion=2.4.0 packaging/mediagrab.iss      -> dist\MediaGrabSetup-2.4.0.exe
;
; NOTE: per-user install (PrivilegesRequired=lowest): no UAC prompt, and the
; embedded Python stays writable so Settings -> "update yt-dlp" keeps working
; - under Program Files it would need admin rights for every pip install.
; {autopf} resolves to %LOCALAPPDATA%\Programs for a per-user install.

#ifndef AppVersion
  #error Pass the version: ISCC /DAppVersion=x.y.z packaging/mediagrab.iss
#endif

[Setup]
; NOTE: AppId is what Windows uses to recognise MediaGrab across versions
; (upgrades in place, one entry in Installed apps) - never change it.
AppId={{9D9F945E-00A3-4FD0-BAC8-0D5E524BE292}
AppName=MediaGrab
AppVersion={#AppVersion}
AppVerName=MediaGrab {#AppVersion}
AppPublisher=umitkrkmz
AppPublisherURL=https://github.com/umitkrkmz/mediagrab
AppSupportURL=https://github.com/umitkrkmz/mediagrab/issues
AppUpdatesURL=https://github.com/umitkrkmz/mediagrab/releases
; NOTE: shown in the setup exe's Properties -> Details tab only. SmartScreen's
; "Unknown publisher" comes from an Authenticode signature, not from these -
; only code signing changes that (see ROADMAP: code-signing research).
VersionInfoCompany=umitkrkmz
VersionInfoDescription=MediaGrab Setup
VersionInfoProductName=MediaGrab
VersionInfoCopyright=GPL-3.0-or-later - github.com/umitkrkmz/mediagrab
DefaultDirName={autopf}\MediaGrab
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
ShowLanguageDialog=auto
Compression=lzma2/ultra64
SolidCompression=yes
OutputDir=..\dist
OutputBaseFilename=MediaGrabSetup-{#AppVersion}
UninstallDisplayName=MediaGrab
UninstallDisplayIcon={app}\python\pythonw.exe
; NOTE: a running MediaGrab holds python314.dll and friends open - let the
; Windows Restart Manager close it before files are replaced or removed.
CloseApplications=yes

; NOTE: English FIRST - Inno picks the language matching Windows' UI language
; and falls back to the first entry; with Turkish first, a German Windows would
; have got a Turkish installer. ShowLanguageDialog=auto (in [Setup]) skips the picker
; whenever there's a match, so Turkish and English users never see it.
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Messages]
; NOTE: Inno's own Turkish file has "icin" here (missing ç); same sentence,
; spelled right.
turkish.SelectDirBrowseLabel=İlerlemek için Sonraki üzerine tıklayın. Farklı bir klasör seçmek için Göz at üzerine tıklayın.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\build\windows\MediaGrab\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
; NOTE: pythonw.exe = no console window; run.py opens the browser itself and,
; if MediaGrab is already running, only opens the browser again.
Name: "{autoprograms}\MediaGrab"; Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\app\run.py"""; WorkingDir: "{app}\app"
Name: "{autodesktop}\MediaGrab"; Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\app\run.py"""; WorkingDir: "{app}\app"; Tasks: desktopicon

[Run]
Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\app\run.py"""; WorkingDir: "{app}\app"; Description: "{cm:LaunchProgram,MediaGrab}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; NOTE: files created after install aren't in Inno's uninstall log - an
; in-app yt-dlp update rewrites site-packages, Python writes __pycache__.
; Only the program folders are swept; user data is never touched here.
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\ffmpeg"
Type: filesandordirs; Name: "{app}\app\mediagrab"
