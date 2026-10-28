"""Lossless daily study books. Cleanup requires matching sources and a pushed private snapshot."""
import argparse
import base64
import hashlib
import json
import os
import posixpath
import re
import subprocess
from pathlib import Path, PurePosixPath

DATA_BEGIN = "<!-- STUDY_BOOK_SOURCE_DATA_BEGIN -->"
DATA_END = "<!-- STUDY_BOOK_SOURCE_DATA_END -->"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(root, name):
    root = Path(root).resolve()
    name = str(name).replace("\\", "/")
    parts = PurePosixPath(name)
    if parts.is_absolute() or ":" in name or any(p in ("..", ".git") for p in parts.parts):
        raise ValueError(f"Unsafe relative path: {name}")
    if not parts.parts:
        raise ValueError("Empty path")
    path = root.joinpath(*parts.parts)
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Path escapes workspace: {name}")
    current = root
    for part in parts.parts:
        current = current / part
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError(f"Linked path is not eligible: {name}")
    return path


def check_cleanup_path(name):
    parts = PurePosixPath(name)
    if parts.parts[0] not in ("03-code_codex", "04-notes"):
        raise ValueError(f"Protected source cannot be cleaned: {name}")
    if parts.suffix not in (".c", ".py", ".md", ".json") or parts.name == "knowledge-corrections.md":
        raise ValueError(f"Shared/non-lesson file cannot be cleaned: {name}")


def git(root, *args):
    p = subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=35)
    if p.returncode:
        raise ValueError(p.stderr.decode("utf-8", errors="replace").strip())
    return p.stdout


def anchor(name):
    return "src-" + digest(name.encode())[:12]


def normalize(raw):
    return raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def rewrite_links(text, source, book, all_paths):
    def replace(match):
        label, target = match.groups()
        if re.match(r"^[a-zA-Z][\w+.-]*://", target) or target.startswith("mailto:"):
            return match.group(0)
        if target.startswith("#"):
            return f"[{label}](#{anchor(source)})"
        target = target.strip("<>")
        path, sep, fragment = target.partition("#")
        if not path or re.match(r"^[a-zA-Z]:", path):
            return match.group(0)
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source), path))
        if resolved in all_paths:
            return f"[{label}](#{anchor(resolved)})"
        rebased = posixpath.relpath(resolved, posixpath.dirname(book))
        if sep:
            rebased += "#" + fragment
        return f"[{label}]({rebased})"
    return re.sub(r"(?<!!)\[([^\]]+)\]\(([^)\n]+)\)", replace, text)


def section(item, book, all_paths):
    name = item["path"]
    raw = base64.b64decode(item["bytes_b64"], validate=True)
    content = normalize(raw)
    heading = (f"<!-- study-source:{anchor(name)}:begin -->\n"
               f'<a id="{anchor(name)}"></a>\n\n'
               f"### {name}\n\n来源：{item['role']}；SHA-256：`{item['sha256']}`。\n\n")
    if name.endswith(".md"):
        body = rewrite_links(content, name, book, all_paths)
    else:
        longest = max((len(m[0]) for m in re.finditer(r"`+", content)), default=0)
        fence = "`" * max(3, longest + 1)
        language = {".c": "c", ".py": "python", ".json": "json", ".bat": "bat"}.get(Path(name).suffix, "text")
        body = f"{fence}{language}\n{content}\n{fence}"
    return heading + body + f"\n\n<!-- study-source:{anchor(name)}:end -->"


def snapshot_sources(root, data):
    snapshot = data["snapshot_commit"]
    if not re.fullmatch(r"[0-9a-f]{40}", snapshot):
        raise ValueError("A full snapshot commit is required")
    for item in data["sources"]:
        raw = git(root, "show", f"{snapshot}:{item['path']}")
        if digest(raw) != item["sha256"]:
            raise ValueError(f"Snapshot bytes do not match source: {item['path']}")


def build(root, book, date, snapshot, entries, intro):
    root = Path(root).resolve()
    out = safe(root, book)
    sources, seen = [], set()
    for entry in entries:
        name = entry["path"].replace("\\", "/")
        if name.casefold() in seen:
            raise ValueError(f"Duplicate source: {name}")
        seen.add(name.casefold())
        if entry.get("cleanup", False):
            check_cleanup_path(name)
            if name == book:
                raise ValueError("Cannot clean the book itself")
        raw = safe(root, name).read_bytes()
        normalize(raw)  # Reject undecodable text before writing or cleaning anything.
        sources.append({"path": name, "group": entry.get("group", "其他"),
                        "role": entry.get("role", "课堂资料"), "cleanup": bool(entry.get("cleanup")),
                        "sha256": digest(raw), "bytes_b64": base64.b64encode(raw).decode("ascii")})
    data = {"schema_version": 1, "date": date, "book": book,
            "snapshot_commit": snapshot, "sources": sources}
    snapshot_sources(root, data)
    all_paths = {s["path"] for s in sources}
    lines = [intro.rstrip(), "", "## 源文件目录与完整内容", "",
             f"原件快照：`{snapshot}`。以下内容可离线按原始字节恢复。", ""]
    for item in sources:
        lines.append(f"- [{item['path']}](#{anchor(item['path'])})（{item['group']} / {item['role']}）")
    previous = None
    for item in sources:
        if item["group"] != previous:
            previous = item["group"]
            lines.extend(["", "## " + previous, ""])
        lines.extend([section(item, book, all_paths), ""])
    lines.extend(["<details>", "<summary>原文件精确恢复数据（工具使用）</summary>", "", DATA_BEGIN,
                  "```json", json.dumps(data, ensure_ascii=False, indent=2), "```", DATA_END,
                  "", "</details>", ""])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    verify(root, book)
    return data


