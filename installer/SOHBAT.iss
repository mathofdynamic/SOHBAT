#ifndef AppVersion
  #error "Build using scripts/build-installer.ps1 so the version matches the app."
#endif
#ifndef PayloadDir
  #define PayloadDir "..\.perfection\installer-payload"
#endif

[Setup]
; This AppId is permanent. NEVER change it for a future version.
AppId={{D0E533D9-A5F2-44B0-B513-BDA47EE40618}
AppName=SOHBAT
AppVersion={#AppVersion}
AppPublisher=Mohammad H Mohammady
AppPublisherURL=https://github.com/mathofdynamic/SOHBAT
AppSupportURL=https://github.com/mathofdynamic/SOHBAT/issues
AppUpdatesURL=https://github.com/mathofdynamic/SOHBAT/releases
DefaultDirName={localappdata}\Programs\SOHBAT
UsePreviousAppDir=yes
DisableDirPage=auto
DisableProgramGroupPage=yes
DefaultGroupName=SOHBAT
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.19041
UninstallDisplayIcon={app}\SOHBAT.exe
SetupIconFile=..\sohbat\assets\brand\app.ico
WizardSmallImageFile={#PayloadDir}\logo.bmp
LicenseFile=..\LICENSE
WizardStyle=modern
WizardSizePercent=120,120
DisableWelcomePage=no
OutputDir=..\dist\installers
OutputBaseFilename=SOHBAT-Setup-{#AppVersion}-windows-x64
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
SetupMutex=SOHBAT.Installer
VersionInfoVersion={#AppVersion}
VersionInfoDescription=SOHBAT offline dictation installer

[Files]
Source: "..\dist\SOHBAT\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#PayloadDir}\models\tiny-streaming-en\*"; DestDir: "{app}\models\tiny-streaming-en"; Flags: ignoreversion
Source: "{#PayloadDir}\licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion
Source: "THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\banner.bmp"; Flags: dontcopy
Source: "..\sohbat\assets\fonts\Inter.ttf"; Flags: dontcopy

[Icons]
Name: "{userprograms}\SOHBAT"; Filename: "{app}\SOHBAT.exe"; WorkingDir: "{app}"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SOHBAT"; ValueData: """{app}\SOHBAT.exe"""; Flags: uninsdeletevalue; Check: StartupEnabled
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "Flowlet"; Flags: deletevalue

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"; Check: CleanPreviousRuntime
Type: files; Name: "{userprograms}\Flowlet.lnk"

[Run]
Filename: "{app}\SOHBAT.exe"; Description: "Open SOHBAT"; Flags: nowait postinstall skipifsilent

[Code]
function AddFontResourceEx(FileName: String; Flags, Reserved: Cardinal): Integer;
  external 'AddFontResourceExW@gdi32.dll stdcall';
function RemoveFontResourceEx(FileName: String; Flags, Reserved: Cardinal): Boolean;
  external 'RemoveFontResourceExW@gdi32.dll stdcall';

function InitializeSetup: Boolean;
var Directory: String;
    VersionMS, VersionLS: Cardinal;
    NewVersion: Int64;
begin
  Result := True;
  if not RegQueryStringValue(HKCU,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{D0E533D9-A5F2-44B0-B513-BDA47EE40618}_is1',
    'InstallLocation', Directory) then
    Directory := ExpandConstant('{localappdata}\Programs\SOHBAT');
  if GetVersionNumbers(AddBackslash(Directory) + 'SOHBAT.exe', VersionMS, VersionLS)
    and StrToVersion('{#AppVersion}', NewVersion) then
    if ComparePackedVersion(PackVersionNumbers(VersionMS, VersionLS), NewVersion) > 0 then begin
      SuppressibleMsgBox('A newer version of SOHBAT is already installed. This older installer will not replace it.', mbError, MB_OK, IDOK);
      Result := False;
    end;
end;

function CleanPreviousRuntime: Boolean;
var Expected: String;
begin
  if not RegQueryStringValue(HKCU,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{D0E533D9-A5F2-44B0-B513-BDA47EE40618}_is1',
    'InstallLocation', Expected) then
    Expected := ExpandConstant('{localappdata}\Programs\SOHBAT');
  Result := (CompareText(AddBackslash(Expected), AddBackslash(ExpandConstant('{app}'))) = 0)
    and FileExists(ExpandConstant('{app}\SOHBAT.exe'));
end;

function StartupEnabled: Boolean;
var Value: String;
begin
  Result := RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'SOHBAT', Value)
    or RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'Flowlet', Value);
end;

procedure AddBanner(Page: TNewNotebookPage; Title, Description: TNewStaticText);
var Banner: TBitmapImage;
    Inset: Integer;
begin
  Inset := ScaleX(22);
  Banner := TBitmapImage.Create(WizardForm);
  Banner.Parent := Page;
  Banner.Left := 0;
  Banner.Top := 0;
  Banner.Width := Page.ClientWidth;
  Banner.Height := Banner.Width div 3;
  Banner.Stretch := True;
  Banner.Bitmap.LoadFromFile(ExpandConstant('{tmp}\banner.bmp'));
  Title.Left := Inset;
  Title.Top := Banner.Height + ScaleY(18);
  Title.Width := Page.ClientWidth - Inset * 2;
  Title.Font.Name := 'Inter';
  Title.Font.Size := 18;
  Description.Font.Name := 'Inter';
  Description.Left := Inset;
  Description.Top := Title.Top + Title.Height + ScaleY(14);
  Description.Width := Page.ClientWidth - Inset * 2;
  Description.Height := Page.ClientHeight - Description.Top - ScaleY(8);
end;

procedure InitializeWizard;
begin
  ExtractTemporaryFile('banner.bmp');
  ExtractTemporaryFile('Inter.ttf');
  if AddFontResourceEx(ExpandConstant('{tmp}\Inter.ttf'), $10, 0) > 0 then
    WizardForm.Font.Name := 'Inter';
  WizardForm.WizardBitmapImage.Visible := False;
  WizardForm.WizardBitmapImage2.Visible := False;
  AddBanner(WizardForm.WelcomePage, WizardForm.WelcomeLabel1, WizardForm.WelcomeLabel2);
  AddBanner(WizardForm.FinishedPage, WizardForm.FinishedHeadingLabel, WizardForm.FinishedLabel);
  WizardForm.WelcomeLabel1.Caption := 'Install SOHBAT {#AppVersion}';
  WizardForm.WelcomeLabel2.Caption := 'Private, offline dictation for Windows.' + #13#10 + #13#10 +
    'Includes the English speech model. No Python or model download is required.' + #13#10 + #13#10 +
    'Future versions update this same installation and preserve your preferences.';
end;

procedure DeinitializeSetup;
begin
  RemoveFontResourceEx(ExpandConstant('{tmp}\Inter.ttf'), $10, 0);
end;

