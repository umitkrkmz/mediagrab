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
; NOTE: no "folder already exists, install anyway?" question - in this layout
; the folder only ever holds MediaGrab's own program files (user data lives in
; %LOCALAPPDATA%\MediaGrab and the downloads folder), and the question makes
; people fear their videos are about to be overwritten.
DirExistsWarning=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
SetupIconFile=mediagrab.ico
ShowLanguageDialog=auto
Compression=lzma2/ultra64
SolidCompression=yes
OutputDir=..\dist
OutputBaseFilename=MediaGrabSetup-{#AppVersion}
UninstallDisplayName=MediaGrab
UninstallDisplayIcon={app}\mediagrab.ico
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
; NOTE: MediaGrab.exe = the embedded pythonw.exe (no console window) under
; MediaGrab's own name and icon, so Task Manager says "MediaGrab", not
; "Python" (packaging/exe_branding.py). run.py opens the browser itself and,
; if MediaGrab is already running, only opens the browser again.
Name: "{autoprograms}\MediaGrab"; Filename: "{app}\python\MediaGrab.exe"; Parameters: """{app}\app\run.py"""; WorkingDir: "{app}\app"; IconFilename: "{app}\mediagrab.ico"
Name: "{autodesktop}\MediaGrab"; Filename: "{app}\python\MediaGrab.exe"; Parameters: """{app}\app\run.py"""; WorkingDir: "{app}\app"; IconFilename: "{app}\mediagrab.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\python\MediaGrab.exe"; Parameters: """{app}\app\run.py"""; WorkingDir: "{app}\app"; Description: "{cm:LaunchProgram,MediaGrab}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; NOTE: files created after install aren't in Inno's uninstall log - an
; in-app yt-dlp update rewrites site-packages, Python writes __pycache__.
; Only the program folders are swept; user data is never touched here.
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\ffmpeg"
Type: filesandordirs; Name: "{app}\app\mediagrab"

[CustomMessages]
english.DownloadDirCaption=Download folder
english.DownloadDirDescription=Where should downloaded videos and music be saved?
english.DownloadDirSubCaption=MediaGrab saves everything you download in this folder. You can change it later in Settings.
english.DownloadDirInsideApp=Please choose a folder outside MediaGrab's own program folder - an update or uninstall could delete files inside it.
turkish.DownloadDirCaption=İndirme klasörü
turkish.DownloadDirDescription=İndirilen videolar ve müzikler nereye kaydedilsin?
turkish.DownloadDirSubCaption=MediaGrab indirdiğiniz her şeyi bu klasöre kaydeder. Daha sonra Ayarlar'dan değiştirebilirsiniz.
turkish.DownloadDirInsideApp=Lütfen MediaGrab'ın kendi program klasörünün dışında bir klasör seçin; güncelleme ya da kaldırma sırasında oradaki dosyalar silinebilir.
english.DownloadDirPrevious=The folder from your previous MediaGrab installation is filled in below.
english.DownloadDirFromPrevious=from your previous installation
turkish.DownloadDirPrevious=Aşağıda önceki MediaGrab kurulumunuzda kullandığınız klasör seçili.
turkish.DownloadDirFromPrevious=önceki kurulumunuzdan
english.DownloadDirDefault=Default: %1
turkish.DownloadDirDefault=Varsayılan: %1
english.MediaGrabRunning=MediaGrab is running. It will be closed to continue; downloads in progress will stop.
turkish.MediaGrabRunning=MediaGrab çalışıyor. Devam etmek için kapatılacak; süren indirmeler durur.
english.MediaGrabStillRunning=MediaGrab could not be closed. Quit it from its icon in the notification area (next to the clock), then try again.
turkish.MediaGrabStillRunning=MediaGrab kapatılamadı. Saatin yanındaki simgesinden kapatıp yeniden deneyin.

[Code]
#include "settings_json.iss"

#include "close_mediagrab.iss"

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if not CloseMediaGrab(WizardSilent) then
    Result := CustomMessage('MediaGrabStillRunning');
end;

function InitializeUninstall(): Boolean;
begin
  Result := CloseMediaGrab(UninstallSilent);
end;

var
  DownloadDirPage: TInputDirWizardPage;
  // NOTE: set when MediaGrab was uninstalled with its data kept and is now
  // installed again - the page then starts from that folder, not the default.
  PreviousDownloadDir: String;

// NOTE: Windows' own "Downloads" location (people move it to other drives),
// read from the per-user Shell Folders key; ~\Downloads if it isn't there.
function UserDownloadsFolder(): String;
begin
  if not RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders',
    '{374DE290-123F-4565-9164-39C4925E467B}', Result) then
    Result := ExpandConstant('{%USERPROFILE}') + '\Downloads';
