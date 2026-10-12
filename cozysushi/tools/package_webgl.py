"""Split Unity build files for Git, or restore them in a Pages staging folder."""
import argparse
import hashlib
import json
from pathlib import Path

GAME = Path(__file__).resolve().parents[1]
REPO = GAME.parent
CHUNKS = GAME / ".build-chunks"
LIMIT = 90 * 1024 * 1024
CHUNK_SIZE = 50 * 1024 * 1024
BEGIN = "# BEGIN Cozy Sushi generated build exclusions"
END = "# END Cozy Sushi generated build exclusions"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pack():
    files = []
    CHUNKS.mkdir(exist_ok=True)
    used = {"manifest.json"}
    for source in sorted((GAME / "Build").rglob("*")):
        if not source.is_file() or source.stat().st_size <= LIMIT:
            continue
        relative = source.relative_to(REPO).as_posix()
        prefix = hashlib.sha256(relative.encode()).hexdigest()[:16]
        parts = []
        with source.open("rb") as stream:
            index = 0
            while block := stream.read(CHUNK_SIZE):
                name = f"{prefix}.{index:04d}.part"
                (CHUNKS / name).write_bytes(block)
                parts.append({"name": name, "size": len(block),
                              "sha256": hashlib.sha256(block).hexdigest()})
                used.add(name)
                index += 1
        files.append({"path": relative, "size": source.stat().st_size,
                      "sha256": digest(source), "parts": parts})
        print(f"Packed {relative}: {len(parts)} chunks")
    manifest = {"version": 1, "files": files}
    (CHUNKS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # Only remove obsolete generated parts in this script's dedicated folder.
    for old in CHUNKS.glob("*.part"):
        if old.name not in used and old.resolve().parent == CHUNKS.resolve():
            old.unlink()
    ignore = REPO / ".gitignore"
    text = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
    if BEGIN in text:
        start = text.index(BEGIN)
        finish = text.index(END, start) + len(END)
        text = text[:start] + text[finish:]
    rules = ["/" + entry["path"] for entry in files]
    ignore.write_text(text.rstrip() + "\n\n" + BEGIN + "\n" +
                      "\n".join(rules) + "\n" + END + "\n", encoding="utf-8")
    print("Original build files remain on disk. Commit chunks, manifest and .gitignore.")


def assemble(destination):
    destination = destination.resolve()
    if destination == REPO.resolve() or REPO.resolve() in destination.parents:
        raise ValueError("Use a staging folder outside the repository.")
    manifest = json.loads((CHUNKS / "manifest.json").read_text(encoding="utf-8"))
    if manifest["version"] != 1:
        raise ValueError("Unsupported manifest version")
    for entry in manifest["files"]:
        target = (destination / entry["path"]).resolve()
        if destination not in target.parents:
            raise ValueError("Invalid output path")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".assembling")
        with temporary.open("wb") as output:
            for part in entry["parts"]:
                source = (CHUNKS / part["name"]).resolve()
                if source.parent != CHUNKS.resolve():
                    raise ValueError("Invalid chunk path")
                if source.stat().st_size != part["size"] or digest(source) != part["sha256"]:
                    raise ValueError(f"Corrupt chunk: {source.name}")
                with source.open("rb") as stream:
                    while block := stream.read(1024 * 1024):
                        output.write(block)
        if temporary.stat().st_size != entry["size"] or digest(temporary) != entry["sha256"]:
            raise ValueError(f"Reconstruction failed: {entry['path']}")
        temporary.replace(target)
        print(f"Verified {entry['path']} ({entry['size']} bytes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["pack", "assemble"])
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    if args.action == "pack":
        pack()
    else:
        if args.destination is None:
            parser.error("assemble requires --destination")
        assemble(args.destination)
