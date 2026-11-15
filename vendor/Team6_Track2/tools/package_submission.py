"""Create a clean submission ZIP; excludes keys, environments and generated caches."""
import argparse
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", "out", "build", "dist"}
SKIP_NAMES = {"credentials.json", "secrets.json", ".netrc", "Thumbs.db", ".DS_Store", "desktop.ini"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".zip", ".tar", ".pem", ".key"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT.parent / "Team6_Track2.zip")
    args = parser.parse_args()
    destination = args.out.resolve()
    if destination.is_relative_to(ROOT):
        raise ValueError("Write the ZIP outside the repository to prevent self-inclusion")
    destination.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for source in sorted(ROOT.rglob("*")):
            if not source.is_file() or source.is_symlink():
                continue
            relative = source.relative_to(ROOT)
            if any(part in SKIP_DIRS for part in relative.parts):
                continue
            if source.name.startswith(".env") or source.name in SKIP_NAMES or source.suffix.lower() in SKIP_SUFFIXES:
                continue
            archive.write(source, "Team6_Track2/" + relative.as_posix())
            count += 1
    with zipfile.ZipFile(destination) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP integrity failure: {bad}")
        expanded = sum(info.file_size for info in archive.infolist())
    print(f"{destination}: {count} files; {destination.stat().st_size / 1048576:.2f} MiB compressed; {expanded / 1048576:.2f} MiB expanded; CRC check passed")


if __name__ == "__main__":
    main()
