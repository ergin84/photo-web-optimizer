#!/usr/bin/env python3
"""Desktop GUI for optimize_for_web.

L'utente seleziona una o piu foto (anche da cartelle diverse) e l'app
genera, accanto a ciascuna foto, una sottocartella ``web/`` con le
versioni ottimizzate (JPEG + WebP, 4 dimensioni) prodotte dalla logica
di ``optimize_for_web.py``.
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from optimize_for_web import (
    SIZES,
    SOURCE_EXTENSIONS,
    human_bytes,
    process_one,
)


class PhotoOptimizerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Photo Web Optimizer")
        self.root.geometry("760x560")
        self.root.minsize(640, 480)

        self.files: list[Path] = []
        self.msg_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.worker: threading.Thread | None = None

        self._build_ui()
        self.root.after(100, self._drain_queue)

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 6}

        top = ttk.Frame(self.root)
        top.pack(fill="x", **pad)

        ttk.Button(top, text="Seleziona foto...", command=self.pick_files).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(top, text="Seleziona cartella...", command=self.pick_folder).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(top, text="Rimuovi selezionati", command=self.remove_selected).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(top, text="Pulisci lista", command=self.clear_files).pack(
            side="left"
        )

        info = (
            f"Output: sottocartella 'web/' nella stessa cartella delle foto.   "
            f"Formati: JPEG + WebP   Dimensioni: "
            + ", ".join(f"{l} ({s}px)" for l, s in SIZES)
        )
        ttk.Label(self.root, text=info, foreground="#555").pack(
            anchor="w", padx=8
        )

        list_frame = ttk.LabelFrame(self.root, text="File selezionati")
        list_frame.pack(fill="both", expand=True, **pad)

        self.listbox = tk.Listbox(list_frame, selectmode="extended", activestyle="none")
        scroll = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.listbox.yview
        )
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.progress = ttk.Progressbar(
            self.root, orient="horizontal", mode="determinate"
        )
        self.progress.pack(fill="x", **pad)

        log_frame = ttk.LabelFrame(self.root, text="Log")
        log_frame.pack(fill="both", expand=True, **pad)

        self.log = tk.Text(log_frame, height=8, state="disabled", wrap="word")
        log_scroll = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log.yview
        )
        self.log.configure(yscrollcommand=log_scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", **pad)

        self.status_var = tk.StringVar(value="Pronto.")
        ttk.Label(bottom, textvariable=self.status_var).pack(side="left")

        self.start_btn = ttk.Button(
            bottom, text="Avvia ottimizzazione", command=self.start
        )
        self.start_btn.pack(side="right")

    def pick_files(self) -> None:
        types = [
            (
                "Immagini",
                " ".join(f"*{ext}" for ext in sorted(SOURCE_EXTENSIONS)),
            ),
            ("Tutti i file", "*.*"),
        ]
        paths = filedialog.askopenfilenames(
            title="Seleziona una o piu foto", filetypes=types
        )
        if paths:
            self._add_paths(Path(p) for p in paths)

    def pick_folder(self) -> None:
        folder = filedialog.askdirectory(title="Seleziona una cartella di foto")
        if not folder:
            return
        found = [
            p
            for p in Path(folder).iterdir()
            if p.is_file() and p.suffix.lower() in SOURCE_EXTENSIONS
        ]
        if not found:
            messagebox.showinfo(
                "Nessuna immagine",
                "La cartella scelta non contiene immagini supportate.",
            )
            return
        self._add_paths(found)

    def _add_paths(self, paths) -> None:
        existing = set(self.files)
        added = 0
        for p in paths:
            p = p.resolve()
            if p in existing:
                continue
            if p.suffix.lower() not in SOURCE_EXTENSIONS:
                continue
            self.files.append(p)
            existing.add(p)
            self.listbox.insert("end", str(p))
            added += 1
        if added:
            self.status_var.set(
                f"{len(self.files)} foto in lista ({added} aggiunte)."
            )

    def remove_selected(self) -> None:
        for idx in reversed(self.listbox.curselection()):
            self.listbox.delete(idx)
            del self.files[idx]
        self.status_var.set(f"{len(self.files)} foto in lista.")

    def clear_files(self) -> None:
        self.listbox.delete(0, "end")
        self.files.clear()
        self.status_var.set("Lista svuotata.")

    def start(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        if not self.files:
            messagebox.showwarning(
                "Nessuna foto", "Aggiungi almeno una foto alla lista."
            )
            return

        self._log_clear()
        self.progress.configure(maximum=len(self.files), value=0)
        self.start_btn.configure(state="disabled")
        self.status_var.set("Elaborazione in corso...")

        files_snapshot = list(self.files)
        self.worker = threading.Thread(
            target=self._run, args=(files_snapshot,), daemon=True
        )
        self.worker.start()

    def _run(self, files: list[Path]) -> None:
        by_folder: dict[Path, list[Path]] = {}
        for f in files:
            by_folder.setdefault(f.parent, []).append(f)

        for folder in by_folder:
            (folder / "web").mkdir(exist_ok=True)

        total_in = 0
        total_out = 0
        errors: list[tuple[str, str]] = []
        done = 0

        with ThreadPoolExecutor() as pool:
            futures = {
                pool.submit(process_one, f, f.parent / "web"): f for f in files
            }
            for fut in as_completed(futures):
                src = futures[fut]
                name, outs, err = fut.result()
                done += 1
                if err is not None:
                    errors.append((name, err))
                    self.msg_queue.put(
                        ("log", f"[{done}/{len(files)}] FAIL  {name}: {err}")
                    )
                else:
                    in_size = src.stat().st_size
                    out_dir = src.parent / "web"
                    out_size = sum(
                        (out_dir / o).stat().st_size for o in outs
                    )
                    total_in += in_size
                    total_out += out_size
                    self.msg_queue.put(
                        (
                            "log",
                            f"[{done}/{len(files)}] OK    {name}  "
                            f"{human_bytes(in_size)} -> {len(outs)} file, "
                            f"{human_bytes(out_size)}",
                        )
                    )
                self.msg_queue.put(("progress", done))

        self.msg_queue.put(
            (
                "done",
                {
                    "total": len(files),
                    "errors": errors,
                    "in": total_in,
                    "out": total_out,
                },
            )
        )

    def _drain_queue(self) -> None:
        try:
            while True:
                kind, payload = self.msg_queue.get_nowait()
                if kind == "log":
                    self._log_append(str(payload))
                elif kind == "progress":
                    self.progress.configure(value=payload)
                elif kind == "done":
                    self._on_done(payload)
        except queue.Empty:
            pass
        self.root.after(100, self._drain_queue)

    def _on_done(self, summary: dict) -> None:
        ok = summary["total"] - len(summary["errors"])
        self._log_append("-" * 60)
        self._log_append(
            f"Completato. {ok}/{summary['total']} foto elaborate.  "
            f"Sorgenti: {human_bytes(summary['in'])}  "
            f"Output: {human_bytes(summary['out'])}"
        )
        self.start_btn.configure(state="normal")
        if summary["errors"]:
            self.status_var.set(
                f"Fatto con {len(summary['errors'])} errore/i."
            )
            messagebox.showwarning(
                "Completato con errori",
                f"{ok}/{summary['total']} foto elaborate.\n"
                f"{len(summary['errors'])} errore/i (vedi log).",
            )
        else:
            self.status_var.set("Fatto.")
            messagebox.showinfo(
                "Completato",
                f"Tutte le {summary['total']} foto sono state ottimizzate.",
            )

    def _log_append(self, line: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _log_clear(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")


def main() -> int:
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except tk.TclError:
        pass
    PhotoOptimizerApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
