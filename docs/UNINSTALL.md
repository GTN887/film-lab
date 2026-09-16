# Uninstall Film Lab

Film Lab is a folder of files plus two shortcuts. Nothing is registered as a Windows service.

## Remove shortcuts + folder

1. Close the **Film Lab** and **Film Lab Comfy** windows.
2. Start Menu → **Film Lab** → **Uninstall Film Lab**, or double-click **UNINSTALL_FILM_LAB.bat** in the install folder.
3. **1** — remove Desktop / Start Menu shortcuts only. Files stay. Grok Bot can still patch.
4. **2** — remove shortcuts **and** delete the install folder. Type `DELETE` to confirm.

The uninstaller refuses to delete your user profile, Desktop, or a folder that still has `.git` (a source checkout). Delete a git clone yourself in Explorer.

Inno Setup `Install_Film_Lab.exe` also has the normal Windows **Apps → Film Lab → Uninstall** entry. That removes the files it copied. Run **UNINSTALL_FILM_LAB.bat** first if you want the Desktop shortcuts gone before Apps uninstall.

## Keep the folder (patch in place)

Point **Grok Bot / Cursor** at the install folder (`Desktop\Film Lab` or `%LOCALAPPDATA%\Film Lab`). Edit `app.py` and `film_lab\` there. Next **START_FILM_LAB.bat** picks up the patch. No reinstall.

`data/install.json` marks a managed install (`patch_in_place: true`).

## Manual delete

1. Delete **Film Lab.lnk** and **Film Lab Repair.lnk** from the Desktop.
2. Delete `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Film Lab`.
3. Delete the install folder.

See [PACKAGING.md](PACKAGING.md), [DESKTOP.md](DESKTOP.md).
