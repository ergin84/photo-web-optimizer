# Build & distribuzione

Come produrre l'eseguibile autonomo di **Photo Web Optimizer** per Windows, macOS e Linux a partire dai sorgenti.

> **Niente cross-compilation.** Per ottenere il `.exe` Windows compili su Windows, per il `.app` macOS su un Mac, per il binario Linux su Linux. Lo script `build.py` rileva il sistema e fa la cosa giusta.

## Procedura comune (tutte le piattaforme)

```bash
# 1. Crea un virtualenv dedicato al build
python3 -m venv .venv-build

# 2. Attiva il venv
#    Linux/macOS:
source .venv-build/bin/activate
#    Windows (cmd):
#    .venv-build\Scripts\activate.bat
#    Windows (PowerShell):
#    .venv-build\Scripts\Activate.ps1

# 3. Installa le dipendenze di build (PyInstaller + Pillow)
pip install -r requirements-build.txt

# 4. Compila
python build.py
```

Output:
- **Windows** → `dist\PhotoWebOptimizer.exe` (singolo file)
- **macOS**   → `dist/PhotoWebOptimizer.app` (bundle) + un eseguibile fallback
- **Linux**   → `dist/PhotoWebOptimizer` (ELF eseguibile)

## Cosa pubblicare sul sito

Carica sul tuo hosting:

| Piattaforma | File da offrire al download |
|---|---|
| Windows | `PhotoWebOptimizer.exe` (oppure uno `.zip` con `.exe + README.txt`) |
| macOS | `PhotoWebOptimizer.app` zippato (es. `PhotoWebOptimizer-mac.zip`) o, meglio, un `.dmg` |
| Linux | `PhotoWebOptimizer` (singolo binario) o un AppImage |

Suggerimento: nomi versionati, es. `PhotoWebOptimizer-1.0-win64.exe`.

## Avvertenze per l'utente finale

Inseriscile nella pagina di download:

- **Windows**: alla prima esecuzione SmartScreen mostrera *"Windows ha protetto il PC"*. L'utente deve cliccare *"Ulteriori informazioni" → "Esegui comunque"*. Per evitarlo serve firmare l'eseguibile con un certificato Authenticode (~200-400 euro/anno).
- **macOS**: Gatekeeper bloccherà l'app come *"non identificata"*. L'utente deve cliccare con il tasto destro → *Apri* → *Apri* alla prima esecuzione. Per evitarlo serve Apple Developer ID (99 USD/anno) e la notarizzazione.
- **Linux**: dopo il download l'utente deve dare permessi di esecuzione: `chmod +x PhotoWebOptimizer` e lanciarlo con `./PhotoWebOptimizer`. Su distribuzioni vecchie potrebbe mancare `libtk` (raro).
- **Antivirus falsi positivi** su .exe PyInstaller sono frequenti. Caricare il file su [VirusTotal](https://www.virustotal.com/) prima di pubblicare aiuta a diagnosticare.

## Pulizia

Lo script `build.py` rimuove automaticamente le cartelle `build/` e `dist/` precedenti prima di ricompilare. Per pulire manualmente:

```bash
rm -rf build dist *.spec
```

## Aggiornare l'icona

Le icone vengono generate proceduralmente da `make_icon.py`. Per sostituirle con la tua:

1. Sostituisci `icon.png` (consigliato 1024x1024 PNG con trasparenza).
2. Su Windows serve anche `icon.ico` (multi-size). Puoi convertire da PNG con Pillow:
   ```python
   from PIL import Image
   img = Image.open("icon.png")
   img.save("icon.ico", sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
   ```
3. Rilancia `python build.py`.
