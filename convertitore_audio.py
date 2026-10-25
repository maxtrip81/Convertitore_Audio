#!/usr/bin/env python3
"""
Convertitore Audio — MP3 320 kbps / WAV, 44.100 Hz stereo
Converte qualsiasi file audio o video in MP3 (320 kbps CBR) o WAV (PCM 16 bit),
tagliando i silenzi iniziali e finali e normalizzando il volume secondo EBU R128.

A cura di Massimiliano Mascioli Trippa
"""

import json
import math
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception:  # drag & drop facoltativo
    TkinterDnD = None
    DND_FILES = None

APP_NAME = "Convertitore Audio"
APP_ID = "ConvertitoreAudio"
VERSION = "1.1.0"
AUTHOR = "Massimiliano Mascioli Trippa"
# scritto nei tag del file convertito (MP3: TENC «Codificato da», WAV: ITCH + BWF originator)
TOOL_TAG = "%s %s - a cura di %s" % (APP_NAME, VERSION, AUTHOR)

# Taglio dei silenzi: sotto questa soglia, per almeno questa durata, il segnale è silenzio
SILENCE_THRESHOLD_DB = -60
SILENCE_MIN_SECONDS = 0.1
# Normalizzazione broadcast EBU R128 (ITU-R BS.1770): -23 LUFS integrati, true peak max -1 dBTP
LOUDNESS_TARGET = -23.0
TRUE_PEAK_MAX = -1.0

# Estensioni cercate quando si aggiunge una cartella.
# I file scelti uno per uno vengono accettati qualunque sia l'estensione.
MEDIA_EXTENSIONS = {
    # audio
    "mp3", "mp2", "mp1", "wav", "wave", "w64", "rf64", "bwf", "aif", "aiff",
    "aifc", "flac", "alac", "m4a", "m4b", "m4r", "aac", "adts", "ogg", "oga",
    "opus", "spx", "wma", "wv", "ape", "mpc", "ac3", "eac3", "dts", "amr",
    "awb", "au", "snd", "caf", "mka", "tta", "dsf", "dff", "ra", "rm", "gsm",
    "voc", "mid", "xm", "mod", "s3m", "it",
    # video
    "mp4", "m4v", "mov", "qt", "avi", "mkv", "webm", "wmv", "asf", "flv",
    "f4v", "mpg", "mpeg", "mpe", "m1v", "m2v", "vob", "ts", "mts", "m2ts",
    "3gp", "3g2", "ogv", "mxf", "dv", "rmvb", "divx", "xvid", "h264", "hevc",
}

