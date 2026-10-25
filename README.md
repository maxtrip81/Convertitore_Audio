# Convertitore Audio — MP3 320 / WAV

**A cura di Massimiliano Mascioli Trippa** · versione 1.1.0 · macOS, Windows e Linux

**[⬇ Scarica l'ultima versione](../../releases/latest)**

Converte qualsiasi file audio o video in:

- **MP3** · 320 kbps CBR · 44.100 Hz · stereo
- **WAV** · PCM 16 bit · 44.100 Hz · stereo

Durante la conversione, entrambe attive di serie:

- **taglia il silenzio iniziale e finale** in eccesso;
- **normalizza il volume secondo EBU R128**, lo standard broadcast radiotelevisivo europeo adottato anche in Italia: −23 LUFS integrati e true peak massimo −1 dBTP, con misura ITU-R BS.1770.

Legge praticamente ogni formato: MP3, WAV, AIFF, FLAC, ALAC, M4A/AAC, OGG, Opus, WMA, APE, WavPack, AC3, DTS, AMR, CAF, MP4, MOV, MKV, AVI, WebM, WMV, FLV, MPEG, VOB, TS/M2TS, 3GP e molti altri. Dai video viene estratta la traccia audio.

L'interfaccia è in **italiano** (predefinito) e in **inglese**: si cambia con i pulsanti **IT / EN** in alto a destra e la scelta viene ricordata.

## Come si usa

1. Trascina file o cartelle nella finestra, oppure usa **Aggiungi file…** / **Aggiungi cartella…** (le cartelle vengono lette anche nelle sottocartelle).
2. Scegli il formato: **MP3 320** o **WAV**.
3. In **Elaborazione** lascia attive (o disattiva) le opzioni **Taglia il silenzio iniziale e finale** e **Normalizza il volume**.
4. Scegli dove salvare: nella stessa cartella dell'originale o in un'altra cartella.
5. Premi **Converti**. Ogni file viene prima analizzato («Analisi…») e poi convertito. Al termine, **Apri cartella** mostra i file convertiti.

### Taglio dei silenzi e normalizzazione

- **Silenzio:** viene considerato silenzio tutto ciò che resta sotto −60 dBFS. Si tolgono solo il silenzio all'inizio e quello alla fine; le pause dentro il brano restano intatte. Un file completamente muto non viene tagliato.
- **Volume:** ogni file viene misurato e portato a −23 LUFS con un semplice guadagno, che lascia intatta la dinamica. Solo se il guadagno necessario farebbe superare −1 dBTP entra in azione un limitatore true peak. In quel caso il limite di picco prevale, come prevede la norma, e il file può risultare leggermente sotto −23 LUFS.
- **Sorgenti mono e multicanale:** la misura viene fatta sul risultato stereo finale. Un mono duplicato sui due canali e un 5.1 riportato a stereo escono quindi anch'essi a −23 LUFS.
- **WAV identici bit per bit:** con le due opzioni disattivate, un WAV già a 16 bit / 44.100 Hz resta identico bit per bit all'originale.

### Nome del programma nei tag

Ogni file convertito riporta il nome del programma nei metadati:

| Formato | Campo | Valore |
|---|---|---|
| MP3 | ID3 TENC, «Codificato da» | `Convertitore Audio 1.1.0 - a cura di Massimiliano Mascioli Trippa` |
| WAV | INFO ITCH | `Convertitore Audio 1.1.0 - a cura di Massimiliano Mascioli Trippa` |
| WAV | BWF `bext` originator, chunk broadcast | `Convertitore Audio` |

Il campo «Codificato da» si vede, ad esempio, in Esplora risorse (Proprietà → Dettagli), VLC, Mp3tag e foobar2000. Il campo «Software» (TSSE/ISFT) viene invece scritto sempre da FFmpeg con il proprio nome e non si può modificare.

Dettagli utili:

- Gli originali non vengono mai modificati né sovrascritti. Se il file di destinazione esiste già, il nuovo file prende un nome come `brano (1).mp3`.
- Si convertono fino a 4 file alla volta.
- Titolo, artista, album e gli altri tag vengono copiati; negli MP3 viene mantenuta anche la copertina.
- Le sorgenti mono diventano stereo con lo stesso segnale su entrambi i canali.
- Nel WAV, la riduzione a 16 bit avviene con dither triangolare.
- I file che non si possono convertire (video senza audio, file danneggiati) vengono segnati in rosso: fai doppio clic sulla riga per vedere il dettaglio.
- **Annulla** interrompe la conversione e cancella i file lasciati a metà.

## Installazione

Scarica dalla pagina [Releases](../../releases/latest) il file adatto al tuo sistema:

| Sistema | File |
|---|---|
| macOS con processore Apple (M1, M2, M3, M4…), macOS 12 o successivo | `ConvertitoreAudio-macOS-AppleSilicon.zip` |
| macOS con processore Intel, macOS 12 o successivo | `ConvertitoreAudio-macOS-Intel.zip` |
| Windows 10 / 11 (64 bit) | `ConvertitoreAudio-Windows-x64.zip` |
| Linux 64 bit (Ubuntu 22.04+, Debian 12+, Fedora 36+, Mint 21+) | `ConvertitoreAudio-Linux-x64.tar.gz` |

### macOS

1. Scompatta lo zip e trascina **Convertitore Audio** in **Applicazioni**.
2. L'app non è firmata con un certificato Apple, quindi al primo avvio macOS la blocca. Per sbloccarla:
   - apri l'app una volta (comparirà l'avviso), poi vai in **Impostazioni di Sistema → Privacy e sicurezza** e premi **Apri comunque**;
   - in alternativa, da Terminale:
     ```bash
     xattr -dr com.apple.quarantine "/Applications/Convertitore Audio.app"
     ```