def verify(root, book):
    text = safe(root, book).read_text(encoding="utf-8")
    if text.count(DATA_BEGIN) != 1 or text.count(DATA_END) != 1:
        raise ValueError("Missing/duplicate recovery section")
    encoded = text.split(DATA_BEGIN, 1)[1].split(DATA_END, 1)[0].strip()
    if not (encoded.startswith("```json\n") and encoded.endswith("\n```")):
        raise ValueError("Invalid recovery envelope")
    data = json.loads(encoded[len("```json\n"):-len("\n```")])
    if data["schema_version"] != 1 or data["book"] != book:
        raise ValueError("Book identity mismatch")
    names = [s["path"] for s in data["sources"]]
    if len({n.casefold() for n in names}) != len(names):
        raise ValueError("Duplicate source paths")
    for item in data["sources"]:
        safe(root, item["path"])
        if item["cleanup"]:
            check_cleanup_path(item["path"])
        raw = base64.b64decode(item["bytes_b64"], validate=True)
        if digest(raw) != item["sha256"]:
            raise ValueError(f"Recovery checksum mismatch: {item['path']}")
        if text.count(section(item, book, set(names))) != 1:
            raise ValueError(f"Readable section differs from source: {item['path']}")
    return data


def private_remote_snapshot(root, snapshot):
    if git(root, "rev-parse", "HEAD").decode().strip() != snapshot:
        raise ValueError("HEAD changed since snapshot; stop cleanup")
    remote = git(root, "remote", "get-url", "origin").decode().strip()
    remote_head = git(root, "ls-remote", "--heads", "origin", "main").decode().split()
    if not remote_head or remote_head[0] != snapshot:
        raise ValueError("Snapshot is not current on origin/main")
    local = Path(remote)
    if local.is_dir():
        p = subprocess.run(["git", "--git-dir", str(local), "rev-parse", "--is-bare-repository"],
                           capture_output=True, text=True, timeout=10)
        if p.returncode or p.stdout.strip() != "true":
            raise ValueError("Invalid local backup remote")
        return
    if not remote.startswith("https://github.com/"):
        raise ValueError("Remote privacy verification is not supported for this host")
    slug = remote.removeprefix("https://github.com/").removesuffix(".git").strip("/")
    p = subprocess.run(["gh", "api", "repos/" + slug, "--jq", "{private:.private}"],
                       capture_output=True, text=True, timeout=25,
                       env=os.environ | {"GODEBUG": "http2client=0"})
    if p.returncode or not json.loads(p.stdout).get("private"):
        raise ValueError("Private GitHub backup could not be verified")


def clean(root, book):
    root = Path(root).resolve()
    data = verify(root, book)
    snapshot_sources(root, data)
    selected = [s for s in data["sources"] if s["cleanup"]]
    for item in selected:
        if digest(safe(root, item["path"]).read_bytes()) != item["sha256"]:
            raise ValueError(f"Source changed; nothing will be cleaned: {item['path']}")
    private_remote_snapshot(root, data["snapshot_commit"])
    removed = []
    for item in selected:
        path = safe(root, item["path"])
        if digest(path.read_bytes()) != item["sha256"]:
            raise ValueError(f"Concurrent change; cleanup stopped at {item['path']}")
        path.unlink()  # Only individual verified files; never recursive directory removal.
        removed.append(item["path"])
    return removed


def restore(root, book, source, output=None):
    data = verify(root, book)
    item = next((s for s in data["sources"] if s["path"] == source), None)
    if item is None:
        raise ValueError(f"Source not in book: {source}")
    target = safe(root, output or source)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(base64.b64decode(item["bytes_b64"], validate=True))
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify", "clean", "restore"))
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--book", required=True)
    parser.add_argument("--manifest")
    parser.add_argument("--intro")
    parser.add_argument("--date")
    parser.add_argument("--snapshot")
    parser.add_argument("--source")
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.action == "build":
        if not all((args.manifest, args.intro, args.date, args.snapshot)):
            parser.error("build needs manifest, intro, date and snapshot")
        data = build(args.root, args.book, args.date, args.snapshot,
                     json.loads(Path(args.manifest).read_text(encoding="utf-8-sig")),
                     Path(args.intro).read_text(encoding="utf-8-sig"))
        print(json.dumps({"sources": len(data["sources"]), "snapshot": args.snapshot}))
    elif args.action == "verify":
        data = verify(args.root, args.book)
        print(json.dumps({"verified_sources": len(data["sources"]), "snapshot": data["snapshot_commit"]}))
    elif args.action == "clean":
        print(json.dumps({"removed": clean(args.root, args.book)}, ensure_ascii=False))
    else:
        if not args.source:
            parser.error("restore needs source")
        print(restore(args.root, args.book, args.source, args.output))


if __name__ == "__main__":
    main()
