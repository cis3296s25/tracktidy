# 🎵 TrackTidy - All-in-One DJ Music Manager (POC)
TrackTidy is a **command-line tool** for managing your music files. It allows you to:
- ✅ **Edit metadata** (song title, artist, album, track number)
- ✅ **Convert audio files** between formats (MP3, WAV, FLAC, AAC, OGG)
- ✅ **Fetch and apply cover art**

---

![This is a screenshot.](images.png)
# How to run
### 1️⃣ Install Dependencies
Make sure you have **Python 3.10+** installed. Then install the required libraries:

```sh
pip install rich mutagen
```

### 2️⃣ Install FFmpeg
TrackTidy uses **FFmpeg** for audio conversion. Install it:

- **Windows**: [Download FFmpeg](https://ffmpeg.org/download.html) and add it to `PATH`.

---


# How to contribute
Follow this project board to know the latest status of the project: [http://...]([http://...])  

### How to build
- Use this github repository: https://github.com/cis3296s25/projects-03-tracktidy
- Project board link: https://github.com/orgs/cis3296s25/projects/72
### Convert an Audio File
```sh
python audio_converter.py
```
- Enter the path to your audio file.
- Choose an output format (MP3, WAV, FLAC, AAC, OGG).
- TrackTidy will display a **real-time progress bar** while converting.

### Edit Metadata
```sh
python metadata_editor.py
```
- View existing metadata.
- Edit **title, artist, album, track number** interactively.

---


