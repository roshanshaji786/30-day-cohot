#!/usr/bin/env python3
"""
Package the theme for Shopify upload.

  1. runs tools/verify.py (static checks) -- aborts the build if anything fails
  2. runs tools/render_check.py (real headless browser render + screenshots)
     -- aborts the build if the theme does not visibly render correctly
  3. zips only the folders Shopify expects, so the archive uploads cleanly
  4. prints the file size, file count and SHA-256 of the archive

Step 2 exists because a theme once passed every static check and still rendered
as unstyled Times New Roman in a live store. A file is not shipped until it has
been seen rendering in a browser.

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
                      os.path.join(os.path.dirname(here), "theme-v15")):
        if os.path.exists(os.path.join(candidate, "config", "settings_schema.json")):
            return candidate
    raise SystemExit("Could not find the theme folder. Pass it as the first argument.")


def main():
    theme = (sys.argv[1] if len(sys.argv) > 1 else theme_root()).rstrip("/")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(theme) or ".", "ai-shopify-business-bootcamp-v15.zip")

    print("==", "verify".upper(), "=" * 46)
    result = subprocess.run([sys.executable, os.path.join(theme, "tools/verify.py"), theme])
    if result.returncode != 0:
        raise SystemExit("\nBuild aborted: fix the problems above and re-run.")

    print("\n==", "render".upper(), "=" * 46)
    render = subprocess.run([sys.executable, os.path.join(theme, "tools/render_check.py")],
                            env=dict(os.environ, PYTHONPATH=os.environ.get(
                                "PYTHONPATH", "/home/user/pylibs")))
    if render.returncode != 0:
        raise SystemExit("\nBuild aborted: the rendered page did not pass the visual gate.\n"
                         "Screenshots for inspection: "
                         + os.environ.get("RENDER_OUT", "/tmp/theme-render") + "/shots")

    print("\n==", "resilience".upper(), "=" * 40)
    print("  confirming the page still renders if the :root token block is lost")
    resilience = subprocess.run([sys.executable, os.path.join(theme, "tools/render_check.py"),
                                 "--no-vars"],
                                env=dict(os.environ, PYTHONPATH=os.environ.get(
                                    "PYTHONPATH", "/home/user/pylibs")))
    if resilience.returncode != 0:
        raise SystemExit("\nBuild aborted: the theme does not survive a lost token block.\n"
                         "Add literal fallbacks to the var() declarations in assets/theme.css.")

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
