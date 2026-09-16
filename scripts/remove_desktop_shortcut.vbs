' Remove Film Lab Desktop + Start Menu shortcuts. No PowerShell.
Option Explicit

Dim fso, sh, desktop, startMenu

Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")

desktop = sh.SpecialFolders("Desktop")
If fso.FileExists(desktop & "\Film Lab.lnk") Then fso.DeleteFile desktop & "\Film Lab.lnk", True
If fso.FileExists(desktop & "\Film Lab Repair.lnk") Then fso.DeleteFile desktop & "\Film Lab Repair.lnk", True
If fso.FileExists(desktop & "\Install Film Lab.lnk") Then fso.DeleteFile desktop & "\Install Film Lab.lnk", True

startMenu = sh.SpecialFolders("StartMenu") & "\Programs\Film Lab"
If fso.FolderExists(startMenu) Then fso.DeleteFolder startMenu, True

WScript.Echo "Removed Film Lab Desktop and Start Menu shortcuts."
