"""
helper/downloader.py
Moteur de téléchargement universel compatible ProgressUpdater.
"""
import os, re, logging, asyncio
import httpx, patoolib, yt_dlp

logger = logging.getLogger(__name__)
DOWNLOAD_DIR = "downloads/"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

YTDLP_PATTERNS = re.compile(
    r"(youtube\.com|youtu\.be|tiktok\.com|instagram\.com|"
    r"dailymotion\.com|twitter\.com|x\.com|facebook\.com|"
    r"vimeo\.com|twitch\.tv|reddit\.com|soundcloud\.com|"
    r"bilibili\.com|nicovideo\.jp|rumble\.com|odysee\.com)",
    re.IGNORECASE,
)
ARCHIVE_EXTENSIONS = {
    ".zip",".rar",".7z",".tar",".gz",".bz2",
    ".xz",".tar.gz",".tar.bz2",".tar.xz",
}

def is_ytdlp_url(url): return bool(YTDLP_PATTERNS.search(url))
def is_archive(path):
    lower = path.lower()
    return any(lower.endswith(e) for e in ARCHIVE_EXTENSIONS)


async def download_direct(url: str, dest_dir: str, progress_cb=None) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=300) as client:
        async with client.stream("GET", url) as resp:
            resp.raise_for_status()
            cd = resp.headers.get("Content-Disposition","")
            m  = re.search(r'filename="?([^";\n]+)"?', cd)
            filename = m.group(1).strip() if m else url.split("?")[0].rstrip("/").split("/")[-1] or "fichier"
            total    = int(resp.headers.get("Content-Length", 0))
            dest     = os.path.join(dest_dir, filename)
            done     = 0

            # Informe ProgressUpdater du nom de fichier
            if progress_cb and hasattr(progress_cb, "filename") and not progress_cb.filename:
                progress_cb.filename = filename

            logger.info(f"[DL Direct] {filename}")
            with open(dest,"wb") as f:
                async for chunk in resp.aiter_bytes(512*1024):
                    f.write(chunk)
                    done += len(chunk)
                    if progress_cb and total:
                        await progress_cb(done, total)
    return dest


async def download_ytdlp(url: str, dest_dir: str, progress_cb=None, audio_only=False) -> str:
    result = {"path": None, "error": None}
    loop   = asyncio.get_event_loop()

    def _hook(d):
        if d["status"] == "finished":
            result["path"] = d["filename"]
        if progress_cb and d["status"] == "downloading":
            dl    = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            if total:
                asyncio.run_coroutine_threadsafe(progress_cb(dl, total), loop)

    opts = {
        "outtmpl":              os.path.join(dest_dir, "%(title)s.%(ext)s"),
        "format":               "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format":  "mp4",
        "noplaylist":           True,
        "quiet":                True,
        "no_warnings":          True,
        "progress_hooks":       [_hook],
        "http_headers":         {"User-Agent":"Mozilla/5.0"},
    }
    if audio_only:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{"key":"FFmpegExtractAudio","preferredcodec":"mp3"}]

    def _run():
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not result["path"]:
                    result["path"] = ydl.prepare_filename(info)
        except Exception as e:
            result["error"] = str(e)

    await loop.run_in_executor(None, _run)
    if result["error"]: raise RuntimeError(result["error"])

    # Correction extension après merge
    if result["path"] and not os.path.exists(result["path"]):
        base = os.path.splitext(result["path"])[0]
        for ext in [".mp4",".mkv",".webm",".mp3",".m4a"]:
            if os.path.exists(base + ext):
                result["path"] = base + ext; break

    logger.info(f"[yt-dlp] Terminé : {result['path']}")
    return result["path"]


async def extract_archive(archive_path: str, dest_dir: str) -> list[str]:
    extract_to = os.path.join(dest_dir, "extracted_" + os.path.basename(archive_path))
    os.makedirs(extract_to, exist_ok=True)
    await asyncio.get_event_loop().run_in_executor(
        None, lambda: patoolib.extract_archive(archive_path, outdir=extract_to)
    )
    files = []
    for root,_,fnames in os.walk(extract_to):
        for f in fnames: files.append(os.path.join(root,f))
    logger.info(f"[Extract] {len(files)} fichiers")
    return files
