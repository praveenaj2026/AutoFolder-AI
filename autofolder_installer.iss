; AutoFolder AI - Professional Windows Installer Script
; Built with Inno Setup 6.x
; https://jrsoftware.org/isinfo.php

#define MyAppName "AutoFolder AI"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "AutoFolder AI"
#define MyAppURL "https://github.com/praveenaj2026/AutoFolder-AI"
#define MyAppExeName "AutoFolder AI.exe"
#define MyAppDescription "AI-Powered File Organization Tool"
#define MyAppId "{{A8B7C9D6-E5F4-4321-9876-1234567890AB}"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
; Uncomment the following line if you have an info/readme file
; InfoBeforeFile=README.md
OutputDir=installer_output
OutputBaseFilename=AutoFolder-AI-Setup-v{#MyAppVersion}
SetupIconFile=resources\icons\app_icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; Require Windows 10 or later
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
; Privileges - do not require admin for install
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
; Modern look
WizardImageFile=compiler:WizModernImage-IS.bmp
WizardSmallImageFile=compiler:WizModernSmallImage-IS.bmp

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "startup"; Description: "Launch {#MyAppName} at Windows startup"; GroupDescription: "Additional options:"; Flags: unchecked

[Files]
; Main executable
Source: "dist\AutoFolder AI\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; All other files and folders from the PyInstaller build
; This includes: _internal folder with AI models, config, resources, DLLs, etc.
Source: "dist\AutoFolder AI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Tesseract OCR installer (optional - users can install via app menu)
Source: "tesseract-ocr-w64-setup-5.5.0.20241111.exe"; DestDir: "{app}\third_party"; Flags: ignoreversion; Check: FileExists(ExpandConstant('{src}\tesseract-ocr-w64-setup-5.5.0.20241111.exe'))

; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppDescription}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\User Guide"; Filename: "{app}\README.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "{#MyAppDescription}"

; Quick Launch (Windows 7 and earlier)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

; Startup folder (optional)
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startup

[Registry]
; Register application for "Open With" dialogs (optional)
Root: HKCU; Subkey: "Software\Classes\.autofolder"; ValueType: string; ValueName: ""; ValueData: "AutoFolderFile"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\AutoFolderFile"; ValueType: string; ValueName: ""; ValueData: "AutoFolder AI Project"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\AutoFolderFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKCU; Subkey: "Software\Classes\AutoFolderFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

; Store installation path for the app to find resources
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey

[Run]
; Option to launch the app after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up user data (optional - be careful with this!)
; Uncomment if you want to remove user config/logs on uninstall
; Type: filesandordirs; Name: "{userappdata}\AutoFolder AI"
; Type: filesandordirs; Name: "{userdocs}\AutoFolder_Logs"

; Clean up any generated files in installation directory
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\__pycache__"

[Code]
// Pascal script for advanced installer logic

// Check if the app is currently running
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  // Check if app is running
  if CheckForMutexes('AutoFolderAIMutex') then
  begin
    if MsgBox('AutoFolder AI is currently running. Please close it before continuing with the installation.', 
              mbError, MB_OKCANCEL) = IDOK then
    begin
      Result := False;
    end
    else
    begin
      Result := False;
    end;
  end;
end;

// Custom uninstall confirmation
function InitializeUninstall(): Boolean;
var
  Response: Integer;
begin
  Response := MsgBox('Are you sure you want to uninstall AutoFolder AI?' + #13#10 + #13#10 +
                     'Your settings and logs will be preserved in:' + #13#10 +
                     ExpandConstant('{userappdata}\AutoFolder AI'), 
                     mbConfirmation, MB_YESNO);
  Result := Response = IDYES;
end;

// Post-install message
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Any post-install actions can go here
  end;
end;

// Custom welcome message
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  
  if CurPageID = wpWelcome then
  begin
    // Custom logic on welcome page if needed
  end;
end;

// Check for .NET or other dependencies (if needed)
function DependenciesInstalled(): Boolean;
begin
  // Add dependency checks here if needed
  // For example, check for Visual C++ Redistributable
  Result := True;
end;