FORMATS = ("mp3", "wav")
MAX_WORKERS = max(1, min(4, (os.cpu_count() or 2) // 2))

# Colori (stessa palette di maxtrip.it)
BG = "#f3f1ec"
SURFACE = "#ebe8e1"
FIELD = "#fbfaf7"
FG = "#121212"
MUTED = "#67635c"
LINE = "#d9d5cd"
LINE_STRONG = "#bdb8ae"
ACCENT = "#cc2f12"
ACCENT_HOVER = "#a92610"
ACCENT_DISABLED = "#e3a99d"
OK_GREEN = "#2f7d32"
WHITE = "#ffffff"

STRINGS = {
    "it": {
        "subtitle": "Converte qualsiasi file audio o video in MP3 o WAV",
        "credit": "A cura di Massimiliano Mascioli Trippa",
        "add_files": "Aggiungi file…",
        "add_folder": "Aggiungi cartella…",
        "remove": "Rimuovi",
        "clear": "Svuota lista",
        "col_file": "File",
        "col_folder": "Cartella",
        "col_status": "Stato",
        "drop_hint": "Trascina qui file o cartelle audio e video\noppure usa «Aggiungi file…»",
        "drop_hint_nodnd": "Usa «Aggiungi file…» o «Aggiungi cartella…»\nper scegliere i file da convertire",
        "format": "Formato di uscita",
        "fmt_mp3": "MP3  ·  320 kbps  ·  44.100 Hz  ·  stereo",
        "fmt_wav": "WAV  ·  PCM 16 bit  ·  44.100 Hz  ·  stereo",
        "processing": "Elaborazione",
        "opt_trim": "Taglia il silenzio iniziale e finale",
        "opt_norm": "Normalizza il volume  ·  EBU R128 (−23 LUFS, −1 dBTP)",
        "dest": "Destinazione",
        "dest_same": "Stessa cartella del file originale",
        "dest_custom": "Altra cartella:",
        "browse": "Sfoglia…",
        "convert": "Converti",
        "cancel": "Annulla",
        "open_folder": "Apri cartella",
        "st_wait": "In attesa",
        "st_analyze": "Analisi… {p}%",
        "st_run": "Conversione… {p}%",
        "st_run_nopct": "Conversione…",
        "st_done": "Completato",
        "st_error": "Errore",
        "st_cancel": "Annullato",
        "err_noaudio": "nessuna traccia audio",
        "err_unreadable": "file non leggibile o formato non supportato",
        "err_damaged": "file danneggiato o non supportato",
        "err_write": "impossibile scrivere nella cartella di destinazione",
        "sum_empty": "Nessun file in lista",
        "sum_ready": "{n} file in lista",
        "sum_running": "Conversione in corso: {done} di {total}",
        "sum_done": "Fatto: {ok} convertiti",
        "sum_done_err": "Fatto: {ok} convertiti, {err} con errori — doppio clic su un errore per i dettagli",
        "sum_cancel": "Conversione annullata",
        "ffmpeg_ok": "FFmpeg {v}",
        "ffmpeg_missing": "FFmpeg non trovato",
        "err_no_ffmpeg_title": "FFmpeg non trovato",
        "err_no_ffmpeg": "Per convertire serve FFmpeg.\n\n"
                         "• Windows: copia ffmpeg.exe nella cartella del programma, "
                         "dentro una sottocartella «ffmpeg».\n"
                         "• macOS: installa FFmpeg con Homebrew (brew install ffmpeg).\n"
                         "• Linux: installa FFmpeg dal gestore pacchetti (es. sudo apt install ffmpeg).",
        "err_empty": "Aggiungi almeno un file da convertire.",
        "all_done": "Tutti i file in lista sono già stati convertiti.",
        "err_dest": "Scegli una cartella di destinazione valida.",
        "err_detail_title": "Dettagli errore",
        "confirm_quit_title": "Conversione in corso",
        "confirm_quit": "Una conversione è in corso. Vuoi interromperla e uscire?",
        "dlg_files": "Scegli i file da convertire",
        "dlg_folder": "Scegli una cartella da convertire",
        "dlg_dest": "Scegli la cartella di destinazione",
        "ft_media": "File audio e video",
        "ft_all": "Tutti i file",
        "about": "Informazioni su {app}",
        "about_text": "{app} {v}\n\n{credit}\n\nConverte audio e video in MP3 320 kbps o WAV "
                      "16 bit, 44.100 Hz stereo. Taglia il silenzio iniziale e finale e "
                      "normalizza il volume secondo EBU R128 (−23 LUFS, true peak −1 dBTP)."
                      "\n\nUtilizza FFmpeg (ffmpeg.org), distribuito con licenza GPL.",
    },
    "en": {
        "subtitle": "Converts any audio or video file to MP3 or WAV",
        "credit": "Created by Massimiliano Mascioli Trippa",
        "add_files": "Add files…",
        "add_folder": "Add folder…",
        "remove": "Remove",
        "clear": "Clear list",
        "col_file": "File",
        "col_folder": "Folder",
        "col_status": "Status",
        "drop_hint": "Drop audio and video files or folders here\nor use “Add files…”",
        "drop_hint_nodnd": "Use “Add files…” or “Add folder…”\nto choose the files to convert",
        "format": "Output format",
        "fmt_mp3": "MP3  ·  320 kbps  ·  44,100 Hz  ·  stereo",
        "fmt_wav": "WAV  ·  16-bit PCM  ·  44,100 Hz  ·  stereo",
        "processing": "Processing",
        "opt_trim": "Trim leading and trailing silence",
        "opt_norm": "Normalize loudness  ·  EBU R128 (−23 LUFS, −1 dBTP)",
        "dest": "Destination",
        "dest_same": "Same folder as the original file",
        "dest_custom": "Other folder:",
        "browse": "Browse…",
        "convert": "Convert",
        "cancel": "Cancel",
        "open_folder": "Open folder",
        "st_wait": "Waiting",
        "st_analyze": "Analyzing… {p}%",
        "st_run": "Converting… {p}%",
        "st_run_nopct": "Converting…",
        "st_done": "Done",
        "st_error": "Error",
        "st_cancel": "Cancelled",
        "err_noaudio": "no audio track",
        "err_unreadable": "unreadable file or unsupported format",
        "err_damaged": "damaged or unsupported file",
        "err_write": "cannot write to the destination folder",
        "sum_empty": "No files in the list",
        "sum_ready": "{n} files in the list",
        "sum_running": "Converting: {done} of {total}",
        "sum_done": "Done: {ok} converted",
        "sum_done_err": "Done: {ok} converted, {err} failed — double-click an error for details",
        "sum_cancel": "Conversion cancelled",
        "ffmpeg_ok": "FFmpeg {v}",
        "ffmpeg_missing": "FFmpeg not found",
        "err_no_ffmpeg_title": "FFmpeg not found",
        "err_no_ffmpeg": "FFmpeg is required to convert files.\n\n"
                         "• Windows: copy ffmpeg.exe into an “ffmpeg” subfolder "
                         "next to the program.\n"
                         "• macOS: install FFmpeg with Homebrew (brew install ffmpeg).\n"
                         "• Linux: install FFmpeg with your package manager (e.g. sudo apt install ffmpeg).",
        "err_empty": "Add at least one file to convert.",
        "all_done": "All files in the list have already been converted.",
        "err_dest": "Choose a valid destination folder.",
        "err_detail_title": "Error details",
        "confirm_quit_title": "Conversion in progress",
        "confirm_quit": "A conversion is in progress. Stop it and quit?",
        "dlg_files": "Choose the files to convert",
        "dlg_folder": "Choose a folder to convert",
        "dlg_dest": "Choose the destination folder",
        "ft_media": "Audio and video files",
        "ft_all": "All files",
        "about": "About {app}",
        "about_text": "{app} {v}\n\n{credit}\n\nConverts audio and video to 320 kbps MP3 or "
                      "16-bit WAV, 44,100 Hz stereo. Trims leading and trailing silence and "
                      "normalizes loudness to EBU R128 (−23 LUFS, true peak −1 dBTP)."
                      "\n\nPowered by FFmpeg (ffmpeg.org), distributed under the GPL license.",
    },
}

APP_TITLES = {"it": "Convertitore Audio", "en": "Audio Converter"}


# --------------------------------------------------------------------------
# FFmpeg
# --------------------------------------------------------------------------

def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(*parts):
    return os.path.join(getattr(sys, "_MEIPASS", None) or _app_dir(), *parts)


def find_ffmpeg():
    """FFmpeg incluso nel pacchetto, accanto al programma, oppure installato."""
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    candidates = []
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        candidates.append(os.path.join(bundle, "ffmpeg", exe))
    here = _app_dir()
    candidates += [os.path.join(here, "ffmpeg", exe), os.path.join(here, exe)]
    for path in candidates:
        if os.path.isfile(path):
            return path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    path = shutil.which("ffmpeg")
    if path:
        return path
    # le app macOS avviate dal Finder non ereditano il PATH della shell
    for path in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/opt/local/bin/ffmpeg"):
        if os.path.isfile(path):
            return path
    return None


def _popen_kwargs():
    kwargs = {"stdin": subprocess.DEVNULL}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kwargs


def ffmpeg_info(ffmpeg):
    """Restituisce (versione, supporto soxr)."""
    try:
        out = subprocess.run([ffmpeg, "-hide_banner", "-version"], capture_output=True,
                             text=True, encoding="utf-8", errors="replace", timeout=20,
                             **_popen_kwargs()).stdout
    except Exception:
        return None, False
    first = out.splitlines()[0] if out else ""
    m = re.match(r"ffmpeg version (\S+)", first)
    version = m.group(1) if m else "?"
    version = re.split(r"[-_+]", version.lstrip("n"))[0] or version
    return version, "--enable-libsoxr" in out


_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
_STREAM_RE = re.compile(r"Stream #0:(\d+)[^:]*:\s*(Audio|Video):\s*([A-Za-z0-9_]+)(.*)")
_SAMPLE_FMT_RE = re.compile(r"^(u8|s16|s32|s64|flt|dbl)p?\b")


def probe_media(ffmpeg, src):
    """Legge durata e tracce del file analizzando l'output di `ffmpeg -i`."""
    proc = subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-i", src],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=180, **_popen_kwargs())
    text = proc.stderr
    info = {"duration": None, "audio": None, "cover": None, "log": text}
    m = _DURATION_RE.search(text)
    if m:
        h, mnt, s = m.groups()
        seconds = int(h) * 3600 + int(mnt) * 60 + float(s)
        info["duration"] = seconds if seconds > 0 else None
    for line in text.splitlines():
        sm = _STREAM_RE.search(line)
        if not sm:
            continue
        index, kind, codec, rest = sm.groups()
        if kind == "Audio" and info["audio"] is None:
            parts = [p.strip() for p in rest.split(",")]
            rate = next((int(p.split()[0]) for p in parts if re.fullmatch(r"\d+ Hz", p)), None)
            sample_fmt = next((_SAMPLE_FMT_RE.match(p).group(1) for p in parts
                               if _SAMPLE_FMT_RE.match(p)), None)
            info["audio"] = {
                "codec": codec,
                "rate": rate,
                "mono": "mono" in parts,
                "stereo": "stereo" in parts,
                "sample_fmt": sample_fmt,
            }
        elif (kind == "Video" and info["cover"] is None and "(attached pic)" in rest
              and codec in ("mjpeg", "png")):
            info["cover"] = int(index)
    return info


def loudness_target(audio):
    # una sorgente mono duplicata sui due canali suona 3 LU più forte: la si porta a -26
    return LOUDNESS_TARGET - 3.0 if audio.get("mono") else LOUDNESS_TARGET


def analysis_command(ffmpeg, src, audio, trim, normalize):
    """Primo passaggio: trova i silenzi e misura la loudness senza scrivere nulla."""
    filters = []
    if trim:
        filters.append("silencedetect=noise=%ddB:duration=%s" % (SILENCE_THRESHOLD_DB, SILENCE_MIN_SECONDS))
    if normalize:
        # misura sul segnale già nella disposizione dei canali finale (es. 5.1 -> stereo)
        filters.append("aformat=channel_layouts=%s" % ("mono" if audio.get("mono") else "stereo"))
        filters.append("loudnorm=I=%.1f:TP=%.1f:LRA=50:print_format=json"
                       % (loudness_target(audio), TRUE_PEAK_MAX))
    return [ffmpeg, "-hide_banner", "-nostdin", "-i", src, "-map", "0:a:0", "-vn", "-sn", "-dn",
            "-af", ",".join(filters), "-f", "null", "-progress", "pipe:1", "-nostats",
            "-loglevel", "info", "-"]


_LOUDNORM_KEYS = ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")


def analysis_plan(log, total, audio, trim, normalize):
    """Dai risultati dell'analisi ricava taglio, guadagno e durata finale."""
    plan = {"trim": None, "volume": None, "loudnorm": None, "duration": total}
    if trim and total:
        starts = [float(v) for v in re.findall(r"silence_start: (-?[\d.]+)", log)]
        ends = [float(v) for v in re.findall(r"silence_end: (-?[\d.]+)", log)]
        begin, end = 0.0, None
        if starts and ends and starts[0] <= 0.05:
            begin = ends[0]                     # silenzio iniziale
        if starts and (len(ends) < len(starts) or ends[-1] >= total - 0.05):
            end = starts[-1]                    # silenzio fino alla fine del file
        length = (end if end is not None else total) - begin
        if length >= 0.5 and (begin > 0 or end is not None):  # file tutto muto: non si taglia
            plan["trim"] = (begin, end)
            plan["duration"] = length
    if normalize:
        found = dict(re.findall(r'"(%s)"\s*:\s*"([^"]*)"' % "|".join(_LOUDNORM_KEYS), log))
        try:
            m = {k: float(found[k]) for k in _LOUDNORM_KEYS}
        except (KeyError, ValueError):
            return plan
        if not all(math.isfinite(v) for v in m.values()) or m["input_i"] <= -70:
            return plan                         # silenzio: niente da normalizzare
        gain = loudness_target(audio) - m["input_i"]
        if m["input_tp"] + gain <= TRUE_PEAK_MAX:
            plan["volume"] = gain               # guadagno lineare: la dinamica resta intatta
        else:
            # il guadagno pieno supererebbe -1 dBTP: loudnorm limita i picchi (true peak)
            plan["loudnorm"] = (
                "loudnorm=I=%.1f:TP=%.1f:LRA=50:measured_I=%.2f:measured_TP=%.2f:measured_LRA=%.2f:"
                "measured_thresh=%.2f:offset=%.2f:linear=true:print_format=none"
                % (loudness_target(audio), TRUE_PEAK_MAX, m["input_i"], m["input_tp"],
                   m["input_lra"], m["input_thresh"], m["target_offset"]))
    return plan


def audio_filter(fmt, audio, soxr, plan=None):
    """Catena di filtri per ottenere 44.100 Hz stereo con la massima qualità."""
    plan = plan or {}
    chain = []
    mono = audio.get("mono")
    layout = "mono" if mono else "stereo"
    resampler = ":resampler=soxr:precision=28" if soxr else ""
    if plan.get("trim"):
        begin, end = plan["trim"]
        bounds = (["start=%.6f" % begin] if begin > 0 else []) + (["end=%.6f" % end] if end is not None else [])
        chain.append("atrim=" + ":".join(bounds))
        chain.append("asetpts=PTS-STARTPTS")
    leveled = plan.get("volume") is not None or plan.get("loudnorm")
    if leveled:
        chain.append("aformat=channel_layouts=%s" % layout)
        chain.append(plan["loudnorm"] or "volume=%.2fdB" % plan["volume"])
    if fmt == "wav":
        lossless = (not leveled and audio.get("sample_fmt") in ("u8", "s16")
                    and audio.get("rate") == 44100 and (audio.get("stereo") or mono))
        if not lossless:
            # riduzione a 16 bit con dither quando la sorgente ha più risoluzione
            chain.append("aformat=sample_fmts=fltp:channel_layouts=%s" % layout)
            chain.append("aresample=44100%s:osf=s16:dither_method=triangular" % resampler)
    elif audio.get("rate") != 44100 or plan.get("loudnorm"):
        # loudnorm lavora a 192 kHz: si torna a 44.100 Hz
        chain.append("aresample=44100%s" % resampler)
    if mono:
        # mono -> stereo: stesso segnale e stesso livello su entrambi i canali
        chain.append("pan=stereo|c0=c0|c1=c0")
    return ",".join(chain)


def build_command(ffmpeg, src, dst, fmt, info, soxr=False, plan=None):
    cmd = [ffmpeg, "-hide_banner", "-nostdin", "-y", "-i", src, "-map", "0:a:0"]
    if fmt == "mp3" and info.get("cover") is not None:
        cmd += ["-map", "0:%d" % info["cover"], "-c:v", "copy", "-disposition:v:0", "attached_pic"]
    else:
        cmd += ["-vn"]
    cmd += ["-sn", "-dn"]
    af = audio_filter(fmt, info["audio"], soxr, plan)
    if af:
        cmd += ["-af", af]
    cmd += ["-metadata", "encoded_by=" + TOOL_TAG]
    if fmt == "mp3":
        cmd += ["-c:a", "libmp3lame", "-b:a", "320k", "-ar", "44100", "-ac", "2",
                "-id3v2_version", "3", "-f", "mp3"]
    else:
        cmd += ["-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2", "-rf64", "auto",
                "-write_bext", "1", "-metadata", "originator=" + APP_NAME, "-f", "wav"]
    cmd += ["-progress", "pipe:1", "-nostats", "-loglevel", "error", dst]
    return cmd


_LOG_PREFIX_RE = re.compile(r"^(\[[^\]]*\]\s*)+")


def _parse_time(value):
    try:
        h, m, s = value.split(":")
        t = int(h) * 3600 + int(m) * 60 + float(s)
        return t if t >= 0 else None
    except ValueError:
        return None


class Cancelled(Exception):
    pass


class ConversionError(Exception):
    pass


def run_ffmpeg(cmd, duration, on_progress, cancel_event, register, bytes_per_sec=None,
               keep_log=False):
    """Esegue ffmpeg riportando la percentuale; solleva Cancelled o ConversionError.
    Restituisce (log, secondi elaborati); il log completo solo con keep_log."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            encoding="utf-8", errors="replace", bufsize=1, **_popen_kwargs())
    register(proc, True)
    errors = deque(maxlen=12)
    log = []

    def drain():
        for line in proc.stderr:
            line = _LOG_PREFIX_RE.sub("", line.strip())
            if not line:
                continue
            if keep_log:
                log.append(line)
            if not errors or errors[-1] != line:
                errors.append(line)

    t = threading.Thread(target=drain, daemon=True)
    t.start()
    last = -1
    processed = None
    block = {}
    try:
        for line in proc.stdout:
            if cancel_event.is_set():
                break
            key, _, value = line.strip().partition("=")
            block[key] = value
            if key != "progress":
                continue
            seconds = _parse_time(block.get("out_time", ""))
            if seconds is None and bytes_per_sec:
                # con la copertina ffmpeg non riporta out_time: stima dai byte scritti
                try:
                    seconds = int(block.get("total_size", "")) / bytes_per_sec
                except ValueError:
                    pass
            block = {}
            if seconds is not None:
                processed = seconds
            if seconds is not None and duration:
                pct = min(99, int(seconds * 100 / duration))
                if pct != last:
                    last = pct
                    on_progress(pct)
        if cancel_event.is_set():
            proc.kill()
        proc.wait()
        t.join(timeout=5)
    finally:
        register(proc, False)
    if cancel_event.is_set():
        raise Cancelled()
    if proc.returncode != 0:
        raise ConversionError("\n".join(errors) or "ffmpeg exit code %s" % proc.returncode)
    return "\n".join(log), processed


# --------------------------------------------------------------------------
# Configurazione
# --------------------------------------------------------------------------

def config_path():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, APP_ID, "config.json")


def load_config():
    try:
        with open(config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_config(data):
    try:
        path = config_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def is_hidden(name):
    return name.startswith(".")


def short_path(path):
    home = os.path.expanduser("~")
    if path == home or path.startswith(home + os.sep):
        return "~" + path[len(home):]
    return path


def open_in_file_manager(path):
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


# --------------------------------------------------------------------------
# Interfaccia
# --------------------------------------------------------------------------

class App:
    def __init__(self, root, dnd_enabled):
        self.root = root
        self.dnd_enabled = dnd_enabled
        self.config = load_config()
        self.lang = self.config.get("lang") if self.config.get("lang") in STRINGS else "it"

        self.ffmpeg = find_ffmpeg()
        self.ffmpeg_version, self.soxr = ffmpeg_info(self.ffmpeg) if self.ffmpeg else (None, False)
        if self.ffmpeg and not self.ffmpeg_version:
            self.ffmpeg = None

        self.items = {}            # iid -> dati del file
        self.known_paths = set()   # per evitare doppioni
        self.batch = []
        self.running = False
        self.cancel_event = threading.Event()
        self.q = queue.Queue()
        self.lock = threading.Lock()
        self.reserved = set()
        self.procs = set()
        self.active_outputs = set()
        self.last_output_dir = None
        self._summary = ("sum_empty", {})
        self._translatable = []

        self.var_fmt = tk.StringVar(value=self.config.get("format") if self.config.get("format") in FORMATS else "mp3")
        self.var_dest_mode = tk.StringVar(value="custom" if self.config.get("dest_mode") == "custom" else "same")
        self.var_dest = tk.StringVar(value=self.config.get("dest_dir") or "")
        self.var_trim = tk.BooleanVar(value=bool(self.config.get("trim", True)))
        self.var_norm = tk.BooleanVar(value=bool(self.config.get("normalize", True)))

        self._setup_style()
        self._build_ui()
        self._build_menu()
        self.retranslate()
        self._update_dest_state()
        self._refresh_list_state()

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        if sys.platform == "darwin":
            root.createcommand("::tk::mac::Quit", self.on_close)
            root.createcommand("::tk::mac::OpenDocument", lambda *paths: self.add_paths(paths))
        root.after(100, self._poll)

        if not self.ffmpeg:
            root.after(300, lambda: messagebox.showerror(self.t("err_no_ffmpeg_title"),
                                                         self.t("err_no_ffmpeg"), parent=root))

    # --- testi -------------------------------------------------------------

    def t(self, key, **kw):
        text = STRINGS[self.lang].get(key, STRINGS["it"].get(key, key))
        return text.format(**kw) if kw else text

    def tr(self, widget, key, option="text"):
        self._translatable.append((widget, key, option))
        return widget

    def set_lang(self, lang):
        if lang == self.lang:
            return
        self.lang = lang
        self.config["lang"] = lang
        save_config(self.config)
        self.retranslate()

    def retranslate(self):
        self.root.title("%s — MP3 320 / WAV" % APP_TITLES[self.lang])
        self.lbl_title.configure(text=APP_TITLES[self.lang])
        for widget, key, option in self._translatable:
            widget.configure(**{option: self.t(key)})
        for col, key in (("file", "col_file"), ("folder", "col_folder"), ("status", "col_status")):
            self.tree.heading(col, text=self.t(key))
        self.lbl_drop.configure(text=self.t("drop_hint" if self.dnd_enabled else "drop_hint_nodnd"))
        self.btn_it.configure(style="SegOn.TButton" if self.lang == "it" else "Seg.TButton")
        self.btn_en.configure(style="SegOn.TButton" if self.lang == "en" else "Seg.TButton")
        if self.ffmpeg:
            self.lbl_ffmpeg.configure(text=self.t("ffmpeg_ok", v=self.ffmpeg_version), foreground=MUTED)
        else:
            self.lbl_ffmpeg.configure(text=self.t("ffmpeg_missing"), foreground=ACCENT)
        for iid in self.items:
            self._render(iid)
        self._set_summary(*self._summary)
        self._build_menu()

    # --- stile -------------------------------------------------------------

    def _setup_style(self):
        base = tkfont.nametofont("TkDefaultFont")
        family = base.actual("family")
        size = abs(base.actual("size")) or 12
        if sys.platform != "darwin":
            size = max(size, 10)
        self.f_base = tkfont.Font(family=family, size=size)
        self.f_bold = tkfont.Font(family=family, size=size, weight="bold")
        self.f_small = tkfont.Font(family=family, size=max(size - 2, 8))
        self.f_head = tkfont.Font(family=family, size=max(size - 1, 8), weight="bold")
        self.f_title = tkfont.Font(family=family, size=size + 10, weight="bold")

        self.root.configure(background=BG)
        st = ttk.Style(self.root)
        st.theme_use("clam")
        st.configure(".", background=BG, foreground=FG, font=self.f_base, bordercolor=LINE,
                     lightcolor=BG, darkcolor=BG, troughcolor=SURFACE, focuscolor=BG,
                     selectbackground="#f2d3cb", selectforeground=FG)
        st.configure("TFrame", background=BG)
        st.configure("TLabel", background=BG, foreground=FG)
        st.configure("Muted.TLabel", foreground=MUTED)
        st.configure("Small.TLabel", foreground=MUTED, font=self.f_small)
        st.configure("Section.TLabel", font=self.f_bold)
        st.configure("Title.TLabel", font=self.f_title)
        st.configure("Drop.TLabel", background=FIELD, foreground=MUTED, justify="center")

        st.configure("TButton", background=SURFACE, foreground=FG, bordercolor=LINE_STRONG,
                     lightcolor=SURFACE, darkcolor=SURFACE, padding=(14, 6), relief="flat",
                     focusthickness=0)
        st.map("TButton",
               background=[("disabled", BG), ("pressed", "#d9d5cc"), ("active", "#e2ded6")],
               lightcolor=[("pressed", "#d9d5cc"), ("active", "#e2ded6")],
               darkcolor=[("pressed", "#d9d5cc"), ("active", "#e2ded6")],
               foreground=[("disabled", "#a7a29a")],
               bordercolor=[("disabled", LINE)])
        st.configure("Accent.TButton", background=ACCENT, foreground=WHITE, bordercolor=ACCENT,
                     lightcolor=ACCENT, darkcolor=ACCENT, font=self.f_bold, padding=(26, 8))
        st.map("Accent.TButton",
               background=[("disabled", ACCENT_DISABLED), ("pressed", ACCENT_HOVER), ("active", ACCENT_HOVER)],
               lightcolor=[("disabled", ACCENT_DISABLED), ("pressed", ACCENT_HOVER), ("active", ACCENT_HOVER)],
               darkcolor=[("disabled", ACCENT_DISABLED), ("pressed", ACCENT_HOVER), ("active", ACCENT_HOVER)],
               bordercolor=[("disabled", ACCENT_DISABLED), ("pressed", ACCENT_HOVER), ("active", ACCENT_HOVER)],
               foreground=[("disabled", WHITE)])
        for name, bg, fg in (("Seg.TButton", BG, MUTED), ("SegOn.TButton", FG, WHITE)):
            st.configure(name, background=bg, foreground=fg, bordercolor=LINE_STRONG if bg == BG else FG,
                         lightcolor=bg, darkcolor=bg, padding=(9, 3), font=self.f_head)
            st.map(name, background=[("active", "#e2ded6" if bg == BG else "#2a2a2a")],
                   lightcolor=[("active", "#e2ded6" if bg == BG else "#2a2a2a")],
                   darkcolor=[("active", "#e2ded6" if bg == BG else "#2a2a2a")])

        st.configure("TRadiobutton", background=BG, foreground=FG, indicatorbackground=WHITE,
                     indicatorforeground=ACCENT, indicatormargin=(0, 0, 8, 0), padding=(0, 3),
                     upperbordercolor=LINE_STRONG, lowerbordercolor=LINE_STRONG)
        st.map("TRadiobutton",
               background=[("active", BG)],
               indicatorbackground=[("disabled", BG), ("pressed", SURFACE)],
               foreground=[("disabled", "#a7a29a")])
        st.configure("TCheckbutton", background=BG, foreground=FG, indicatorbackground=WHITE,
                     indicatorforeground=ACCENT, indicatormargin=(0, 0, 8, 0), padding=(0, 3),
                     upperbordercolor=LINE_STRONG, lowerbordercolor=LINE_STRONG)
        st.map("TCheckbutton",
               background=[("active", BG)],
               indicatorbackground=[("disabled", BG), ("pressed", SURFACE)],
               foreground=[("disabled", "#a7a29a")])

        st.configure("TEntry", fieldbackground=FIELD, foreground=FG, bordercolor=LINE_STRONG,
                     lightcolor=FIELD, darkcolor=FIELD, insertcolor=FG, padding=(6, 4))
        st.map("TEntry", fieldbackground=[("disabled", BG), ("readonly", FIELD)],
               foreground=[("disabled", "#a7a29a")], bordercolor=[("focus", MUTED)])

        rowheight = self.f_base.metrics("linespace") + 12
        st.configure("Treeview", background=FIELD, fieldbackground=FIELD, foreground=FG,
                     bordercolor=LINE, lightcolor=FIELD, darkcolor=FIELD, rowheight=rowheight,
                     borderwidth=1, relief="solid")
        st.map("Treeview", background=[("selected", "#f2d3cb")], foreground=[("selected", FG)])
        st.configure("Treeview.Heading", background=SURFACE, foreground=MUTED, font=self.f_head,
                     bordercolor=LINE, lightcolor=SURFACE, darkcolor=SURFACE, relief="flat",
                     padding=(8, 5))
        st.map("Treeview.Heading", background=[("active", "#e2ded6")])

        st.configure("Vertical.TScrollbar", background=SURFACE, troughcolor=FIELD, bordercolor=FIELD,
                     lightcolor=SURFACE, darkcolor=SURFACE, arrowcolor=MUTED, gripcount=0)
        st.map("Vertical.TScrollbar", background=[("active", "#dcd8cf")])

        st.configure("Horizontal.TProgressbar", background=ACCENT, troughcolor=SURFACE,
                     bordercolor=SURFACE, lightcolor=ACCENT, darkcolor=ACCENT, thickness=8)
        st.configure("Line.TFrame", background=LINE)

    # --- costruzione finestra ----------------------------------------------

    def _build_ui(self):
        root = self.root
        root.geometry("900x700")
        root.minsize(760, 600)

        outer = ttk.Frame(root, padding=(22, 18, 22, 12))
        outer.pack(fill="both", expand=True)

        # intestazione
        header = ttk.Frame(outer)
        header.pack(fill="x")
        titles = ttk.Frame(header)
        titles.pack(side="left", fill="x", expand=True)
        self.lbl_title = ttk.Label(titles, style="Title.TLabel")
        self.lbl_title.pack(anchor="w")
        self.tr(ttk.Label(titles, style="Muted.TLabel"), "subtitle").pack(anchor="w", pady=(2, 0))
        langbox = ttk.Frame(header)
        langbox.pack(side="right", anchor="ne")
        self.btn_it = ttk.Button(langbox, text="IT", width=3, takefocus=False,
                                 command=lambda: self.set_lang("it"))
        self.btn_en = ttk.Button(langbox, text="EN", width=3, takefocus=False,
                                 command=lambda: self.set_lang("en"))
        self.btn_it.pack(side="left")
        self.btn_en.pack(side="left", padx=(4, 0))

        # barra comandi della lista
        toolbar = ttk.Frame(outer)
        toolbar.pack(fill="x", pady=(16, 8))
        self.btn_add_files = self.tr(ttk.Button(toolbar, command=self.ask_files), "add_files")
        self.btn_add_files.pack(side="left")
        self.btn_add_folder = self.tr(ttk.Button(toolbar, command=self.ask_folder), "add_folder")
        self.btn_add_folder.pack(side="left", padx=(8, 0))
        self.btn_clear = self.tr(ttk.Button(toolbar, command=self.clear_list), "clear")
        self.btn_clear.pack(side="right")
        self.btn_remove = self.tr(ttk.Button(toolbar, command=self.remove_selected), "remove")
        self.btn_remove.pack(side="right", padx=(0, 8))

        # lista dei file
        listframe = ttk.Frame(outer)
        self.tree = ttk.Treeview(listframe, columns=("file", "folder", "status"), show="headings",
                                 selectmode="extended", height=5)
        self.tree.column("file", width=280, minwidth=140, stretch=True)
        self.tree.column("folder", width=300, minwidth=120, stretch=True)
        self.tree.column("status", width=190, minwidth=150, stretch=False)
        for col in ("file", "folder", "status"):
            self.tree.heading(col, anchor="w")
        self.tree.tag_configure("done", foreground=OK_GREEN)
        self.tree.tag_configure("error", foreground=ACCENT)
        self.tree.tag_configure("cancel", foreground=MUTED)
        self.tree.tag_configure("run", foreground=FG)
        self.tree.tag_configure("analyze", foreground=FG)
        vsb = ttk.Scrollbar(listframe, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.lbl_drop = ttk.Label(listframe, style="Drop.TLabel", anchor="center")
        self.tree.bind("<Double-1>", self._show_error_detail)
        self.tree.bind("<Delete>", lambda e: self.remove_selected())
        self.tree.bind("<BackSpace>", lambda e: self.remove_selected())
        self.lbl_drop.bind("<Button-1>", lambda e: self.ask_files() if not self.running else None)

        # parte inferiore: impacchettata prima della lista, così è la lista a ridursi
        bottom = ttk.Frame(outer)
        bottom.pack(side="bottom", fill="x")
        listframe.pack(fill="both", expand=True)

        # opzioni
        options = ttk.Frame(bottom)
        options.pack(fill="x", pady=(16, 0))
        options.columnconfigure(0, weight=1, uniform="opt")
        options.columnconfigure(1, weight=1, uniform="opt")

        fmt = ttk.Frame(options)
        fmt.grid(row=0, column=0, sticky="nw", padx=(0, 16))
        self.tr(ttk.Label(fmt, style="Section.TLabel"), "format").pack(anchor="w", pady=(0, 4))
        self.rb_mp3 = self.tr(ttk.Radiobutton(fmt, variable=self.var_fmt, value="mp3",
                                              command=self._save_options), "fmt_mp3")
        self.rb_mp3.pack(anchor="w")
        self.rb_wav = self.tr(ttk.Radiobutton(fmt, variable=self.var_fmt, value="wav",
                                              command=self._save_options), "fmt_wav")
        self.rb_wav.pack(anchor="w")

        dest = ttk.Frame(options)
        dest.grid(row=0, column=1, sticky="new")
        self.tr(ttk.Label(dest, style="Section.TLabel"), "dest").pack(anchor="w", pady=(0, 4))
        self.rb_same = self.tr(ttk.Radiobutton(dest, variable=self.var_dest_mode, value="same",
                                               command=self._on_dest_mode), "dest_same")
        self.rb_same.pack(anchor="w")
        row = ttk.Frame(dest)
        row.pack(fill="x")
        self.rb_custom = self.tr(ttk.Radiobutton(row, variable=self.var_dest_mode, value="custom",
                                                 command=self._on_dest_mode), "dest_custom")
        self.rb_custom.pack(side="left")
        self.btn_browse = self.tr(ttk.Button(row, command=self.ask_dest, padding=(10, 3)), "browse")
        self.btn_browse.pack(side="right")
        self.ent_dest = ttk.Entry(row, textvariable=self.var_dest)
        self.ent_dest.pack(side="left", fill="x", expand=True, padx=(8, 8))
        self.ent_dest.bind("<FocusOut>", lambda e: self._save_options())

        proc = ttk.Frame(options)
        proc.grid(row=1, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self.tr(ttk.Label(proc, style="Section.TLabel"), "processing").pack(anchor="w", pady=(0, 4))
        checks = ttk.Frame(proc)
        checks.pack(anchor="w")
        self.cb_trim = self.tr(ttk.Checkbutton(checks, variable=self.var_trim,
                                               command=self._save_options), "opt_trim")
        self.cb_trim.pack(side="left", padx=(0, 24))
        self.cb_norm = self.tr(ttk.Checkbutton(checks, variable=self.var_norm,
                                               command=self._save_options), "opt_norm")
        self.cb_norm.pack(side="left")

        # avanzamento e azioni
        self.pb = ttk.Progressbar(bottom, mode="determinate", maximum=1000)
        self.pb.pack(fill="x", pady=(18, 6))
        actions = ttk.Frame(bottom)
        actions.pack(fill="x")
        self.lbl_summary = ttk.Label(actions, style="Muted.TLabel")
        self.lbl_summary.pack(side="left", fill="x", expand=True)
        self.btn_convert = self.tr(ttk.Button(actions, style="Accent.TButton", command=self.start), "convert")
        self.btn_convert.pack(side="right")
        self.btn_cancel = self.tr(ttk.Button(actions, command=self.cancel), "cancel")
        self.btn_cancel.pack(side="right", padx=(0, 8))
        self.btn_open = self.tr(ttk.Button(actions, command=self.open_output), "open_folder")
        self.btn_open.pack(side="right", padx=(0, 8))
        self.btn_cancel.state(["disabled"])
        self.btn_open.state(["disabled"])

        # piè di pagina
        ttk.Frame(bottom, style="Line.TFrame", height=1).pack(fill="x", pady=(14, 8))
        footer = ttk.Frame(bottom)
        footer.pack(fill="x")
        self.tr(ttk.Label(footer, style="Small.TLabel"), "credit").pack(side="left")
        self.lbl_ffmpeg = ttk.Label(footer, style="Small.TLabel")
        self.lbl_ffmpeg.pack(side="right")
        ttk.Label(footer, text="v%s  ·  " % VERSION, style="Small.TLabel").pack(side="right")

        if self.dnd_enabled:
            root.drop_target_register(DND_FILES)
            root.dnd_bind("<<Drop>>", self._on_drop)

        mod = "Command" if sys.platform == "darwin" else "Control"
        root.bind("<%s-o>" % mod, lambda e: self.ask_files())

    def _build_menu(self):
        if sys.platform != "darwin":
            return
        menubar = tk.Menu(self.root)
        appmenu = tk.Menu(menubar, name="apple", tearoff=False)
        appmenu.add_command(label=self.t("about", app=APP_TITLES[self.lang]), command=self.show_about)
        menubar.add_cascade(menu=appmenu)
        self.root.configure(menu=menubar)

    def show_about(self):
        messagebox.showinfo(self.t("about", app=APP_TITLES[self.lang]),
                            self.t("about_text", app=APP_TITLES[self.lang], v=VERSION,
                                   credit=self.t("credit")), parent=self.root)

    # --- gestione lista ----------------------------------------------------

    def ask_files(self):
        if self.running:
            return
        exts = " ".join("*.%s" % e for e in sorted(MEDIA_EXTENSIONS))
        paths = filedialog.askopenfilenames(parent=self.root, title=self.t("dlg_files"),
                                            filetypes=[(self.t("ft_media"), exts),
                                                       (self.t("ft_all"), "*")])
        if paths:
            self.add_paths(self.root.tk.splitlist(paths) if isinstance(paths, str) else paths)

    def ask_folder(self):
        if self.running:
            return
        path = filedialog.askdirectory(parent=self.root, title=self.t("dlg_folder"), mustexist=True)
        if path:
            self.add_paths([path])

    def ask_dest(self):
        start = self.var_dest.get() if os.path.isdir(self.var_dest.get()) else os.path.expanduser("~")
        path = filedialog.askdirectory(parent=self.root, title=self.t("dlg_dest"), initialdir=start)
        if path:
            self.var_dest.set(os.path.normpath(path))
            self.var_dest_mode.set("custom")
            self._on_dest_mode()

    def _on_drop(self, event):
        if not self.running:
            self.add_paths(self.root.tk.splitlist(event.data))
        return event.action

    def add_paths(self, paths):
        if self.running:
            return
        files = []
        for p in paths:
            p = os.path.normpath(str(p))
            if os.path.isdir(p):
                for folder, dirs, names in os.walk(p):
                    dirs[:] = sorted(d for d in dirs if not is_hidden(d))
                    for name in sorted(names, key=str.lower):
                        ext = os.path.splitext(name)[1][1:].lower()
                        if not is_hidden(name) and ext in MEDIA_EXTENSIONS:
                            files.append(os.path.join(folder, name))
            elif os.path.isfile(p) and not is_hidden(os.path.basename(p)):
                files.append(p)
        for f in files:
            key = os.path.normcase(os.path.abspath(f))
            if key in self.known_paths:
                continue
            self.known_paths.add(key)
            iid = self.tree.insert("", "end")
            self.items[iid] = {"src": f, "key": key, "state": "wait", "pct": None, "error": ""}
            self._render(iid)
        self._refresh_list_state()

    def remove_selected(self):
        if self.running:
            return
        for iid in self.tree.selection():
            item = self.items.pop(iid, None)
            if item:
                self.known_paths.discard(item["key"])
            self.tree.delete(iid)
        self._refresh_list_state()

    def clear_list(self):
        if self.running:
            return
        self.tree.delete(*self.tree.get_children())
        self.items.clear()
        self.known_paths.clear()
        self.pb["value"] = 0
        self._refresh_list_state()

    def _refresh_list_state(self):
        if self.items:
            self.lbl_drop.place_forget()
        else:
            self.lbl_drop.place(in_=self.tree, relx=0.5, rely=0.55, anchor="center")
        if not self.running:
            n = len(self.items)
            self._set_summary("sum_ready" if n else "sum_empty", {"n": n})

    def _status_text(self, item):
        state = item["state"]
        if state == "analyze":
            return self.t("st_analyze", p=item["pct"] or 0)
        if state == "run":
            return self.t("st_run", p=item["pct"]) if item["pct"] is not None else self.t("st_run_nopct")
        if state == "error":
            first = item["error"].splitlines()[0] if item["error"] else ""
            return "%s: %s" % (self.t("st_error"), first) if first else self.t("st_error")
        return self.t({"wait": "st_wait", "done": "st_done", "cancel": "st_cancel"}[state])

    def _render(self, iid):
        item = self.items[iid]
        src = item["src"]
        self.tree.item(iid, values=(os.path.basename(src), short_path(os.path.dirname(src)),
                                    self._status_text(item)), tags=(item["state"],))

    def _show_error_detail(self, event):
        iid = self.tree.identify_row(event.y)
        item = self.items.get(iid)
        if item and item["state"] == "error":
            messagebox.showerror(self.t("err_detail_title"),
                                 "%s\n\n%s" % (os.path.basename(item["src"]), item["error"]),
                                 parent=self.root)

    def _set_summary(self, key, kw):
        self._summary = (key, kw)
        self.lbl_summary.configure(text=self.t(key, **kw))

    # --- opzioni -----------------------------------------------------------

    def _on_dest_mode(self):
        self._update_dest_state()
        self._save_options()
        if self.var_dest_mode.get() == "custom" and not self.var_dest.get():
            self.ask_dest()

    def _update_dest_state(self):
        custom = self.var_dest_mode.get() == "custom" and not self.running
        self.ent_dest.state(["!disabled"] if custom else ["disabled"])

    def _save_options(self):
        self.config.update({"format": self.var_fmt.get(), "dest_mode": self.var_dest_mode.get(),
                            "dest_dir": self.var_dest.get().strip(), "lang": self.lang,
                            "trim": self.var_trim.get(), "normalize": self.var_norm.get()})
        save_config(self.config)

    def open_output(self):
        if self.last_output_dir and os.path.isdir(self.last_output_dir):
            open_in_file_manager(self.last_output_dir)

    # --- conversione -------------------------------------------------------

    def _set_running(self, running):
        self.running = running
        normal = ["disabled"] if running else ["!disabled"]
        for w in (self.btn_add_files, self.btn_add_folder, self.btn_remove, self.btn_clear,
                  self.btn_convert, self.rb_mp3, self.rb_wav, self.rb_same, self.rb_custom,
                  self.btn_browse, self.cb_trim, self.cb_norm):
            w.state(normal)
        self.btn_cancel.state(["!disabled"] if running else ["disabled"])
        self._update_dest_state()

    def start(self):
        if self.running:
            return
        if not self.ffmpeg:
            messagebox.showerror(self.t("err_no_ffmpeg_title"), self.t("err_no_ffmpeg"), parent=self.root)
            return
        if not self.items:
            messagebox.showinfo(APP_TITLES[self.lang], self.t("err_empty"), parent=self.root)
            return
        batch = [iid for iid in self.tree.get_children() if self.items[iid]["state"] != "done"]
        if not batch:
            messagebox.showinfo(APP_TITLES[self.lang], self.t("all_done"), parent=self.root)
            return
        dest = None
        if self.var_dest_mode.get() == "custom":
            dest = self.var_dest.get().strip()
            try:
                if not dest:
                    raise OSError
                os.makedirs(dest, exist_ok=True)
            except OSError:
                messagebox.showerror(APP_TITLES[self.lang], self.t("err_dest"), parent=self.root)
                return
        self._save_options()

        for iid in batch:
            self.items[iid].update(state="wait", pct=None, error="")
            self._render(iid)
        self.batch = batch
        self.reserved.clear()
        self.cancel_event.clear()
        self.last_output_dir = dest
        self.btn_open.state(["disabled"])
        self._set_running(True)
        self._set_summary("sum_running", {"done": 0, "total": len(batch)})
        jobs = [(iid, self.items[iid]["src"]) for iid in batch]
        settings = {"fmt": self.var_fmt.get(), "dest": dest,
                    "trim": self.var_trim.get(), "normalize": self.var_norm.get()}
        threading.Thread(target=self._run_batch, args=(jobs, settings), daemon=True).start()

    def cancel(self):
        if not self.running:
            return
        self.cancel_event.set()
        self._kill_all()

    def _kill_all(self):
        with self.lock:
            procs = list(self.procs)
        for p in procs:
            try:
                p.kill()
            except Exception:
                pass

    def _register_proc(self, proc, add):
        with self.lock:
            (self.procs.add if add else self.procs.discard)(proc)

    def _run_batch(self, jobs, settings):
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            for iid, src in jobs:
                pool.submit(self._convert_one, iid, src, settings)
        self.q.put(("finished",))

    def _reserve_output(self, src, settings):
        folder = settings["dest"] or os.path.dirname(src)
        base = os.path.splitext(os.path.basename(src))[0]
        ext = settings["fmt"]
        with self.lock:
            n = 0
            while True:
                name = "%s.%s" % (base, ext) if n == 0 else "%s (%d).%s" % (base, n, ext)
                path = os.path.join(folder, name)
                key = os.path.normcase(path).lower()
                if key not in self.reserved and not os.path.exists(path):
                    self.reserved.add(key)
                    return path
                n += 1

    def _convert_one(self, iid, src, settings):
        if self.cancel_event.is_set():
            self.q.put(("item", iid, "cancel", None, ""))
            return
        self.q.put(("item", iid, "run", None, ""))
        out = None
        try:
            info = probe_media(self.ffmpeg, src)
            if info["audio"] is None:
                if info["duration"] is None and "Stream #" not in info["log"]:
                    lines = [l.strip() for l in info["log"].splitlines() if l.strip()]
                    detail = lines[-1] if lines else ""
                    raise ConversionError("%s\n\n%s" % (self.t("err_unreadable"), detail))
                raise ConversionError(self.t("err_noaudio"))
            if self.cancel_event.is_set():
                raise Cancelled()
            # 1° passaggio (solo se serve): silenzi e loudness, pari al 40% dell'avanzamento
            plan, duration, base, span = None, info["duration"], 0, 100
            if settings["trim"] or settings["normalize"]:
                self.q.put(("item", iid, "analyze", 0, ""))
                log, total = self._run(
                    analysis_command(self.ffmpeg, src, info["audio"], settings["trim"], settings["normalize"]),
                    info["duration"], lambda pct: self.q.put(("item", iid, "analyze", pct * 40 // 100, "")),
                    keep_log=True)
                plan = analysis_plan(log, total or info["duration"], info["audio"],
                                     settings["trim"], settings["normalize"])
                duration, base, span = plan["duration"], 40, 60
            # 2° passaggio: conversione
            out = self._reserve_output(src, settings)
            cmd = build_command(self.ffmpeg, src, out, settings["fmt"], info, self.soxr, plan)
            with self.lock:
                self.active_outputs.add(out)
            self._run(cmd, duration, lambda pct: self.q.put(("item", iid, "run", base + pct * span // 100, "")),
                      bytes_per_sec=40000 if settings["fmt"] == "mp3" else 176400)
            with self.lock:
                self.active_outputs.discard(out)
            self.q.put(("item", iid, "done", 100, out))
        except Cancelled:
            self._discard(out)
            self.q.put(("item", iid, "cancel", None, ""))
        except Exception as exc:
            self._discard(out)
            if self.cancel_event.is_set():
                self.q.put(("item", iid, "cancel", None, ""))
            else:
                self.q.put(("item", iid, "error", None, str(exc).strip() or exc.__class__.__name__))

    def _run(self, cmd, duration, on_progress, **kw):
        try:
            return run_ffmpeg(cmd, duration, on_progress, self.cancel_event, self._register_proc, **kw)
        except ConversionError as exc:
            raise ConversionError(self._friendly_error(str(exc)))

    def _friendly_error(self, details):
        if "Permission denied" in details or "Read-only file system" in details:
            summary = self.t("err_write")
        elif re.search(r"Invalid data|Decode error|Error while decoding|could not find codec", details, re.I):
            summary = self.t("err_damaged")
        else:
            return details
        return "%s\n\n%s" % (summary, details)

    def _discard(self, path):
        if not path:
            return
        with self.lock:
            self.active_outputs.discard(path)
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

    def _poll(self):
        try:
            while True:
                msg = self.q.get_nowait()
                if msg[0] == "item":
                    _, iid, state, pct, extra = msg
                    item = self.items.get(iid)
                    if item is None:
                        continue
                    item["state"], item["pct"] = state, pct
                    if state == "error":
                        item["error"] = extra
                    elif state == "done":
                        item["out"] = extra
                        if not self.last_output_dir or self.var_dest_mode.get() == "same":
                            self.last_output_dir = os.path.dirname(extra)
                    self._render(iid)
                elif msg[0] == "finished":
                    self._on_finished()
        except queue.Empty:
            pass
        if self.running:
            self._update_progress()
        self.root.after(100, self._poll)

    def _update_progress(self):
        if not self.batch:
            return
        total, finished, frac = len(self.batch), 0, 0.0
        for iid in self.batch:
            item = self.items.get(iid)
            if item is None:
                continue
            if item["state"] in ("done", "error", "cancel"):
                finished += 1
                frac += 1
            elif item["state"] in ("analyze", "run") and item["pct"]:
                frac += item["pct"] / 100.0
        self.pb["value"] = int(frac * 1000 / total)
        self._set_summary("sum_running", {"done": finished, "total": total})

    def _on_finished(self):
        self._set_running(False)
        states = [self.items[i]["state"] for i in self.batch if i in self.items]
        ok, err = states.count("done"), states.count("error")
        self.pb["value"] = 1000 if not self.cancel_event.is_set() else self.pb["value"]
        if self.cancel_event.is_set():
            self._set_summary("sum_cancel", {})
        elif err:
            self._set_summary("sum_done_err", {"ok": ok, "err": err})
        else:
            self._set_summary("sum_done", {"ok": ok})
        if ok and self.last_output_dir:
            self.btn_open.state(["!disabled"])
        if not self.cancel_event.is_set():
            self.root.bell()

    def on_close(self):
        if self.running:
            if not messagebox.askyesno(self.t("confirm_quit_title"), self.t("confirm_quit"),
                                       parent=self.root):
                return
            self.cancel_event.set()
            self._kill_all()
            with self.lock:
                procs, outputs = list(self.procs), list(self.active_outputs)
            for p in procs:
                try:
                    p.wait(timeout=3)
                except Exception:
                    pass
            for path in outputs:
                self._discard(path)
        self._save_options()
        self.root.destroy()


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    root, dnd = None, False
    if TkinterDnD is not None:
        try:
            root = TkinterDnD.Tk()
            dnd = True
        except Exception:
            root = None
    if root is None:
        root = tk.Tk()
    try:
        if sys.platform == "win32":
            root.iconbitmap(default=resource_path("assets", "icon.ico"))
        elif sys.platform.startswith("linux"):
            root.iconphoto(True, tk.PhotoImage(file=resource_path("assets", "icon.png")))
    except Exception:
        pass
    app = App(root, dnd)
    initial = [a for a in sys.argv[1:] if os.path.exists(a)]
    if initial:
        app.add_paths(initial)
    root.mainloop()


if __name__ == "__main__":
    main()
