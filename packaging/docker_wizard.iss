// "Install with Docker" - talking to Docker: is it there, is MediaGrab
// already installed in it (where, which version), and the install itself.
// Included by mediagrab.iss inside [Code], after docker_mode.iss and
// settings_json.iss (JsonStringValue). The read-only detection is also run
// on its own by tests/test_installer_script.py against the real Docker.
//
// Needs the CustomMessages Docker* (mediagrab.iss).

const
  DockerContainer = 'mediagrab';

var
  DockerExe: String;
  // NOTE: filled by DetectExistingDocker - an install found here (by this
  // installer or the old Tk one) is updated in place, never asked for a new
  // folder or password.
  ExistingDockerFolder: String;
  ExistingDockerVersion: String;
  ExistingDockerState: String;
  DockerFirstLine: String;
  DockerLastLine: String;
  DockerProgressPage: TOutputProgressWizardPage;

procedure DockerLog(const S: String; const Error, FirstLine: Boolean);
begin
  if Trim(S) <> '' then
  begin
    if DockerFirstLine = '' then
      DockerFirstLine := Trim(S);
    DockerLastLine := Trim(S);
    // NOTE: docker compose pull/up print one line per layer/step - shown
    // under the progress bar so a long first download doesn't look stuck.
    if DockerProgressPage <> nil then
      DockerProgressPage.SetText(DockerProgressPage.Msg1Label.Caption, DockerLastLine);
  end;
  Log('docker: ' + S);
end;

// Runs docker with Params; True on exit code 0. DockerFirstLine holds the
// first non-empty output line afterwards.
function RunDocker(const Params, WorkingDir: String): Boolean;
var
  ResultCode: Integer;
begin
  DockerFirstLine := '';
  DockerLastLine := '';
  Result := False;
  if DockerExe = '' then
    Exit;
  try
    Result := ExecAndLogOutput(DockerExe, Params, WorkingDir, SW_HIDE, ewWaitUntilTerminated, ResultCode, @DockerLog)
      and (ResultCode = 0);
  except
    Log(GetExceptionMessage);
  end;
end;

function FindDocker(): String;
begin
  Result := FileSearch('docker.exe', GetEnv('PATH'));
  // NOTE: Docker Desktop installed after this Windows session started
  // isn't on this process's PATH yet.
  if (Result = '') and FileExists(ExpandConstant('{commonpf64}\Docker\Docker\resources\bin\docker.exe')) then
    Result := ExpandConstant('{commonpf64}\Docker\Docker\resources\bin\docker.exe');
end;

// 'missing' | 'no_compose' | 'not_running' | 'ready' - cheapest check first;
// Docker Desktop can be installed but not started.
function DockerStatus(): String;
begin
  DockerExe := FindDocker();
  if DockerExe = '' then
    Result := 'missing'
  else if not RunDocker('compose version', '') then
    Result := 'no_compose'
  else if not RunDocker('info --format "{{.ServerVersion}}"', '') then
    Result := 'not_running'
  else
    Result := 'ready';
end;

// NOTE: the version is read from inside the image, so it works for images
// built before they carried any version label (the 2.3.x ones).
function MediaGrabVersionIn(const Container, Image: String; Running: Boolean): String;
var
  Code: String;
begin
  Result := '';
  Code := '-c "import mediagrab; print(mediagrab.__version__)"';
  if Running then
  begin
    if RunDocker('exec ' + Container + ' python ' + Code, '') then
      Result := DockerFirstLine;
  end
  else if (Image <> '') and RunDocker('run --rm --entrypoint python ' + Image + ' ' + Code, '') then
    Result := DockerFirstLine;
end;

// NOTE: Container is a parameter for the tests, which use their own.
procedure DetectExistingDocker(const Container, DefaultFolder, RememberedFolder: String);
var
  Labels, Folder, Image: String;
begin
  ExistingDockerFolder := '';
  ExistingDockerVersion := '';
  ExistingDockerState := '';
  Image := '';
  // NOTE: a container compose created knows the folder it came from.
  if RunDocker('inspect --format "{{json .Config.Labels}}" ' + Container, '') then
  begin
    Labels := DockerFirstLine;
    if JsonStringValue(Labels, 'com.docker.compose.project.working_dir', Folder) and FileExists(AddBackslash(Folder) + 'docker-compose.yml') then
      ExistingDockerFolder := Folder;
    if RunDocker('inspect --format "{{.State.Status}}" ' + Container, '') then
      ExistingDockerState := DockerFirstLine;
    if RunDocker('inspect --format "{{.Config.Image}}" ' + Container, '') then
      Image := DockerFirstLine;
  end;
  if (ExistingDockerFolder = '') and (RememberedFolder <> '') and FileExists(AddBackslash(RememberedFolder) + 'docker-compose.yml') then
    ExistingDockerFolder := RememberedFolder;
  if (ExistingDockerFolder = '') and FileExists(AddBackslash(DefaultFolder) + 'docker-compose.yml') then
    ExistingDockerFolder := DefaultFolder;
  if ExistingDockerFolder <> '' then
    ExistingDockerVersion := MediaGrabVersionIn(Container, Image, ExistingDockerState = 'running');
end;

// NOTE: the host's LAN address for MEDIAGRAB_HOST_LAN_IP (see
// DockerComposeLines); '' if it can't be found - remote access still works,
// only its displayed address/QR code would be the container's.
function HostLanIp(): String;
var
  ResultCode: Integer;
begin
  DockerFirstLine := '';
  try
    ExecAndLogOutput(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
      '-NoProfile -NonInteractive -Command "(Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway } | Select-Object -First 1).IPv4Address.IPAddress"',
      '', SW_HIDE, ewWaitUntilTerminated, ResultCode, @DockerLog);
  except
    Log(GetExceptionMessage);
  end;
  Result := DockerFirstLine;
