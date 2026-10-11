// The uninstaller's "what about my data?" window - included by mediagrab.iss
// inside [Code]. ReadDownloadsSummary is also run on its own by
// tests/test_installer_script.py against the real Python helper.
//
// Default is to remove only the program: settings, channels, cookies,
// statistics and every downloaded video stay, and a reinstall picks them up.
// "Also remove MediaGrab's settings" deletes %LOCALAPPDATA%\MediaGrab; the
// videos have their own box on top of that, with one more confirmation.
//
// NOTE: deleting videos is done by MediaGrab's own Python
// (mediagrab/uninstall.py) while it still exists: it deletes only what
// History shows (never the whole folder - it may hold the user's own files)
// and is unit-tested; Pascal only asks and passes the answer on.
//
// Needs the CustomMessages Uninstall* (mediagrab.iss).

var
  DeleteMediaGrabData: Boolean;
  DeleteDownloads: Boolean;
  DownloadsFolder: String;
  DownloadsCount: Integer;
  DownloadsMB: Integer;
  // NOTE: set for a Docker install, so the window says what was removed and
  // where its data is; empty = the normal install's wording.
  UninstallIntro: String;
  KeepRadio, RemoveRadio: TNewRadioButton;
  VideosBox: TNewCheckBox;

// NOTE: python.exe hidden, not pythonw: the exit code is what tells success.
function RunUninstallHelper(const PythonExe, AppDir, Command, OutFile: String): Boolean;
var
  ResultCode: Integer;
begin
  DeleteFile(OutFile);
  Result := Exec(PythonExe, '-m mediagrab.uninstall ' + Command + ' "' + OutFile + '"', AppDir,
    SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0) and FileExists(OutFile);
end;

// Fills DownloadsFolder/Count/MB; False if the helper couldn't run (then
// the videos box is simply not offered).
function ReadDownloadsSummary(const PythonExe, AppDir, OutFile: String): Boolean;
var
  Lines: TArrayOfString;
begin
  Result := RunUninstallHelper(PythonExe, AppDir, 'summary', OutFile)
    and LoadStringsFromFile(OutFile, Lines) and (GetArrayLength(Lines) >= 4);
  if Result then
  begin
    DownloadsFolder := Lines[0];
    DownloadsCount := StrToIntDef(Lines[1], 0);
    DownloadsMB := StrToIntDef(Lines[3], 0);
  end;
  DeleteFile(OutFile);
end;

function SizeText(MB: Integer): String;
begin
  if MB >= 1024 then
    Result := IntToStr(MB div 1024) + ',' + IntToStr((MB mod 1024) * 10 div 1024) + ' GB'
  else
    Result := IntToStr(MB) + ' MB';
end;

procedure UninstallChoiceChanged(Sender: TObject);
begin
  VideosBox.Enabled := RemoveRadio.Checked and (DownloadsCount > 0);
  if not VideosBox.Enabled then
    VideosBox.Checked := False;
end;

procedure AskUninstallOptions(HaveSummary: Boolean);
var
  Form: TSetupForm;
  Intro: TNewStaticText;
  OkButton: TNewButton;
  Top: Integer;
begin
  Form := CreateCustomForm(ScaleX(480), ScaleY(250), False, True);
  try
    Form.Caption := CustomMessage('UninstallOptionsCaption');
    Top := ScaleY(12);

    Intro := TNewStaticText.Create(Form);
    Intro.Parent := Form;
    Intro.Left := ScaleX(12);
    Intro.Top := Top;
    Intro.Width := Form.ClientWidth - ScaleX(24);
    Intro.WordWrap := True;
    if UninstallIntro <> '' then
      Intro.Caption := UninstallIntro
    else
      Intro.Caption := CustomMessage('UninstallOptionsIntro');
    Top := Top + Intro.Height + ScaleY(12);

    KeepRadio := TNewRadioButton.Create(Form);
    KeepRadio.Parent := Form;
    KeepRadio.Left := ScaleX(12);
    KeepRadio.Top := Top;
    KeepRadio.Width := Form.ClientWidth - ScaleX(24);
    KeepRadio.Caption := CustomMessage('UninstallKeepData');
    KeepRadio.Checked := True;
    KeepRadio.OnClick := @UninstallChoiceChanged;
    Top := Top + ScaleY(26);

    RemoveRadio := TNewRadioButton.Create(Form);
    RemoveRadio.Parent := Form;
    RemoveRadio.Left := ScaleX(12);
    RemoveRadio.Top := Top;
    RemoveRadio.Width := Form.ClientWidth - ScaleX(24);
    RemoveRadio.Caption := CustomMessage('UninstallRemoveData');
    RemoveRadio.OnClick := @UninstallChoiceChanged;
    Top := Top + ScaleY(26);

    VideosBox := TNewCheckBox.Create(Form);
    VideosBox.Parent := Form;
    VideosBox.Left := ScaleX(32);
    VideosBox.Top := Top;
    VideosBox.Width := Form.ClientWidth - ScaleX(44);
    if HaveSummary and (DownloadsCount > 0) then
      // NOTE: never start a line with "[" here - Inno reads it as a section.
      VideosBox.Caption := FmtMessage(CustomMessage('UninstallDeleteVideos'), [IntToStr(DownloadsCount),
        SizeText(DownloadsMB)])
    else
      VideosBox.Caption := CustomMessage('UninstallNoVideos');
    VideosBox.Enabled := False;
    Top := Top + ScaleY(34);

    OkButton := TNewButton.Create(Form);
    OkButton.Parent := Form;
    OkButton.Width := ScaleX(90);
    OkButton.Height := ScaleY(25);
    OkButton.Left := Form.ClientWidth - OkButton.Width - ScaleX(12);
    OkButton.Top := Top;
    OkButton.Caption := CustomMessage('UninstallContinue');
    OkButton.ModalResult := mrOk;
    OkButton.Default := True;
    Form.ClientHeight := Top + OkButton.Height + ScaleY(12);

    // NOTE: closing the window with X counts as "keep everything".
    if Form.ShowModal() = mrOk then
    begin
      DeleteMediaGrabData := RemoveRadio.Checked;
      DeleteDownloads := DeleteMediaGrabData and VideosBox.Checked;
    end;
  finally
    Form.Free();
  end;

  if DeleteDownloads then
    // NOTE: the one step that can't be undone - asked once more, "No"
    // pre-selected.
    DeleteDownloads := MsgBox(FmtMessage(CustomMessage('UninstallConfirmVideos'), [IntToStr(DownloadsCount),
      SizeText(DownloadsMB), DownloadsFolder]), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
end;
