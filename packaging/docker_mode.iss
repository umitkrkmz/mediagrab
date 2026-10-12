// "Install with Docker" - the docker-compose.yml side. Included by
// mediagrab.iss inside [Code]; the functions here are also run on their own
// by tests/test_installer_script.py, and their output is checked with
// Docker's own parser (docker compose config).
//
// NOTE: this replaces the Docker mode of the old Tk installer
// (setup_mediagrab.py, retired in v2.4.0) and keeps its compose layout -
// the same volumes and the same C:\MediaGrab default - so a Docker install
// made with it is found and updated in place.

// A value for a double-quoted YAML list item. NOTE: the whole "KEY=VALUE"
// item is quoted, not just the value - `- KEY="VALUE"` hands the container
// the quote characters too (seen in v2.1). "$" is doubled: compose reads
// $NAME in the file as a variable and a password containing "$" arrived cut
// short (the old installer didn't do this).
function ComposeQuote(const Value: String): String;
begin
  Result := Value;
  StringChangeEx(Result, '\', '\\', True);
  StringChangeEx(Result, '"', '\"', True);
  StringChangeEx(Result, '$', '$$', True);
end;

procedure AddLine(var Lines: TArrayOfString; const Line: String);
var
  Count: Integer;
begin
  Count := GetArrayLength(Lines);
  SetArrayLength(Lines, Count + 1);
  Lines[Count] := Line;
end;

// NOTE: bridge networking + a mapped port, not the repo's own
// docker-compose.yml (network_mode: host) - Docker Desktop on Windows has no
// host networking. MEDIAGRAB_HOST_LAN_IP: inside the container the app only
// sees its bridge address, so Remote Access's LAN address/QR code would be
// unreachable without the host's real one.
function DockerComposeLines(const Image, Password, LanIp: String): TArrayOfString;
begin
  AddLine(Result, '# Written by the MediaGrab Windows installer. Updating = running a newer');
  AddLine(Result, '# MediaGrab installer, which changes the image line below.');
  AddLine(Result, 'services:');
  AddLine(Result, '  mediagrab:');
  AddLine(Result, '    image: ' + Image);
  AddLine(Result, '    container_name: mediagrab');
  AddLine(Result, '    restart: unless-stopped');
  AddLine(Result, '    ports:');
  AddLine(Result, '      - "8420:8420"');
  AddLine(Result, '    environment:');
  AddLine(Result, '      - "MEDIAGRAB_INITIAL_PASSWORD=' + ComposeQuote(Password) + '"');
  AddLine(Result, '      - "MEDIAGRAB_INSTALLED_BY=windows-installer"');
  if LanIp <> '' then
    AddLine(Result, '      - "MEDIAGRAB_HOST_LAN_IP=' + ComposeQuote(LanIp) + '"');
  AddLine(Result, '    volumes:');
  AddLine(Result, '      - ./data/indirilenler:/app/indirilenler');
  AddLine(Result, '      - ./data/settings.json:/app/settings.json');
  AddLine(Result, '      - ./data/channels.json:/app/channels.json');
  AddLine(Result, '      - ./data/pip-packages:/data/pip-packages');
  AddLine(Result, '      - ./data/cookies:/data/cookies');
  AddLine(Result, '      - ./data/stats:/data/stats');
end;

// An update: only the image line changes (everything else - the password,
// the folders, anything the user edited - stays), and an older file gets
// the MEDIAGRAB_INSTALLED_BY line Settings' update notice relies on.
// False if no MediaGrab image line was found.
function SetComposeImage(const ComposePath, Image: String): Boolean;
var
  Lines, Updated: TArrayOfString;
  I: Integer;
  Line, Trimmed: String;
  HasMarker: Boolean;
begin
  Result := False;
  if not LoadStringsFromFile(ComposePath, Lines) then
    Exit;
  HasMarker := False;
  for I := 0 to GetArrayLength(Lines) - 1 do
    if Pos('MEDIAGRAB_INSTALLED_BY', Lines[I]) > 0 then
      HasMarker := True;
  for I := 0 to GetArrayLength(Lines) - 1 do
  begin
    Line := Lines[I];
    Trimmed := Trim(Line);
    if (not Result) and (Pos('image:', Trimmed) = 1) and (Pos('mediagrab', Lowercase(Trimmed)) > 0) then
    begin
      Line := Copy(Line, 1, Pos('image:', Line) - 1) + 'image: ' + Image;
      Result := True;
    end;
    AddLine(Updated, Line);
    if (not HasMarker) and (Trimmed = 'environment:') then
    begin
      AddLine(Updated, Copy(Line, 1, Pos('environment:', Line) - 1) + '  - "MEDIAGRAB_INSTALLED_BY=windows-installer"');
      HasMarker := True;
    end;
  end;
  if Result then
    Result := SaveStringsToUTF8File(ComposePath, Updated, False);
end;