end;

function MediaGrabAnswers(): Boolean;
var
  Http: Variant;
begin
  Result := False;
  try
    Http := CreateOleObject('WinHttp.WinHttpRequest.5.1');
    Http.SetTimeouts(2000, 2000, 2000, 2000);
    Http.Open('GET', 'http://localhost:8420/', False);
    Http.Send('');
    Result := True;
  except
  end;
end;

procedure EnsureEmptyFile(const Path: String);
begin
  // NOTE: must exist as a FILE before the first `compose up` - Docker
  // creates a missing bind-mount source as a folder, which breaks it for good.
  if not FileExists(Path) then
    SaveStringToFile(Path, '', False);
end;

// The whole Docker install/update, with its own progress page. '' on
// success, otherwise the message to show (the wizard stays on "Ready").
function RunDockerInstall(const Folder, Image, Password: String; IsUpdate: Boolean): String;
var
  Compose: String;
  Waited: Integer;
begin
  Result := '';
  Compose := AddBackslash(Folder) + 'docker-compose.yml';
  DockerProgressPage := CreateOutputProgressPage(CustomMessage('DockerInstallingCaption'), CustomMessage('DockerInstallingDescription'));
  DockerProgressPage.Show();
  try
    DockerProgressPage.SetProgress(1, 5);
    if IsUpdate then
    begin
      DockerProgressPage.SetText(CustomMessage('DockerStepCompose'), Compose);
      if not SetComposeImage(Compose, Image) then
      begin
        Result := FmtMessage(CustomMessage('DockerErrComposeUpdate'), [Compose]);
        Exit;
      end;
    end
    else
    begin
      DockerProgressPage.SetText(CustomMessage('DockerStepFolders'), Folder);
      ForceDirectories(AddBackslash(Folder) + 'data\indirilenler');
      ForceDirectories(AddBackslash(Folder) + 'data\pip-packages');
      ForceDirectories(AddBackslash(Folder) + 'data\cookies');
      ForceDirectories(AddBackslash(Folder) + 'data\stats');
      EnsureEmptyFile(AddBackslash(Folder) + 'data\settings.json');
      EnsureEmptyFile(AddBackslash(Folder) + 'data\channels.json');
      DockerProgressPage.SetText(CustomMessage('DockerStepCompose'), Compose);
      if not SaveStringsToUTF8File(Compose, DockerComposeLines(Image, Password, HostLanIp()), False) then
      begin
        Result := FmtMessage(CustomMessage('DockerErrComposeUpdate'), [Compose]);
        Exit;
      end;
    end;

    DockerProgressPage.SetProgress(2, 5);
    DockerProgressPage.SetText(CustomMessage('DockerStepPull'), Image);
    // NOTE: a failed pull isn't the end if the image is already here
    // (offline); `up` reports it clearly if it isn't.
    if not RunDocker('compose pull', Folder) then
      Log('compose pull failed: ' + DockerLastLine);

    DockerProgressPage.SetProgress(3, 5);
    DockerProgressPage.SetText(CustomMessage('DockerStepStart'), '');
    if not RunDocker('compose up -d', Folder) then
    begin
      Result := FmtMessage(CustomMessage('DockerErrStart'), [DockerLastLine, Folder]);
      Exit;
    end;

    // NOTE: "up -d" succeeding only means the container started - the app
    // inside could still fail at once (a bad password quote did, in v2.1).
    DockerProgressPage.SetProgress(4, 5);
    DockerProgressPage.SetText(CustomMessage('DockerStepWait'), 'http://localhost:8420');
    Waited := 0;
    while not MediaGrabAnswers() and (Waited < 60) do
    begin
      Sleep(1000);
      Waited := Waited + 1;
    end;
    if not MediaGrabAnswers() then
      Result := FmtMessage(CustomMessage('DockerErrNoAnswer'), [Folder]);
    DockerProgressPage.SetProgress(5, 5);
  finally
    DockerProgressPage.Hide();
    DockerProgressPage := nil;
  end;
end;

// Uninstalling a Docker install: the container goes (data stays unless the
// user picks otherwise in AskUninstallOptions). False if Docker couldn't do it.
function DockerComposeDown(const Folder: String): Boolean;
begin
  DockerExe := FindDocker();
  Result := RunDocker('compose down', Folder);
end;

// NOTE: the file types History lists (mover.py HISTORY_EXTS) - counted as
// "files" the way a person would; .json info files only add to the size.
function IsShownInHistory(const Name: String): Boolean;
var
  Ext: String;
begin
  Ext := Lowercase(ExtractFileExt(Name));
  Result := (Ext = '.mp3') or (Ext = '.m4a') or (Ext = '.opus') or (Ext = '.mp4') or (Ext = '.mkv')
    or (Ext = '.srt') or (Ext = '.txt');
end;

// NOTE: Pascal, not MediaGrab's Python - a Docker install has no Python on
// the host. data\indirilenler is MediaGrab's own mount folder there.
procedure CountFolder(const Folder: String; var Files: Integer; var Bytes: Int64);
var
  Rec: TFindRec;
begin
  if FindFirst(AddBackslash(Folder) + '*', Rec) then
  try
    repeat
      if (Rec.Name <> '.') and (Rec.Name <> '..') then
      begin
        if Rec.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0 then
          CountFolder(AddBackslash(Folder) + Rec.Name, Files, Bytes)
        else
        begin
          if IsShownInHistory(Rec.Name) then
            Files := Files + 1;
          Bytes := Bytes + Rec.SizeLow + Int64(Rec.SizeHigh) * 4294967296;
        end;
      end;
    until not FindNext(Rec);
  finally
    FindClose(Rec);
  end;
end;
