// Reads MediaGrab's download folder setting from settings.json - included by
// mediagrab.iss inside [Code], and compiled on its own by
// tests/test_installer_script.py with real ISCC.
//
// NOTE: Inno has no JSON parser. This only has to read one flat string value
// written by Python's json.dump (store.py: ensure_ascii=False, so non-ASCII
// arrives as UTF-8 and only \\ \" \/ and \uXXXX escapes can appear in a
// folder path). Anything unexpected returns '' - the page then simply offers
// the default folder, never a garbled one.

function JsonStringValue(const Json, Key: String; var Value: String): Boolean;
var
  P, I, Code: Integer;
  C: Char;
begin
  Result := False;
  Value := '';
  // NOTE: with the quotes included this can't match a longer key
  // ("last_download_dir") or text inside another value (quotes in a JSON
  // value are escaped).
  P := Pos('"' + Key + '"', Json);
  if P = 0 then Exit;
  I := P + Length(Key) + 2;
  while (I <= Length(Json)) and ((Json[I] = ' ') or (Json[I] = #9) or (Json[I] = #13) or (Json[I] = #10) or (Json[I] = ':')) do
    I := I + 1;
  if (I > Length(Json)) or (Json[I] <> '"') then Exit;
  I := I + 1;
  while I <= Length(Json) do
  begin
    C := Json[I];
    if C = '"' then
    begin
      Result := True;
      Exit;
    end;
    if C = '\' then
    begin
      I := I + 1;
      if I > Length(Json) then Exit;
      C := Json[I];
      if (C = '"') or (C = '\') or (C = '/') then
        Value := Value + C
      else if C = 'u' then
      begin
        if I + 4 > Length(Json) then Exit;
        Code := StrToIntDef('$' + Copy(Json, I + 1, 4), -1);
        if Code < 0 then Exit;
        Value := Value + Chr(Code);
        I := I + 4;
      end
      else
        Exit;  // \n, \t ... never part of a folder path
    end
    else
      Value := Value + C;
    I := I + 1;
  end;
end;

// The folder in an existing settings.json, or '' (no file, no setting,
// the default folder, or anything unreadable).
function ReadDownloadDirSetting(const SettingsPath: String): String;
var
  Raw: AnsiString;
begin
  Result := '';
  if not LoadStringFromFile(SettingsPath, Raw) then Exit;
  if not JsonStringValue(UTF8Decode(Raw), 'download_dir', Result) then
    Result := '';
end;
