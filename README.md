# Photo Web Optimizer

**Built for web developers who need to prepare large photo batches for the web — fast and consistently.**

Drop in a folder of full-resolution photos, get back a `web/` folder containing every image in 4 sizes × 2 formats, ready to drop into `<picture>` / `srcset` / a CMS / a static site. Same naming convention, same quality settings, every time. No manual export from Photoshop / Lightroom for each shoot.

For each source image you get, inside `web/`:

| Variant | Longest side | Formats |
|---|---|---|
| `large`  | 1920 px | progressive JPEG + WebP |
| `medium` | 1200 px | progressive JPEG + WebP |
| `small`  |  800 px | progressive JPEG + WebP |
| `thumb`  |  400 px | progressive JPEG + WebP |

- EXIF orientation honoured, EXIF metadata stripped (smaller files, no GPS leaking)
- Filenames slugified to URL-safe form (`Beach Photo #3.JPG` → `beach-photo-3-large.webp`)
- Parallel processing on all CPU cores
- Simple desktop GUI — multi-select files, or pick a whole folder

Supported input formats: `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.webp`.

## Download

Pre-built executables are published on the [Releases page](../../releases/latest):

| Platform | File |
|---|---|
| Windows 10/11 | `PhotoWebOptimizer-windows-x64.exe` |
| macOS         | `PhotoWebOptimizer-macos.zip` (contains the `.app`) |
| Linux x64     | `PhotoWebOptimizer-linux-x64` |

Stable download URLs (always point to the latest release):

```
https://github.com/ergin84/photo-web-optimizer/releases/latest/download/PhotoWebOptimizer-windows-x64.exe
https://github.com/ergin84/photo-web-optimizer/releases/latest/download/PhotoWebOptimizer-macos.zip
https://github.com/ergin84/photo-web-optimizer/releases/latest/download/PhotoWebOptimizer-linux-x64
```

### First-run notes

The binaries are not code-signed, so the OS will warn you before launching:

- **Windows**: SmartScreen will say *"Windows protected your PC"* → click *More info* → *Run anyway*.
- **macOS**: Gatekeeper will refuse to open an unidentified developer's app → right-click the `.app` → *Open* → *Open*.
- **Linux**: `chmod +x PhotoWebOptimizer && ./PhotoWebOptimizer`.

## Usage

1. Launch the app.
2. Click **Seleziona foto...** (or **Seleziona cartella...**) to add images.
3. Click **Avvia ottimizzazione**.
4. Optimized variants are written to a `web/` folder next to each source image.

If you select photos from multiple folders, each folder gets its own `web/` subfolder — handy when processing several shoots in one session.

## Headless / CLI mode

For CI pipelines, build scripts, or just a faster workflow in the terminal:

```bash
python3 optimize_for_web.py /path/to/photos
python3 optimize_for_web.py /path/to/photos -o web -j 8
```

Flags:
- `-o, --output`  output subfolder name (default `web`)
- `-j, --jobs`    worker processes (default = number of CPU cores)

## Running from source

```bash
pip install pillow
python3 photo_optimizer_gui.py        # GUI
python3 optimize_for_web.py .         # CLI
```

## Building executables from source

See [BUILD.md](BUILD.md) for full details. Short version (run on the OS you want to target — no cross-compilation):

```bash
python3 -m venv .venv-build
source .venv-build/bin/activate       # Windows: .venv-build\Scripts\activate
pip install -r requirements-build.txt
python build.py
```

Output appears in `dist/`.

## Automated releases

Pushing a `v*` tag triggers the [GitHub Actions workflow](.github/workflows/release.yml), which builds Windows + macOS + Linux in parallel on GitHub-hosted runners and publishes a Release with all three binaries attached.

```bash
git tag -a v1.1.0 -m "your changelog here"
git push origin v1.1.0
```

## Customizing the output

The defaults are tuned for typical website use (good quality / good file size). To change them, edit the top of [`optimize_for_web.py`](optimize_for_web.py):

```python
SIZES = [
    ("large", 1920),
    ("medium", 1200),
    ("small", 800),
    ("thumb", 400),
]
JPEG_QUALITY = 82
WEBP_QUALITY = 80
```

## License

No license attached yet — code is © Ergin Mehmeti, all rights reserved. Open an issue if you want a permissive license added.
