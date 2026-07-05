import base64
import time

START_TIME = time.time()


def human_size(size_bytes: int) -> str:
    if not size_bytes:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {units[i]}"


def uptime() -> str:
    seconds = int(time.time() - START_TIME)
    d, seconds = divmod(seconds, 86400)
    h, seconds = divmod(seconds, 3600)
    m, s = divmod(seconds, 60)
    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


def encode_code(msg_id: int) -> str:
    """Turn a DB-channel message id into a short URL-safe code."""
    raw = str(msg_id).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def decode_code(code: str) -> int:
    padding = "=" * (-len(code) % 4)
    raw = base64.urlsafe_b64decode(code + padding)
    return int(raw.decode("utf-8"))


def detect_category(file_type: str, file_name: str = "") -> str:
    file_name = (file_name or "").lower()
    if file_type == "photo":
        return "Photos"
    if file_type == "video":
        return "Videos"
    if file_type == "audio" or file_type == "voice":
        return "Audio"
    if file_name.endswith(".pdf"):
        return "PDF"
    if file_name.endswith((".zip", ".rar", ".7z")):
        return "Archives"
    if file_name.endswith(".apk"):
        return "APK"
    return "Documents"
