# Photo Web Optimizer

Applicazione desktop che genera versioni web-ottimizzate delle tue foto. Per ogni immagine produce 4 dimensioni (large/medium/small/thumb) in JPEG progressivo + WebP, nella sottocartella `web/` accanto agli originali.

- EXIF orientation rispettato, metadata rimossi
- Nomi file *slugified* (URL-safe)
- GUI semplice (tkinter) — multi-selezione file o cartella intera
- Elaborazione parallela in background

## Download

Versioni precompilate disponibili nella [pagina Releases](../../releases/latest):

| Piattaforma | File |
|---|---|
| Windows 10/11 | `PhotoWebOptimizer-windows-x64.exe` |
| macOS         | `PhotoWebOptimizer-macos.zip` (contiene `.app`) |
| Linux x64     | `PhotoWebOptimizer-linux-x64` |

**Avvertenze prima esecuzione**
- **Windows**: SmartScreen avvisa *"Windows ha protetto il PC"* → *Ulteriori informazioni* → *Esegui comunque*.
- **macOS**: Gatekeeper blocca app non firmate → tasto destro sull'app → *Apri* → *Apri*.
- **Linux**: `chmod +x PhotoWebOptimizer && ./PhotoWebOptimizer`.

## Uso

1. Avvia l'app.
2. Premi **Seleziona foto...** (o **Seleziona cartella...**) per aggiungere immagini.
3. Premi **Avvia ottimizzazione**.
4. Le foto ottimizzate appaiono in una sottocartella `web/` accanto agli originali.

Formati di input supportati: `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.webp`.

## Eseguire dai sorgenti

```bash
pip install pillow
python3 photo_optimizer_gui.py
```

Oppure modalità CLI senza GUI:
```bash
python3 optimize_for_web.py /percorso/cartella
```

## Build da sorgente

Vedi [BUILD.md](BUILD.md) per istruzioni dettagliate. In sintesi, sulla piattaforma target:

```bash
python3 -m venv .venv-build
source .venv-build/bin/activate   # Windows: .venv-build\Scripts\activate
pip install -r requirements-build.txt
python build.py
```

## Rilascio automatico

Il push di un tag `v*` (es. `v1.0.0`) attiva [GitHub Actions](.github/workflows/release.yml) che compila Windows + macOS + Linux in parallelo e pubblica una Release con i binari allegati.
