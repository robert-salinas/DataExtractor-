$sLinkFile = "$env:USERPROFILE\Desktop\RS-DataExtractor.lnk" 
$sTargetFile = "$PSScriptRoot\run_app.bat" 
$sIconFile = "$PSScriptRoot\assets\icons\icon.ico" # Asegúrate de tener un icono ahí 
$WshShell = New-Object -ComObject WScript.Shell 
$Shortcut = $WshShell.CreateShortcut($sLinkFile) 
$Shortcut.TargetPath = $sTargetFile 
$Shortcut.IconLocation = $sIconFile 
$Shortcut.WorkingDirectory = $PSScriptRoot 
$Shortcut.Save()
