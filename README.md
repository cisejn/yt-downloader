# YouTube Downloader

A full-stack YouTube downloader web app built with **Python (Flask)** and **yt-dlp**.  
Paste a URL → preview video info → download as MP4 or MP3.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-red)

---

## Features

- Download YouTube videos as MP4 (360p / 480p / 720p / 1080p)
- Download audio as MP3 (192kbps)
- Video preview with thumbnail, title, duration, and view count
- Real-time download progress bar
- Auto-cleanup of files after download

---

## Requirements

- Python 3.10+
- **ffmpeg** must be installed on your system

Install ffmpeg:
- **Mac:** `brew install ffmpeg`
- **Ubuntu/Debian:** `sudo apt install ffmpeg`
- **Windows:** Download from https://ffmpeg.org/download.html

---

## Quick Start

```bash
git clone https://github.com/<your-username>/yt-downloader.git
cd yt-downloader

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5001**

---

## API Reference

### `POST /api/info`
Fetch video metadata without downloading.

### `POST /api/download`
Start a download job. Returns `{ job_id }`.

### `GET /api/status/<job_id>`
Poll download progress. Returns `{ status, progress, title }`.

### `GET /api/file/<job_id>`
Stream the completed file to the browser.

---

## Disclaimer

This tool is for personal and educational use only.  
Downloading YouTube videos may violate YouTube's Terms of Service.

---

## License

MIT
