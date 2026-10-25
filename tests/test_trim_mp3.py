"""Regressione: MP3 con taglio del silenzio iniziale.

Con FFmpeg 7.1 e LAME in virgola mobile, un taglio iniziale di 4, 12, 20… campioni
(resto 4 nella divisione per 8) su un MP3 senza intestazione LAME (es. audio WhatsApp)
faceva fallire la conversione con "inadequate AVFrame plane padding".
Qui si prova il comando reale dell'app su ogni offset con resto 4, più alcuni altri.

Uso:  python tests/test_trim_mp3.py
"""
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import convertitore_audio as ca  # noqa: E402


def main():
    ff = ca.find_ffmpeg()
    if not ff:
        sys.exit("FFmpeg non trovato")
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "senza_lame.mp3")
        subprocess.run([ff, "-v", "error", "-y", "-f", "lavfi", "-i", "anoisesrc=d=2:c=pink:r=44100:a=0.3",
                        "-ac", "2", "-c:a", "libmp3lame", "-b:a", "128k", "-write_xing", "0", src], check=True)
        info = ca.probe_media(ff, src)
        dst = os.path.join(tmp, "out_%d.mp3")

        def convert(offset):
            plan = {"trim": (offset / 44100.0, None), "volume": None, "loudnorm": None}
            cmd = ca.build_command(ff, src, dst % offset, "mp3", info, False, plan)
            r = subprocess.run(cmd, capture_output=True, text=True, **ca._popen_kwargs())
            return offset, r.returncode, r.stderr.strip().splitlines()[-1:] if r.returncode else []

        offsets = list(range(4, 1152, 8)) + [1, 2, 3, 8, 100, 577, 1151]
        with ThreadPoolExecutor(4) as pool:
            failures = [r for r in pool.map(convert, offsets) if r[1]]
    print("conversioni MP3 con taglio iniziale: %d, fallite: %d" % (len(offsets), len(failures)))
    for offset, rc, last in failures[:5]:
        print("  offset %d: exit %d %s" % (offset, rc, last))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
