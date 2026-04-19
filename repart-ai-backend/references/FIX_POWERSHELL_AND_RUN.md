# Fix "scripts disabled" and run everything

## 1. Fix PowerShell script execution (one-time)

In **PowerShell** (Run as Administrator, or your user is enough), run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Type `Y` and Enter. After this, `Activate.ps1`, `npm`, and other `.ps1` scripts will run.

---

## 2. Run without fixing (use .bat files)

Use **Command Prompt (cmd)** or double-click these in File Explorer. No PowerShell scripts run.

| What        | How |
|------------|-----|
| **Backend**  | Double-click `run_backend.bat` or in cmd: `run_backend.bat` |
| **Frontend** | Double-click `run_frontend.bat` (edit path inside if your folder is different) |
| **ngrok**    | Install ngrok first (`winget install ngrok.ngrok`), then run `run_ngrok.bat` |

Run **backend** first, then **ngrok**, then **frontend** (each in its own window).

---

## 3. ngrok not found

Install ngrok, then restart the terminal:

```powershell
winget install ngrok.ngrok
```

Or download from https://ngrok.com/download and put `ngrok.exe` in a folder that is on your PATH, or use its full path in `run_ngrok.bat` (e.g. `"C:\ngrok\ngrok.exe" http 8000`).