end;

// NOTE: an update keeps whatever folder is already in use - the page is
// for a first install only (PrevAppDir is empty then).
function IsFirstInstall(): Boolean;
begin
  Result := WizardForm.PrevAppDir = '';
end;

procedure InitializeWizard;
var
  SubCaption, DefaultDir: String;
begin
  DefaultDir := AddBackslash(UserDownloadsFolder()) + 'MediaGrab';
  PreviousDownloadDir := ReadDownloadDirSetting(ExpandConstant('{localappdata}\MediaGrab\settings.json'));
  // NOTE: the old folder is pre-filled (someone just clicking Next keeps
  // finding their videos), with the default spelled out next to it so going
  // back to it is a matter of typing what's on screen.
  if CompareText(RemoveBackslash(PreviousDownloadDir), DefaultDir) = 0 then
    PreviousDownloadDir := '';
  SubCaption := CustomMessage('DownloadDirSubCaption');
  if PreviousDownloadDir <> '' then
    SubCaption := SubCaption + #13#10#13#10 + CustomMessage('DownloadDirPrevious')
      + #13#10 + FmtMessage(CustomMessage('DownloadDirDefault'), [DefaultDir]);
  DownloadDirPage := CreateInputDirPage(wpSelectDir,
    CustomMessage('DownloadDirCaption'), CustomMessage('DownloadDirDescription'),
    SubCaption, False, 'MediaGrab');
  DownloadDirPage.Add('');
  if PreviousDownloadDir <> '' then
    DownloadDirPage.Values[0] := PreviousDownloadDir
  else
    DownloadDirPage.Values[0] := DefaultDir;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := (PageID = DownloadDirPage.ID) and not IsFirstInstall();
end;

// NOTE: the same rule the app enforces (app.py _check_download_dir): never
// inside MediaGrab's own program folder.
function NextButtonClick(CurPageID: Integer): Boolean;
var
  AppDir, Chosen: String;
begin
  Result := True;
  if CurPageID = DownloadDirPage.ID then
  begin
    AppDir := Lowercase(AddBackslash(WizardDirValue));
    Chosen := Lowercase(AddBackslash(DownloadDirPage.Values[0]));
    if Pos(AppDir, Chosen) = 1 then
    begin
      MsgBox(CustomMessage('DownloadDirInsideApp'), mbError, MB_OK);
      Result := False;
    end;
  end;
end;

// NOTE: the "Ready to install" summary - Inno's own lines plus the downloads
// folder chosen on our page (first install only, like the page itself).
function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,
  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
var
  Caption: String;
begin
  Result := MemoDirInfo + NewLine + NewLine;
  if IsFirstInstall() then
  begin
    Caption := CustomMessage('DownloadDirCaption');
    if (PreviousDownloadDir <> '') and (CompareText(RemoveBackslash(PreviousDownloadDir), RemoveBackslash(DownloadDirPage.Values[0])) = 0) then
      Caption := Caption + ' (' + CustomMessage('DownloadDirFromPrevious') + ')';
    Result := Result + Caption + ':' + NewLine + Space + DownloadDirPage.Values[0] + NewLine + NewLine;
  end;
  if MemoTasksInfo <> '' then
    Result := Result + MemoTasksInfo + NewLine + NewLine;
end;

// NOTE: handed to the app rather than written into settings.json from here:
// MediaGrab reads this file on its first start, checks the folder with its
// own rules and deletes the file (app.py _apply_installer_download_dir).
// What the page showed is what counts - it started from the existing setting,
// if there was one.
procedure CurStepChanged(CurStep: TSetupStep);
var
  Lines: TArrayOfString;
  DataDir: String;
begin
  if (CurStep = ssPostInstall) and IsFirstInstall() then
  begin
    DataDir := ExpandConstant('{localappdata}\MediaGrab');
    ForceDirectories(DataDir);
    SetArrayLength(Lines, 1);
    Lines[0] := DownloadDirPage.Values[0];
    SaveStringsToUTF8File(DataDir + '\install-download-dir.txt', Lines, False);
  end;
end;
