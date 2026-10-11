// Closes a running MediaGrab before files are replaced or removed - included
// by mediagrab.iss inside [Code], and run on its own by
// tests/test_installer_script.py against a real tray icon.
//
// Needs the CustomMessages MediaGrabRunning (asked unless Silent).

const
  // NOTE: the hidden window of MediaGrab's tray icon (mediagrab/tray.py
  // TRAY_WINDOW_CLASS - a test keeps the two in step).
  MediaGrabWindowClass = 'MediaGrabTrayWindow';
  WM_CLOSE = $0010;

// NOTE: a running MediaGrab holds python314.dll and friends open, and the
// Restart Manager (CloseApplications) can't close a windowless pythonw - it
// asked the user to close "Python" by hand. Instead: ask MediaGrab itself
// through its tray window, the same as its own Quit, and wait for it.
// True when MediaGrab isn't running (any more). Versions without a tray
// icon have no such window - the Restart Manager remains the fallback.
function CloseMediaGrab(Silent: Boolean): Boolean;
var
  Waited: Integer;
begin
  Result := True;
  if FindWindowByClassName(MediaGrabWindowClass) = 0 then
    Exit;
  if not Silent then
    if MsgBox(CustomMessage('MediaGrabRunning'), mbConfirmation, MB_OKCANCEL) <> IDOK then
    begin
      Result := False;
      Exit;
    end;
  PostMessage(FindWindowByClassName(MediaGrabWindowClass), WM_CLOSE, 0, 0);
  Waited := 0;
  while (FindWindowByClassName(MediaGrabWindowClass) <> 0) and (Waited < 20000) do
  begin
    Sleep(250);
    Waited := Waited + 250;
  end;
  Result := FindWindowByClassName(MediaGrabWindowClass) = 0;
  if Result then
    // NOTE: the window goes just before the process ends - a moment for
    // Python to let go of its files.
    Sleep(1500);
end;
