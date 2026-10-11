; Inno Setup script for the self-contained Windows build (v2.4.0 work).
;
;   python packaging/build_windows.py
;   ISCC /DAppVersion=2.4.0 packaging/mediagrab.iss      -> dist\MediaGrabSetup-2.4.0.exe
;
; NOTE: per-user install (PrivilegesRequired=lowest): no UAC prompt, and the
; embedded Python stays writable so Settings -> "update yt-dlp" keeps working
; - under Program Files it would need admin rights for every pip install.
; {autopf} resolves to %LOCALAPPDATA%\Programs for a per-user install.
;
; Two kinds of install, picked on the first page (an update keeps the kind):
;   normal  - the embedded Python + MediaGrab + ffmpeg, run on this computer;
;   Docker  - MediaGrab's image in Docker Desktop (docker_mode.iss,
;             docker_wizard.iss); none of the Python/ffmpeg files are copied.

#ifndef AppVersion
  #error Pass the version: ISCC /DAppVersion=x.y.z packaging/mediagrab.iss
#endif
; NOTE: the Docker install uses the image of exactly this release, so this
; installer always installs the same thing and "installed X -> this Y" means
; something. Dev builds pass an existing tag: /DDockerImageTag=2.3.1
#ifndef DockerImageTag
  #define DockerImageTag AppVersion
#endif
#define DockerImage "ghcr.io/umitkrkmz/mediagrab:" + DockerImageTag
; NOTE: the size of the normal install's files, written by build_windows.py.
; They're installed with a Check (not for Docker), and Inno leaves such files
; out of the "at least ... MB of free disk space" it shows - it said 4.3 MB.
#define PayloadSizeFile AddBackslash(SourcePath) + "..\build\windows\payload-bytes.txt"
#if !FileExists(PayloadSizeFile)
  #error Run packaging/build_windows.py first (no build\windows\payload-bytes.txt)
