# -*- mode: python ; coding: utf-8 -*-
# Convertitore Audio — a cura di Massimiliano Mascioli Trippa
#
# Uso:  pyinstaller --noconfirm --clean ConvertitoreAudio.spec
#   macOS   -> dist/Convertitore Audio.app
#   Windows -> dist/Convertitore Audio.exe  (file unico)
#   Linux   -> dist/ConvertitoreAudio       (file unico)
# FFmpeg (fornito da imageio-ffmpeg) viene incluso nel pacchetto.

import os
import shutil
import sys

import imageio_ffmpeg

APP_NAME = "Convertitore Audio"
VERSION = "1.1.2"
IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform == "win32"

# copia di ffmpeg con il nome che l'app si aspetta (ffmpeg / ffmpeg.exe)
ffmpeg_dir = os.path.join(workpath, "ffmpeg_bin")
os.makedirs(ffmpeg_dir, exist_ok=True)
ffmpeg_bin = os.path.join(ffmpeg_dir, "ffmpeg.exe" if IS_WIN else "ffmpeg")
shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(), ffmpeg_bin)

a = Analysis(
    ["convertitore_audio.py"],
    binaries=[(ffmpeg_bin, "ffmpeg")],
    # icona della finestra (su macOS la fornisce il bundle)
    datas=[] if IS_MAC else [("assets/icon.ico" if IS_WIN else "assets/icon.png", "assets")],
    hiddenimports=["tkinterdnd2"],
    # imageio_ffmpeg serve solo in fase di build: ffmpeg è già incluso sopra
    excludes=["imageio_ffmpeg", "PIL", "numpy"],
)
pyz = PYZ(a.pure)

if IS_MAC:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        console=False,
        upx=False,
        argv_emulation=False,
        icon="assets/icon.icns",
    )
    coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name=APP_NAME)
    app = BUNDLE(
        coll,
        name=APP_NAME + ".app",
        icon="assets/icon.icns",
        bundle_identifier="it.maxtrip.convertitoreaudio",
        version=VERSION,
        info_plist={
            "CFBundleDisplayName": APP_NAME,
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "NSHumanReadableCopyright": "A cura di Massimiliano Mascioli Trippa",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "12.0",
            "LSApplicationCategoryType": "public.app-category.music",
            "CFBundleDocumentTypes": [
                {
                    "CFBundleTypeName": "Audio / Video",
                    "CFBundleTypeRole": "Viewer",
                    "LSHandlerRank": "Alternate",
                    "LSItemContentTypes": ["public.audio", "public.movie", "public.audiovisual-content"],
                }
            ],
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=APP_NAME if IS_WIN else "ConvertitoreAudio",
        console=False,
        upx=False,
        icon="assets/icon.ico" if IS_WIN else None,
        version="version_info.txt" if IS_WIN else None,
    )
