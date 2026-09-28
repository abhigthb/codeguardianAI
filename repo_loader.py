import io, re, zipfile, requests
from config import ALLOWED_EXT, SKIP_DIRS, MAX_FILE_BYTES, MAX_FILES


def _valid(path: str) -> bool:
    if any(s in path.split("/") for s in SKIP_DIRS):
        return False
    return any(path.endswith(ext) for ext in ALLOWED_EXT)


def _read_zip(fileobj, max_files=MAX_FILES) -> dict:
    files = {}
    with zipfile.ZipFile(fileobj) as zf:
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            clean = "/".join(name.split("/")[1:]) if "/" in name else name
            if not clean or not _valid(clean):
                continue
            data = zf.read(name)
            if len(data) > MAX_FILE_BYTES:
                continue
            try:
                files[clean] = data.decode("utf-8")
            except UnicodeDecodeError:
                continue
            if len(files) >= max_files:
                break
    return files


def load_from_github(url: str, max_files=MAX_FILES) -> dict:
    m = re.match(r"https?://github\.com/([^/]+)/([^/#?]+)", url.strip())
    if not m:
        raise ValueError("Enter a valid GitHub URL, e.g. https://github.com/user/repo")
    owner, repo = m.group(1), m.group(2).removesuffix(".git")
    r = requests.get(f"https://codeload.github.com/{owner}/{repo}/zip/HEAD", timeout=60)
    if r.status_code != 200:
        raise ValueError("Could not download repo. It must be public.")
    return _read_zip(io.BytesIO(r.content), max_files)


def load_from_uploads(uploaded_files, max_files=MAX_FILES) -> dict:
    files = {}
    for f in uploaded_files:
        if f.name.endswith(".zip"):
            files.update(_read_zip(io.BytesIO(f.read()), max_files))
        else:
            try:
                files[f.name] = f.read().decode("utf-8")
            except UnicodeDecodeError:
                pass
    return dict(list(files.items())[:max_files])