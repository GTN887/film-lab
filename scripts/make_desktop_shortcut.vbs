' Pin Film Lab on the Desktop + Start Menu with the studio icon.
' Called by INSTALL_FILM_LAB.bat. No PowerShell.
Option Explicit

Dim fso, sh, root, desktop, startMenu, startBat, repairBat, ico
Dim deskLnk, repairLnk, menuDir, menuLnk, menuRepair, menuUn, marker, escaped

Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")

If WScript.Arguments.Count >= 1 Then
    root = WScript.Arguments(0)
Else
    root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
End If
If Right(root, 1) = "\" Then root = Left(root, Len(root) - 1)

startBat = root & "\START_FILM_LAB.bat"
repairBat = root & "\REPAIR.bat"
ico = root & "\assets\film_lab.ico"

If Not fso.FileExists(startBat) Then
    WScript.Echo "START_FILM_LAB.bat missing at " & startBat
    WScript.Quit 1
End If

desktop = sh.SpecialFolders("Desktop")
Set deskLnk = sh.CreateShortcut(desktop & "\Film Lab.lnk")
deskLnk.TargetPath = startBat
deskLnk.WorkingDirectory = root
deskLnk.WindowStyle = 1
deskLnk.Description = "Film Lab — local studio (double-click, no PowerShell)"
If fso.FileExists(ico) Then deskLnk.IconLocation = ico & ",0"
deskLnk.Save

If fso.FileExists(repairBat) Then
    Set repairLnk = sh.CreateShortcut(desktop & "\Film Lab Repair.lnk")
    repairLnk.TargetPath = repairBat
    repairLnk.WorkingDirectory = root
    repairLnk.WindowStyle = 1
    repairLnk.Description = "Film Lab Repair — restart desk / Comfy / ports"
    If fso.FileExists(ico) Then repairLnk.IconLocation = ico & ",0"
    repairLnk.Save
End If

startMenu = sh.SpecialFolders("StartMenu") & "\Programs\Film Lab"
If Not fso.FolderExists(startMenu) Then fso.CreateFolder startMenu
Set menuLnk = sh.CreateShortcut(startMenu & "\Film Lab.lnk")
menuLnk.TargetPath = startBat
menuLnk.WorkingDirectory = root
menuLnk.WindowStyle = 1
menuLnk.Description = "Film Lab — local studio"
If fso.FileExists(ico) Then menuLnk.IconLocation = ico & ",0"
menuLnk.Save

If fso.FileExists(repairBat) Then
    Set menuRepair = sh.CreateShortcut(startMenu & "\Repair.lnk")
    menuRepair.TargetPath = repairBat
    menuRepair.WorkingDirectory = root
    menuRepair.WindowStyle = 1
    If fso.FileExists(ico) Then menuRepair.IconLocation = ico & ",0"
    menuRepair.Save
End If

If fso.FileExists(root & "\UNINSTALL_FILM_LAB.bat") Then
    Set menuUn = sh.CreateShortcut(startMenu & "\Uninstall Film Lab.lnk")
    menuUn.TargetPath = root & "\UNINSTALL_FILM_LAB.bat"
    menuUn.WorkingDirectory = root
    menuUn.WindowStyle = 1
    menuUn.Description = "Remove Film Lab shortcuts and optional install folder"
    If fso.FileExists(ico) Then menuUn.IconLocation = ico & ",0"
    menuUn.Save
End If

If Not fso.FolderExists(root & "\data") Then fso.CreateFolder root & "\data"
Dim marker, escaped
escaped = Replace(root, "\", "\\")
Set marker = fso.CreateTextFile(root & "\data\install.json", True)
marker.Write "{"
marker.Write """managed"":true,"
marker.Write """patch_in_place"":true,"
marker.Write """root"":""" & escaped & """"
marker.Write "}"
marker.Close

WScript.Echo "Desktop shortcut: " & desktop & "\Film Lab.lnk"
WScript.Echo "Start Menu: " & startMenu
WScript.Echo "Icon: " & ico
WScript.Echo "Patch in place: Grok Bot / Cursor can edit " & root
WScript.Echo "Uninstall: " & root & "\UNINSTALL_FILM_LAB.bat"
WScript.Echo "Double-click Film Lab. Works offline for local generation."
