import os
import re
import uuid
import threading
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file, abort
import yt_dlp

app = Flask(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

jobs = {}

# Base options applied to every yt-dlp call — fixes js_runtimes error
BASE_OPTS = {
    "extractor_args": {"youtube": {"player_client": ["ios", "android", "web"]}},
    "http_headers": {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    },
    "quiet": True,
    "no_warnings": True,
}


def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def run_download(job_id, url, dl_type, quality):
    job = jobs[job_id]

    def progress_hook(d):
        if d["status"] == "downloading":
            try:
                # Try multiple ways to get progress percentage
                if "_percent_str" in d:
                    pct_str = d.get("_percent_str", "0%")
                    if isinstance(pct_str, str):
                        pct = float(pct_str.strip().replace("%", ""))
                        job["progress"] = pct
                elif "_progress_hooks_progress" in d:
                    job["progress"] = d["_progress_hooks_progress"]
                else:
                    # Default fallback
                    pass
            except (ValueError, TypeError):
                pass
        elif d["status"] == "finished":
            job["progress"] = 100

    out_tmpl = str(DOWNLOAD_DIR / f"{job_id}.%(ext)s")

    if dl_type == "audio":
        ydl_opts = {
            **BASE_OPTS,
            "format": "bestaudio/best",
            "outtmpl": out_tmpl,
            "progress_hooks": [progress_hook],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": 192,
            }],
        }
    else:
        fmt = {
            "1080": "best",
            "720":  "best",
            "480":  "best",
            "360":  "best",
        }.get(quality, "best")

        ydl_opts = {
            **BASE_OPTS,
            "format": fmt,
            "outtmpl": out_tmpl,
            "progress_hooks": [progress_hook],
            "merge_output_format": "mp4",
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = clean_filename(info.get("title", "video"))
            ext = "mp3" if dl_type == "audio" else "mp4"
            job["title"] = title
            job["ext"] = ext
            job["progress"] = 100
            job["status"] = "done"
    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def get_info():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "URL required"}), 400
    try:
        ydl_opts = {**BASE_OPTS, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return jsonify({
            "title":      info.get("title", "Unknown"),
            "thumbnail":  info.get("thumbnail", ""),
            "duration":   info.get("duration", 0),
            "uploader":   info.get("uploader", "Unknown"),
            "view_count": info.get("view_count", 0),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.get_json(silent=True) or {}
    url     = (data.get("url") or "").strip()
    dl_type = data.get("type", "video")
    quality = data.get("quality", "720")

    if not url:
        return jsonify({"error": "URL required"}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "downloading", "progress": 0, "error": None}

    t = threading.Thread(target=run_download, args=(job_id, url, dl_type, quality), daemon=True)
    t.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def job_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/file/<job_id>")
def get_file(job_id):
    job = jobs.get(job_id)
    if not job or job["status"] != "done":
        abort(404)

    ext   = job.get("ext", "mp4")
    title = job.get("title", "download")
    path  = DOWNLOAD_DIR / f"{job_id}.{ext}"

    if not path.exists():
        abort(404)

    resp = send_file(
        path,
        as_attachment=True,
        download_name=f"{title}.{ext}",
        mimetype="audio/mpeg" if ext == "mp3" else "video/mp4"
    )

    @resp.call_on_close
    def cleanup():
        try:
            path.unlink(missing_ok=True)
            jobs.pop(job_id, None)
        except Exception:
            pass

    return resp


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