3. Puoi anche trascinare i file sull'icona dell'app nel Dock, oppure usare **Apri con → Convertitore Audio** dal Finder.

### Windows

1. Scompatta lo zip e avvia **Convertitore Audio.exe**. Non serve installazione.
2. Se compare «Windows ha protetto il PC», premi **Ulteriori informazioni → Esegui comunque**. L'avviso compare perché il programma non è firmato digitalmente.
3. Puoi anche trascinare i file direttamente sull'icona del programma.

### Linux

```bash
tar -xzf ConvertitoreAudio-Linux-x64.tar.gz
./ConvertitoreAudio
```

È un unico eseguibile: puoi spostarlo dove preferisci, per esempio in `~/.local/bin`.

FFmpeg è già incluso in tutte le versioni: non va installato altro.

## Creare i pacchetti

| Sistema | Comando | Risultato |
|---|---|---|
| macOS | `./build_mac.sh` | `dist/Convertitore Audio.app` e `dist/ConvertitoreAudio-macOS.zip` |
| Windows | doppio clic su `build_windows.bat` | `dist\Convertitore Audio.exe` e `dist\ConvertitoreAudio-Windows.zip` |
| Linux | `./build_linux.sh` | `dist/ConvertitoreAudio` e `dist/ConvertitoreAudio-Linux-x64.tar.gz` |

Ogni pacchetto va creato sul proprio sistema. Serve Python 3.9 o successivo da [python.org](https://www.python.org/downloads/); su Mac il Python di sistema non va bene perché usa una versione di Tk troppo vecchia.

**Con GitHub (tutte le versioni insieme):** il workflow `.github/workflows/build.yml` crea su GitHub le versioni macOS Apple Silicon, macOS Intel, Windows e Linux, e prova ad avviarle tutte.

- Per pubblicare una nuova versione, invia un tag che inizia con `v`: il workflow crea la Release con i file da scaricare.
  ```bash
  git tag v1.1.1
  git push origin v1.1.1
  ```
- Per creare i pacchetti senza pubblicare nulla, apri **Actions → Build → Run workflow**: i pacchetti restano scaricabili come *artifact*.

### Avvio dal codice sorgente

```bash
pip install tkinterdnd2 imageio-ffmpeg
python3 convertitore_audio.py
```

`tkinterdnd2` serve per il trascinamento dei file. `imageio-ffmpeg` fornisce FFmpeg; se manca, il programma usa l'FFmpeg installato nel sistema.

## Parametri di conversione

```text
Analisi:  silencedetect=noise=-60dB:duration=0.1, loudnorm=I=-23:TP=-1 (misura)
Taglio:   atrim=start=…:end=…
Volume:   volume=±X dB   (oppure loudnorm a due passaggi con limitatore true peak)
MP3:      -c:a libmp3lame -b:a 320k -ar 44100 -ac 2 -id3v2_version 3   (+ copertina)
WAV:      -c:a pcm_s16le -ar 44100 -ac 2 -write_bext 1   (+ dither triangolare)
```

## Licenze

- Convertitore Audio — © Massimiliano Mascioli Trippa.
- Il programma usa [FFmpeg](https://ffmpeg.org), distribuito con licenza GPL; il codice sorgente di FFmpeg è disponibile su ffmpeg.org. Il binario incluso proviene dal pacchetto [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg).
- Il trascinamento dei file usa [tkinterdnd2](https://github.com/Eliav2/tkinterdnd2) e tkdnd (licenze MIT/BSD).

---

## English

**Audio Converter**, created by Massimiliano Mascioli Trippa (version 1.1.0). It converts any audio or video file to **MP3 320 kbps CBR, 44,100 Hz stereo** or to **16-bit PCM WAV, 44,100 Hz stereo**. Click **EN** in the top-right corner to switch the interface to English; the app remembers your choice.

- **Use:** drop files or folders into the window, or use **Add files…** / **Add folder…**. Then choose the format and the destination, and click **Convert**.
- **Processing (both on by default):** the app trims leading and trailing silence below −60 dBFS and leaves pauses inside the track untouched. It also normalizes loudness to **EBU R128**: −23 LUFS integrated, −1 dBTP max true peak. It applies a plain gain whenever it can, and a true-peak limiter only when the peaks require one.
- **Tool name in the tags:** MP3 files get it in ID3 TENC («Encoded by»). WAV files get it in INFO ITCH and in the BWF `bext` originator field.
- **What is kept:** tags and MP3 cover art are copied. Original files are never overwritten.
- **macOS first launch:** open the app once, then go to **System Settings → Privacy & Security** and click **Open Anyway**. Alternatively, run the `xattr` command shown above.
- **Windows SmartScreen:** click **More info → Run anyway**.
- **Download:** go to the [Releases](../../releases/latest) page. Builds are available for macOS (Apple Silicon and Intel), Windows x64 and Linux x64.
- **Linux:** extract the archive with `tar -xzf ConvertitoreAudio-Linux-x64.tar.gz`, then run `./ConvertitoreAudio`.
- **Building:** run `./build_mac.sh`, `build_windows.bat` or `./build_linux.sh` on the matching system. Pushing a `v*` tag builds every version on GitHub Actions and publishes a Release.
