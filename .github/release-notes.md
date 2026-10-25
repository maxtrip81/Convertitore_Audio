**A cura di Massimiliano Mascioli Trippa**

Converte qualsiasi file audio o video in **MP3 320 kbps** o **WAV 16 bit**, 44.100 Hz stereo. Durante la conversione taglia il silenzio iniziale e finale e normalizza il volume secondo **EBU R128** (−23 LUFS, true peak −1 dBTP). Il nome del programma viene scritto nei tag del file. L'interfaccia è in italiano e in inglese, e FFmpeg è già incluso.

### Download

| Sistema | File |
|---|---|
| macOS con processore Apple (M1, M2, M3, M4…) | `ConvertitoreAudio-macOS-AppleSilicon.zip` |
| macOS con processore Intel | `ConvertitoreAudio-macOS-Intel.zip` |
| Windows 10 / 11 (64 bit) | `ConvertitoreAudio-Windows-x64.zip` |
| Linux 64 bit (Ubuntu 22.04+, Debian 12+, Fedora 36+, Mint 21+) | `ConvertitoreAudio-Linux-x64.tar.gz` |

### Primo avvio

- **macOS:** scompatta lo zip e sposta l'app in Applicazioni, poi aprila. L'app non è firmata da Apple, quindi al primo avvio macOS la blocca. Vai in **Impostazioni di Sistema → Privacy e sicurezza** e premi **Apri comunque**.
- **Windows:** scompatta lo zip e avvia `Convertitore Audio.exe`. Se compare «Windows ha protetto il PC», premi **Ulteriori informazioni → Esegui comunque**.
- **Linux:** scompatta l'archivio con `tar -xzf ConvertitoreAudio-Linux-x64.tar.gz`, poi avvia il programma con `./ConvertitoreAudio`.

---

**English:** converts any audio or video file to 320 kbps MP3 or 16-bit WAV, 44,100 Hz stereo. It trims leading and trailing silence and normalizes loudness to EBU R128 (−23 LUFS, −1 dBTP). Pick the file for your system from the table above. On macOS, the first launch needs **System Settings → Privacy & Security → Open Anyway**. On Windows, click **More info → Run anyway** if SmartScreen appears.

Utilizza [FFmpeg](https://ffmpeg.org) (licenza GPL).