#endif
#define PayloadHandle FileOpen(PayloadSizeFile)
#define PayloadBytes Trim(FileRead(PayloadHandle))
#expr FileClose(PayloadHandle)

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
ExtraDiskSpaceRequired={#PayloadBytes}
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
Source: "..\build\windows\MediaGrab\*"; Excludes: "mediagrab.ico"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion; Check: not IsDockerMode
Source: "mediagrab.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; NOTE: MediaGrab.exe = the embedded pythonw.exe (no console window) under
; MediaGrab's own name and icon, so Task Manager says "MediaGrab", not
; "Python" (packaging/exe_branding.py). run.py opens the browser itself and,
; if MediaGrab is already running, only opens the browser again.
Name: "{autoprograms}\MediaGrab"; Filename: "{app}\python\MediaGrab.exe"; Parameters: """{app}\app\run.py"""; WorkingDir: "{app}\app"; IconFilename: "{app}\mediagrab.ico"; Check: not IsDockerMode
Name: "{autodesktop}\MediaGrab"; Filename: "{app}\python\MediaGrab.exe"; Parameters: """{app}\app\run.py"""; WorkingDir: "{app}\app"; IconFilename: "{app}\mediagrab.ico"; Tasks: desktopicon; Check: not IsDockerMode

[INI]
; NOTE: a Docker install has nothing to start on this computer - its
; shortcuts are links to the container's page.
Filename: "{autoprograms}\MediaGrab.url"; Section: "InternetShortcut"; Key: "URL"; String: "http://localhost:8420"; Check: IsDockerMode
Filename: "{autoprograms}\MediaGrab.url"; Section: "InternetShortcut"; Key: "IconFile"; String: "{app}\mediagrab.ico"; Check: IsDockerMode
Filename: "{autoprograms}\MediaGrab.url"; Section: "InternetShortcut"; Key: "IconIndex"; String: "0"; Check: IsDockerMode
Filename: "{autodesktop}\MediaGrab.url"; Section: "InternetShortcut"; Key: "URL"; String: "http://localhost:8420"; Tasks: desktopicon; Check: IsDockerMode
Filename: "{autodesktop}\MediaGrab.url"; Section: "InternetShortcut"; Key: "IconFile"; String: "{app}\mediagrab.ico"; Tasks: desktopicon; Check: IsDockerMode
Filename: "{autodesktop}\MediaGrab.url"; Section: "InternetShortcut"; Key: "IconIndex"; String: "0"; Tasks: desktopicon; Check: IsDockerMode

[Run]
Filename: "{app}\python\MediaGrab.exe"; Parameters: """{app}\app\run.py"""; WorkingDir: "{app}\app"; Description: "{cm:LaunchProgram,MediaGrab}"; Flags: nowait postinstall skipifsilent; Check: not IsDockerMode
; NOTE: not "Launch MediaGrab" - nothing is started on this computer; the
; container is already running and this only opens its page.
Filename: "http://localhost:8420"; Description: "{cm:DockerOpenInBrowser}"; Flags: shellexec nowait postinstall skipifsilent; Check: IsDockerMode

[UninstallDelete]
; NOTE: files created after install aren't in Inno's uninstall log - an
; in-app yt-dlp update rewrites site-packages, Python writes __pycache__.
; Only the program folders are swept; user data is never touched here.
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\ffmpeg"
Type: filesandordirs; Name: "{app}\app\mediagrab"
Type: files; Name: "{app}\docker-folder.txt"
Type: files; Name: "{autoprograms}\MediaGrab.url"
Type: files; Name: "{autodesktop}\MediaGrab.url"
; NOTE: an empty app\ (and the install folder) was left behind in the dev12
; test; "dirifempty" can't delete anything that's still in them.
Type: dirifempty; Name: "{app}\app"
Type: dirifempty; Name: "{app}"

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
english.UninstallOptionsCaption=Uninstall MediaGrab
english.UninstallOptionsIntro=MediaGrab is being removed. What should happen to your settings and the videos you downloaded?
english.UninstallKeepData=Remove only MediaGrab - keep settings and videos (recommended)
english.UninstallRemoveData=Also delete MediaGrab's settings (channels, cookies, statistics)
english.UninstallDeleteVideos=Also delete the videos I downloaded (%1 files, %2)
english.UninstallNoVideos=No downloaded videos found to delete
english.UninstallContinue=Continue
english.UninstallConfirmVideos=%1 files (%2) will be permanently deleted from:%n%3%n%nThis can't be undone. Are you sure?
turkish.UninstallOptionsCaption=MediaGrab'ı kaldır
turkish.UninstallOptionsIntro=MediaGrab kaldırılıyor. Ayarlarınız ve indirdiğiniz videolar ne olsun?
turkish.UninstallKeepData=Yalnızca MediaGrab'ı kaldır; ayarlar ve videolar kalsın (önerilen)
turkish.UninstallRemoveData=MediaGrab'ın ayarlarını da sil (kanallar, çerezler, istatistikler)
turkish.UninstallDeleteVideos=İndirdiğim videoları da sil (%1 dosya, %2)
turkish.UninstallNoVideos=Silinecek indirilmiş video bulunamadı
turkish.UninstallContinue=Devam
turkish.UninstallConfirmVideos=%1 dosya (%2) kalıcı olarak silinecek:%n%3%n%nBu geri alınamaz. Emin misiniz?
english.ModeCaption=Installation type
english.ModeDescription=How should MediaGrab be installed?
english.ModeSubCaption=If you're not sure, choose the first one.
english.ModeNormal=Normal installation (recommended) - MediaGrab runs right on this computer; nothing else is needed.
english.ModeDocker=Install with Docker (advanced) - MediaGrab runs as a container in Docker Desktop.
turkish.ModeCaption=Kurulum türü
turkish.ModeDescription=MediaGrab nasıl kurulsun?
turkish.ModeSubCaption=Emin değilseniz ilkini seçin.
turkish.ModeNormal=Normal kurulum (önerilen) - MediaGrab doğrudan bu bilgisayarda çalışır; başka bir şey gerekmez.
turkish.ModeDocker=Docker ile kurulum (ileri düzey) - MediaGrab, Docker Desktop'ta bir konteyner olarak çalışır.
english.DockerCaption=Docker
english.DockerDescription=Checking Docker Desktop and any MediaGrab already installed in it
english.DockerStatus_missing=Docker was not found. Install Docker Desktop first, then click "Check again".
english.DockerStatus_no_compose=Docker was found, but it doesn't support "docker compose" - update Docker Desktop.
english.DockerStatus_not_running=Docker was found but isn't running - open Docker Desktop, then click "Check again".
english.DockerStatus_ready=Docker was found and is running.
english.DockerExisting=MediaGrab is already installed in Docker on this computer:%n%1%nVersion: %2 (%3)%n%nNext updates it to version %4. Your data and password are kept.
english.DockerNew=No MediaGrab was found in Docker; it will be installed new.
english.DockerUnknownVersion=unknown
english.DockerStateRunning=running
english.DockerStateStopped=stopped
english.DockerStateNone=no container
english.DockerRecheck=Check again
english.DockerDownload=Download Docker Desktop
english.DockerNotReady=Docker isn't ready yet. Open Docker Desktop, wait until it says it's running, then click "Check again".
english.DockerDirCaption=Docker folder
english.DockerDirDescription=Where should docker-compose.yml and MediaGrab's data go?
english.DockerDirSubCaption=Your downloaded videos are kept inside this folder too (data\indirilenler).
english.DockerDirBad=This folder can't be used (the root of a drive, or a Windows or program folder). Please choose another one.
english.DockerPasswordCaption=Password
english.DockerPasswordDescription=The password for signing in to MediaGrab in Docker
english.DockerPasswordSubCaption=In Docker, MediaGrab always asks for a password. At least 8 characters; you can change it later in Settings.
english.DockerPassword=Password:
english.DockerPasswordAgain=Password (again):
english.DockerPasswordShort=The password must be at least 8 characters.
english.DockerPasswordMismatch=The two passwords are not the same.
english.DockerMemoMode=Installation type:
english.DockerMemoDocker=Docker
english.DockerMemoFolder=Docker folder:
english.DockerMemoAction=What happens:
english.DockerMemoNew=New installation (%1)
english.DockerMemoUpdate=Update: %1 -> %2
english.DockerInstallingCaption=Installing with Docker
english.DockerInstallingDescription=MediaGrab's Docker image is being downloaded and started. The first time this can take a few minutes.
english.DockerStepFolders=Preparing folders...
english.DockerStepCompose=Writing docker-compose.yml...
english.DockerStepPull=Downloading the Docker image...
english.DockerStepStart=Starting MediaGrab...
english.DockerStepWait=Waiting for MediaGrab to open...
english.DockerErrComposeUpdate=docker-compose.yml couldn't be written, or has no MediaGrab in it:%n%1
english.DockerErrStart=Docker couldn't start MediaGrab:%n%1%n%nFor details, run "docker compose logs" in this folder:%n%2
english.DockerErrNoAnswer=MediaGrab started but didn't answer within 60 seconds. For details, run "docker compose logs" in this folder:%n%1
english.UninstallOptionsIntroDocker=MediaGrab has been removed from Docker (its container is deleted). Its data is still in %1 - what should happen to your settings and the videos you downloaded?
english.DockerExistingData=This folder already holds data from an earlier MediaGrab (data\settings.json). If a password was set there, that one stays in use - the password below is only used when there isn't one yet.
english.MigrateCaption=Your earlier MediaGrab
english.MigrateDescription=An earlier MediaGrab installation was found on this computer
english.MigrateSubCaption=%1%n%nThe new MediaGrab can take your settings, channel list, cookies and statistics from it. Your videos stay where they are for now: once MediaGrab is open, it offers to move them into the new downloads folder (History and Settings say so). The earlier installation isn't deleted. If it's open (a black console window), close it first.
english.MigrateCheck=Bring over my settings, channels, cookies and statistics (recommended)
english.MigrateMemo=Brought over from the earlier installation:
english.DockerOpenInBrowser=Open MediaGrab in the browser
english.DockerUninstallDownFailed=MediaGrab couldn't be stopped in Docker (Docker Desktop may be closed). You can delete the container in Docker Desktop.
turkish.DockerCaption=Docker
turkish.DockerDescription=Docker Desktop ve içinde kurulu bir MediaGrab olup olmadığı denetleniyor
turkish.DockerStatus_missing=Docker bulunamadı. Önce Docker Desktop'ı kurun, sonra "Yeniden denetle"ye basın.
turkish.DockerStatus_no_compose=Docker bulundu ama "docker compose" desteklenmiyor - Docker Desktop'ı güncelleyin.
turkish.DockerStatus_not_running=Docker bulundu ama çalışmıyor - Docker Desktop'ı açın, sonra "Yeniden denetle"ye basın.
turkish.DockerStatus_ready=Docker bulundu ve çalışıyor.
turkish.DockerExisting=Bu bilgisayarda Docker'da kurulu bir MediaGrab var:%n%1%nSürüm: %2 (%3)%n%nSonraki ile %4 sürümüne güncellenecek. Verileriniz ve parolanız korunur.
turkish.DockerNew=Docker'da kurulu bir MediaGrab bulunamadı; yeni kurulum yapılacak.
turkish.DockerUnknownVersion=bilinmiyor
turkish.DockerStateRunning=çalışıyor
turkish.DockerStateStopped=durmuş
turkish.DockerStateNone=konteyner yok
turkish.DockerRecheck=Yeniden denetle
turkish.DockerDownload=Docker Desktop'ı indir
turkish.DockerNotReady=Docker henüz hazır değil. Docker Desktop'ı açın, çalıştığını gösterene kadar bekleyin, sonra "Yeniden denetle"ye basın.
turkish.DockerDirCaption=Docker klasörü
turkish.DockerDirDescription=docker-compose.yml ve MediaGrab'ın verileri nereye yazılsın?
turkish.DockerDirSubCaption=İndirdiğiniz videolar da bu klasörün içinde (data\indirilenler) durur.
turkish.DockerDirBad=Bu klasör kullanılamaz (bir sürücünün kökü ya da Windows veya program klasörü). Lütfen başka bir klasör seçin.
turkish.DockerPasswordCaption=Parola
turkish.DockerPasswordDescription=Docker'daki MediaGrab'a girişte kullanılacak parola
turkish.DockerPasswordSubCaption=Docker'da MediaGrab her zaman parola sorar. En az 8 karakter; daha sonra Ayarlar'dan değiştirebilirsiniz.
turkish.DockerPassword=Parola:
turkish.DockerPasswordAgain=Parola (tekrar):
turkish.DockerPasswordShort=Parola en az 8 karakter olmalı.
turkish.DockerPasswordMismatch=İki parola aynı değil.
turkish.DockerMemoMode=Kurulum türü:
turkish.DockerMemoDocker=Docker
turkish.DockerMemoFolder=Docker klasörü:
turkish.DockerMemoAction=Yapılacak işlem:
turkish.DockerMemoNew=Yeni kurulum (%1)
turkish.DockerMemoUpdate=Güncelleme: %1 -> %2
turkish.DockerInstallingCaption=Docker ile kuruluyor
turkish.DockerInstallingDescription=MediaGrab'ın Docker imajı indiriliyor ve başlatılıyor. İlk seferde birkaç dakika sürebilir.
turkish.DockerStepFolders=Klasörler hazırlanıyor...
turkish.DockerStepCompose=docker-compose.yml yazılıyor...
turkish.DockerStepPull=Docker imajı indiriliyor...
turkish.DockerStepStart=MediaGrab başlatılıyor...
turkish.DockerStepWait=MediaGrab'ın açılması bekleniyor...
turkish.DockerErrComposeUpdate=docker-compose.yml yazılamadı ya da içinde MediaGrab yok:%n%1
turkish.DockerErrStart=Docker MediaGrab'ı başlatamadı:%n%1%n%nAyrıntı için bu klasörde "docker compose logs" çalıştırın:%n%2
turkish.DockerErrNoAnswer=MediaGrab başladı ama 60 saniye içinde cevap vermedi. Ayrıntı için bu klasörde "docker compose logs" çalıştırın:%n%1
turkish.UninstallOptionsIntroDocker=MediaGrab Docker'dan kaldırıldı (konteyneri silindi). Verileri %1 klasöründe duruyor; ayarlarınız ve indirdiğiniz videolar ne olsun?
turkish.DockerExistingData=Bu klasörde önceki bir MediaGrab'ın verisi var (data\settings.json). Orada bir parola belirlenmişse o geçerli kalır; aşağıdaki parola yalnızca henüz parola yoksa kullanılır.
turkish.MigrateCaption=Önceki MediaGrab
turkish.MigrateDescription=Bu bilgisayarda eski bir MediaGrab kurulumu bulundu
turkish.MigrateSubCaption=%1%n%nYeni MediaGrab ayarlarınızı, kanal listenizi, çerezlerinizi ve istatistiklerinizi buradan alabilir. Videolarınız şimdilik yerinde kalır: MediaGrab açılınca onları yeni indirme klasörüne taşımayı teklif eder (Geçmiş ve Ayarlar'da yazar). Eski kurulum silinmez. Açıksa (siyah konsol penceresi) önce kapatın.
turkish.MigrateCheck=Ayarlarımı, kanallarımı, çerezlerimi ve istatistiklerimi aktar (önerilen)
turkish.MigrateMemo=Önceki kurulumdan aktarılacak:
turkish.DockerOpenInBrowser=MediaGrab'ı tarayıcıda aç
turkish.DockerUninstallDownFailed=Docker'daki MediaGrab durdurulamadı (Docker Desktop kapalı olabilir). Konteyneri Docker Desktop'tan silebilirsiniz.

[Code]
#include "settings_json.iss"

#include "close_mediagrab.iss"

#include "uninstall_options.iss"

#include "docker_mode.iss"

#include "docker_wizard.iss"

var
  DownloadDirPage: TInputDirWizardPage;
  // NOTE: set when MediaGrab was uninstalled with its data kept and is now
  // installed again - the page then starts from that folder, not the default.
  PreviousDownloadDir: String;
  ModePage: TInputOptionWizardPage;
  DockerPage: TWizardPage;
  DockerStatusText: TNewStaticText;
  DockerDownloadButton: TNewButton;
  DockerIsReady: Boolean;
  DockerDirPage: TInputDirWizardPage;
  DockerPasswordPage: TInputQueryWizardPage;
  // NOTE: a pre-v2.4.0 (Tk installer) MediaGrab found on this computer.
  OldInstallFolder: String;
  // NOTE: its videos are NOT taken over as the downloads folder (user's
  // choice, dev18 test): they live inside the old install's own folder, and
  // whoever deletes that folder later would lose them. The app offers
  // "Move here" for them instead (app.py _apply_installer_migration).
  MigratePage: TInputOptionWizardPage;

// NOTE: also a Check: for [Files]/[Icons]/[INI]/[Run] - evaluated when
// installing, after the wizard.
function IsDockerMode(): Boolean;
begin
  Result := (ModePage <> nil) and (ModePage.SelectedValueIndex = 1);
end;

// NOTE: an update keeps whatever kind and folders are already in use - the
// first-install pages are for a first install only (PrevAppDir is empty then).
function IsFirstInstall(): Boolean;
begin
  Result := WizardForm.PrevAppDir = '';
end;

function DefaultDockerFolder(): String;
begin
  Result := ExpandConstant('{sd}\MediaGrab');
end;

function Migrating(): Boolean;
begin
  Result := (OldInstallFolder <> '') and not IsDockerMode() and IsFirstInstall() and MigratePage.Values[0];
end;

function DockerFolder(): String;
begin
  if ExistingDockerFolder <> '' then
    Result := ExistingDockerFolder
  else
    Result := DockerDirPage.Values[0];
end;

// NOTE: Windows' own "Downloads" location (people move it to other drives),
// read from the per-user Shell Folders key; ~\Downloads if it isn't there.
function UserDownloadsFolder(): String;
begin
  if not RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders',
    '{374DE290-123F-4565-9164-39C4925E467B}', Result) then
    Result := ExpandConstant('{%USERPROFILE}') + '\Downloads';
end;

procedure RefreshDockerPage();
var
  Status, Text, Version, State: String;
begin
  WizardForm.NextButton.Enabled := False;
  Status := DockerStatus();
  DockerIsReady := Status = 'ready';
  Text := CustomMessage('DockerStatus_' + Status);
  if DockerIsReady then
  begin
    DetectExistingDocker(DockerContainer, DefaultDockerFolder(), GetPreviousData('DockerFolder', ''));
    if ExistingDockerFolder <> '' then
    begin
      Version := ExistingDockerVersion;
      if Version = '' then
        Version := CustomMessage('DockerUnknownVersion');
      if ExistingDockerState = 'running' then
        State := CustomMessage('DockerStateRunning')
      else if ExistingDockerState = '' then
        State := CustomMessage('DockerStateNone')
      else
        State := CustomMessage('DockerStateStopped');
      Text := Text + #13#10#13#10 + FmtMessage(CustomMessage('DockerExisting'), [ExistingDockerFolder, Version, State, '{#AppVersion}']);
    end
    else
      Text := Text + #13#10#13#10 + CustomMessage('DockerNew');
  end;
  DockerStatusText.Caption := Text;
  DockerDownloadButton.Visible := (Status = 'missing') or (Status = 'no_compose');
  WizardForm.NextButton.Enabled := True;
end;

procedure DockerRecheckClick(Sender: TObject);
begin
  RefreshDockerPage();
end;

procedure DockerDownloadClick(Sender: TObject);
var
  ErrorCode: Integer;
begin
  ShellExecAsOriginalUser('open', 'https://www.docker.com/products/docker-desktop/', '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
end;

procedure InitializeWizard;
var
  SubCaption, DefaultDir: String;
  RecheckButton: TNewButton;
begin
  // --- installation type -------------------------------------------------
  ModePage := CreateInputOptionPage(wpWelcome, CustomMessage('ModeCaption'), CustomMessage('ModeDescription'),
    CustomMessage('ModeSubCaption'), True, False);
  ModePage.Add(CustomMessage('ModeNormal'));
  ModePage.Add(CustomMessage('ModeDocker'));
  if GetPreviousData('InstallMode', 'normal') = 'docker' then
    ModePage.SelectedValueIndex := 1
  else
    ModePage.SelectedValueIndex := 0;

  // --- Docker: status + existing install -----------------------------------
  DockerPage := CreateCustomPage(ModePage.ID, CustomMessage('DockerCaption'), CustomMessage('DockerDescription'));
  DockerStatusText := TNewStaticText.Create(DockerPage);
  DockerStatusText.Parent := DockerPage.Surface;
  DockerStatusText.Left := 0;
  DockerStatusText.Top := 0;
  DockerStatusText.Width := DockerPage.SurfaceWidth;
  DockerStatusText.AutoSize := False;
  DockerStatusText.Height := ScaleY(150);
  DockerStatusText.WordWrap := True;
  RecheckButton := TNewButton.Create(DockerPage);
  RecheckButton.Parent := DockerPage.Surface;
  RecheckButton.Top := ScaleY(160);
  RecheckButton.Width := ScaleX(130);
  RecheckButton.Height := ScaleY(25);
  RecheckButton.Caption := CustomMessage('DockerRecheck');
  RecheckButton.OnClick := @DockerRecheckClick;
  DockerDownloadButton := TNewButton.Create(DockerPage);
  DockerDownloadButton.Parent := DockerPage.Surface;
  DockerDownloadButton.Top := ScaleY(160);
  DockerDownloadButton.Left := RecheckButton.Width + ScaleX(8);
  DockerDownloadButton.Width := ScaleX(170);
  DockerDownloadButton.Height := ScaleY(25);
  DockerDownloadButton.Caption := CustomMessage('DockerDownload');
  DockerDownloadButton.OnClick := @DockerDownloadClick;
  DockerDownloadButton.Visible := False;

  // --- Docker: folder + password (new installs only) -----------------------
  DockerDirPage := CreateInputDirPage(DockerPage.ID, CustomMessage('DockerDirCaption'), CustomMessage('DockerDirDescription'),
    CustomMessage('DockerDirSubCaption'), False, 'MediaGrab');
  DockerDirPage.Add('');
  DockerDirPage.Values[0] := GetPreviousData('DockerFolder', DefaultDockerFolder());
  DockerPasswordPage := CreateInputQueryPage(DockerDirPage.ID, CustomMessage('DockerPasswordCaption'),
    CustomMessage('DockerPasswordDescription'), CustomMessage('DockerPasswordSubCaption'));
  DockerPasswordPage.Add(CustomMessage('DockerPassword'), True);
  DockerPasswordPage.Add(CustomMessage('DockerPasswordAgain'), True);

  // --- normal: an earlier (Tk installer) MediaGrab --------------------------
  OldInstallFolder := FindOldInstall(ExpandConstant('{localappdata}\MediaGrab\installer.json'));
  MigratePage := CreateInputOptionPage(DockerPasswordPage.ID, CustomMessage('MigrateCaption'),
    CustomMessage('MigrateDescription'), FmtMessage(CustomMessage('MigrateSubCaption'), [OldInstallFolder]), False, False);
  MigratePage.Add(CustomMessage('MigrateCheck'));
  MigratePage.Values[0] := True;

  // --- normal: downloads folder (first install only) -----------------------
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
  Result := False;
  if PageID = ModePage.ID then
    Result := not IsFirstInstall()
  else if PageID = DockerPage.ID then
    Result := not IsDockerMode()
  else if (PageID = DockerDirPage.ID) or (PageID = DockerPasswordPage.ID) then
    Result := not IsDockerMode() or (ExistingDockerFolder <> '')
  else if PageID = MigratePage.ID then
    Result := IsDockerMode() or not IsFirstInstall() or (OldInstallFolder = '')
  else if PageID = wpSelectDir then
    // NOTE: a Docker install keeps only its uninstaller and icon in {app};
    // the folder that matters is the Docker folder, asked for separately.
    Result := IsDockerMode()
  else if PageID = DownloadDirPage.ID then
    Result := IsDockerMode() or not IsFirstInstall();
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = DockerPage.ID then
    RefreshDockerPage();
end;

function IsUnusableDockerFolder(const Folder: String): Boolean;
var
  Key: String;
begin
  Key := Lowercase(AddBackslash(Folder));
  Result := (Length(RemoveBackslash(Folder)) <= 3)
    or (Pos(Lowercase(AddBackslash(ExpandConstant('{win}'))), Key) = 1)
    or (Pos(Lowercase(AddBackslash(ExpandConstant('{commonpf}'))), Key) = 1)
    or (Pos(Lowercase(AddBackslash(ExpandConstant('{commonpf32}'))), Key) = 1);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  AppDir, Chosen, Error: String;
begin
  Result := True;
  if CurPageID = DownloadDirPage.ID then
  begin
    // NOTE: the same rule the app enforces (app.py _check_download_dir):
    // never inside MediaGrab's own program folder.
    AppDir := Lowercase(AddBackslash(WizardDirValue));
    Chosen := Lowercase(AddBackslash(DownloadDirPage.Values[0]));
    if Pos(AppDir, Chosen) = 1 then
    begin
      MsgBox(CustomMessage('DownloadDirInsideApp'), mbError, MB_OK);
      Result := False;
    end;
  end
  else if CurPageID = DockerPage.ID then
  begin
    if not DockerIsReady then
    begin
      MsgBox(CustomMessage('DockerNotReady'), mbInformation, MB_OK);
      Result := False;
    end;
  end
  else if CurPageID = DockerDirPage.ID then
  begin
    if IsUnusableDockerFolder(DockerDirPage.Values[0]) then
    begin
      MsgBox(CustomMessage('DockerDirBad'), mbError, MB_OK);
      Result := False;
    end;
  end
  else if CurPageID = DockerPasswordPage.ID then
  begin
    // NOTE: an earlier MediaGrab's settings.json in the chosen folder keeps
    // ITS password - the app only takes MEDIAGRAB_INITIAL_PASSWORD when
    // none is set yet. Said once here rather than leaving a new password
    // silently ignored (found trying a reinstall into the same folder).
    if FileExists(AddBackslash(DockerDirPage.Values[0]) + 'data\settings.json') then
      MsgBox(CustomMessage('DockerExistingData'), mbInformation, MB_OK);
    if Length(DockerPasswordPage.Values[0]) < 8 then
    begin
      MsgBox(CustomMessage('DockerPasswordShort'), mbError, MB_OK);
      Result := False;
    end
    else if DockerPasswordPage.Values[0] <> DockerPasswordPage.Values[1] then
    begin
      MsgBox(CustomMessage('DockerPasswordMismatch'), mbError, MB_OK);
      Result := False;
    end;
  end
  else if (CurPageID = wpReady) and IsDockerMode() then
  begin
    // NOTE: the Docker work happens here, on "Install", so a failure keeps
    // the wizard open with the message instead of a half-finished install.
    // A MediaGrab running on this computer would hold port 8420.
    if not CloseMediaGrab(False) then
    begin
      Result := False;
      Exit;
    end;
    Error := RunDockerInstall(DockerFolder(), '{#DockerImage}', DockerPasswordPage.Values[0], ExistingDockerFolder <> '');
    if Error <> '' then
    begin
      MsgBox(Error, mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if not CloseMediaGrab(WizardSilent) then
    Result := CustomMessage('MediaGrabStillRunning');
end;

// NOTE: the "Ready to install" summary - Inno's own lines plus our pages.
function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,
  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
var
  Caption, Version: String;
begin
  if IsDockerMode() then
  begin
    Result := CustomMessage('DockerMemoMode') + NewLine + Space + CustomMessage('DockerMemoDocker') + NewLine + NewLine
      + CustomMessage('DockerMemoFolder') + NewLine + Space + DockerFolder() + NewLine + NewLine
      + CustomMessage('DockerMemoAction') + NewLine + Space;
    if ExistingDockerFolder <> '' then
    begin
      Version := ExistingDockerVersion;
      if Version = '' then
        Version := CustomMessage('DockerUnknownVersion');
      Result := Result + FmtMessage(CustomMessage('DockerMemoUpdate'), [Version, '{#AppVersion}']);
    end
    else
      Result := Result + FmtMessage(CustomMessage('DockerMemoNew'), ['{#DockerImage}']);
    Result := Result + NewLine + NewLine;
  end
  else
  begin
    Result := MemoDirInfo + NewLine + NewLine;
    if Migrating() then
      Result := Result + CustomMessage('MigrateMemo') + NewLine + Space + OldInstallFolder + NewLine + NewLine;
    if IsFirstInstall() then
    begin
      Caption := CustomMessage('DownloadDirCaption');
      if (PreviousDownloadDir <> '') and (CompareText(RemoveBackslash(PreviousDownloadDir), RemoveBackslash(DownloadDirPage.Values[0])) = 0) then
        Caption := Caption + ' (' + CustomMessage('DownloadDirFromPrevious') + ')';
      Result := Result + Caption + ':' + NewLine + Space + DownloadDirPage.Values[0] + NewLine + NewLine;
    end;
  end;
  if MemoTasksInfo <> '' then
    Result := Result + MemoTasksInfo + NewLine + NewLine;
end;

procedure RegisterPreviousData(PreviousDataKey: Integer);
begin
  if IsDockerMode() then
  begin
    SetPreviousData(PreviousDataKey, 'InstallMode', 'docker');
    SetPreviousData(PreviousDataKey, 'DockerFolder', DockerFolder());
  end
  else
    SetPreviousData(PreviousDataKey, 'InstallMode', 'normal');
end;

// NOTE: handed to the app rather than written into settings.json from here:
// MediaGrab reads this file on its first start, checks the folder with its
// own rules and deletes the file (app.py _apply_installer_download_dir).
// What the page showed is what counts - it started from the existing setting,
// if there was one. A Docker install instead records its folder for the
// uninstaller.
procedure CurStepChanged(CurStep: TSetupStep);
var
  Lines: TArrayOfString;
  DataDir: String;
begin
  if CurStep <> ssPostInstall then
    Exit;
  SetArrayLength(Lines, 1);
  if IsDockerMode() then
  begin
    Lines[0] := DockerFolder();
    SaveStringsToUTF8File(ExpandConstant('{app}\docker-folder.txt'), Lines, False);
  end
  else if IsFirstInstall() then
  begin
    DataDir := ExpandConstant('{localappdata}\MediaGrab');
    ForceDirectories(DataDir);
    Lines[0] := DownloadDirPage.Values[0];
    SaveStringsToUTF8File(DataDir + '\install-download-dir.txt', Lines, False);
    // NOTE: the app copies the files itself on its first start
    // (app.py _apply_installer_migration) - never over newer ones.
    if Migrating() then
    begin
      Lines[0] := OldInstallFolder;
      SaveStringsToUTF8File(DataDir + '\install-migrate-from.txt', Lines, False);
    end;
  end;
end;

// --- uninstall ---------------------------------------------------------------

var
  UninstallKindRead: Boolean;
  UninstallDockerFolderValue: String;

// NOTE: '' for a normal install. Read once, at the first step, and kept:
// docker-folder.txt itself is deleted during the uninstall, and a Docker
// uninstall must never fall through to the normal one's clean-up (which
// would delete %LOCALAPPDATA%\MediaGrab - a different install's data).
function UninstallDockerFolder(): String;
var
  Lines: TArrayOfString;
begin
  if not UninstallKindRead then
  begin
    UninstallKindRead := True;
    if LoadStringsFromFile(ExpandConstant('{app}\docker-folder.txt'), Lines) and (GetArrayLength(Lines) > 0) then
      UninstallDockerFolderValue := Trim(Lines[0]);
  end;
  Result := UninstallDockerFolderValue;
end;

function InitializeUninstall(): Boolean;
begin
  UninstallDockerFolder();
  Result := True;
end;

procedure DeleteDockerData(const Folder: String);
var
  Data: String;
begin
  Data := AddBackslash(Folder) + 'data\';
  DeleteFile(Data + 'settings.json');
  DeleteFile(Data + 'channels.json');
  DelTree(Data + 'cookies', True, True, True);
  DelTree(Data + 'stats', True, True, True);
  DelTree(Data + 'pip-packages', True, True, True);
  DeleteFile(AddBackslash(Folder) + 'docker-compose.yml');
  RemoveDir(Data + 'indirilenler');
  RemoveDir(Data);
  RemoveDir(Folder);
end;

// NOTE: usUninstall comes after Inno's own "really uninstall?" question and
// before any file is removed. MediaGrab is closed only here - closing it
// before that question (InitializeUninstall) stopped it even when the user
// then answered "No" (seen in the dev12 test); and having said "Yes", nobody
// needs to be asked a second time. MediaGrab's Python is still there to
// count/delete the videos. A silent uninstall keeps all data.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  PythonExe, AppDir, OutFile, Folder: String;
  Files: Integer;
  Bytes: Int64;
begin
  Folder := UninstallDockerFolder();
  if (CurUninstallStep = usUninstall) and (Folder <> '') then
  begin
    // NOTE: a Docker install: the container goes; the Docker folder (its
    // compose file and data, videos included) stays unless chosen below.
    if not DockerComposeDown(Folder) and not UninstallSilent then
      MsgBox(CustomMessage('DockerUninstallDownFailed'), mbInformation, MB_OK);
    if not UninstallSilent then
    begin
      Files := 0;
      Bytes := 0;
      DownloadsFolder := AddBackslash(Folder) + 'data\indirilenler';
      CountFolder(DownloadsFolder, Files, Bytes);
      DownloadsCount := Files;
      DownloadsMB := (Bytes + 1048575) div 1048576;
      UninstallIntro := FmtMessage(CustomMessage('UninstallOptionsIntroDocker'), [Folder]);
      AskUninstallOptions(True);
      if DeleteDownloads then
        DelTree(DownloadsFolder, True, True, True);
      if DeleteMediaGrabData then
        DeleteDockerData(Folder);
    end;
    Exit;
  end;
  if Folder <> '' then
    Exit;

  PythonExe := ExpandConstant('{app}\python\python.exe');
  AppDir := ExpandConstant('{app}\app');
  OutFile := AddBackslash(GetTempDir()) + 'mediagrab-uninstall.txt';
  if CurUninstallStep = usUninstall then
    if not CloseMediaGrab(True) and not UninstallSilent then
      // NOTE: rare (stuck for 20 s); the files it holds stay behind and
      // Inno lists them - better than a half-asked uninstall.
      MsgBox(CustomMessage('MediaGrabStillRunning'), mbError, MB_OK);
  if (CurUninstallStep = usUninstall) and not UninstallSilent then
  begin
    AskUninstallOptions(ReadDownloadsSummary(PythonExe, AppDir, OutFile));
    if DeleteDownloads then
      RunUninstallHelper(PythonExe, AppDir, 'delete-downloads', OutFile);
    DeleteFile(OutFile);
  end;
  if (CurUninstallStep = usPostUninstall) and DeleteMediaGrabData then
    DelTree(ExpandConstant('{localappdata}\MediaGrab'), True, True, True);
end;
