# Film Lab — Creator Start

This folder is the authoritative consolidated Film Lab branch.

## Normal daily launch

On Windows, run **OPEN_FILM_LAB_APP.bat**. It starts the existing Film Lab server underneath and opens the UI in a dedicated Film Lab desktop window.

## Backup launch

If the native window component cannot open, run **OPEN_BROWSER_BACKUP.bat**. The localhost URL is a backup/developer transport, not the intended Creator experience.

## First install

Run **INSTALL_FILM_LAB.bat** once to create the local Python environment and install dependencies. The consolidated requirements include `pywebview` for the dedicated application window.

## Engineering truth

Read `AUTHORITATIVE_AUDIT.md`. The application contains many real subsystems, but real AMD generative motion, advanced consistency graphs, targeted Mark & Direct regeneration, and full Scene World remain runtime gates rather than assumed-complete features.
