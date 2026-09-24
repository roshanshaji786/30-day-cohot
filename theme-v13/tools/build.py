#!/usr/bin/env python3
"""
Package the theme for Shopify upload.

  1. runs tools/verify.py (aborts the build if anything fails)
  2. zips only the folders Shopify expects, so the archive uploads cleanly
  3. prints the file size, file count and SHA-256 of the archive

Usage:  python3 tools/build.py [theme_dir] [output_zip]
"""

import hashlib
import os
import subprocess
import sys
import zipfile

THEME_DIRS = ("assets", "config", "layout", "locales", "sections", "snippets", "templates")
SKIP_NAMES = {".DS_Store", "Thumbs.db"}


def theme_root():
    here = os.path.dirname(os.path.abspath(__file__))
    for candidate in (os.path.dirname(here),
                      os.path.join(os.path.dirname(here), "theme-v13")):
        if os.path.exists(os.path.join(candidate, "config", "settings_schema.json")):
            return candidate
    raise SystemExit("Could not find the theme folder. Pass it as the first argument.")


def main():
    theme = (sys.argv[1] if len(sys.argv) > 1 else theme_root()).rstrip("/")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(theme) or ".", "ai-shopify-business-bootcamp-v13.zip")

    print("==", "verify".upper(), "=" * 46)
    result = subprocess.run([sys.executable, os.path.join(theme, "tools/verify.py"), theme])
    if result.returncode != 0:
        raise SystemExit("\nBuild aborted: fix the problems above and re-run.")

    print("\n==", "package".upper(), "=" * 45)
    files = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for folder in THEME_DIRS:
            root = os.path.join(theme, folder)
            if not os.path.isdir(root):
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
                for name in sorted(filenames):
                    if name.startswith(".") or name in SKIP_NAMES:
                        continue
                    full = os.path.join(dirpath, name)
                    archive.write(full, os.path.relpath(full, theme))
                    files += 1

    with open(out, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()

    size_kb = os.path.getsize(out) / 1024
    print(f"  wrote      {out}")
    print(f"  contents   {files} files in {len(THEME_DIRS)} folders")
    print(f"  size       {size_kb:.1f} KB")
    print(f"  sha256     {digest}")
    print("\n  Upload: Shopify admin → Online Store → Themes → Add theme → Upload zip")

    unzipped = sum(
        os.path.getsize(os.path.join(dp, f))
        for folder in THEME_DIRS
        for dp, _, fs in os.walk(os.path.join(theme, folder))
        for f in fs if not f.startswith(".")
    )
    ratio = size_kb / max(unzipped / 1024, 0.01) * 100
    print(f"  payload    {unzipped / 1024:.1f} KB uncompressed "
          f"(archive is {ratio:.0f}% of that)")


if __name__ == "__main__":
    main()
