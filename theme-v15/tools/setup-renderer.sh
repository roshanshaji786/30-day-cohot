#!/usr/bin/env bash
# Installs the headless browser that tools/render_check.py drives.
#
# Why this script exists: the usual routes are blocked in this sandbox
# (`playwright install chromium` cannot reach its CDN, apt-get needs root, and
# `npx puppeteer browsers install` fails TLS). The @sparticuz/chromium npm
# package ships the Chromium binary *inside the tarball*, so it downloads fine,
# and it also bundles the Amazon Linux shared libraries the binary needs.
#
#   bash tools/setup-renderer.sh
#   PYTHONPATH=/home/user/pylibs python3 tools/render_check.py
#
# Override the resulting paths with env vars if you install elsewhere:
#   RENDER_CHROMIUM, RENDER_LIBDIR, RENDER_NODE_DIR

set -euo pipefail

NODE_DIR="${RENDER_NODE_DIR:-/tmp/btest}"
CHROMIUM="${RENDER_CHROMIUM:-/tmp/chromium-bin}"
LIBDIR="${RENDER_LIBDIR:-/tmp/al2023x/lib}"

echo "==> installing puppeteer + bundled chromium into $NODE_DIR"
mkdir -p "$NODE_DIR"
cd "$NODE_DIR"
[ -f package.json ] || npm init -y >/dev/null
npm install --no-audit --no-fund puppeteer @sparticuz/chromium

echo "==> extracting chromium and its shared libraries"
node -e '
const fs = require("fs"), zlib = require("zlib");
const bin = "node_modules/@sparticuz/chromium/bin/";
const write = (src, dest, mode) => {
  const out = zlib.brotliDecompressSync(fs.readFileSync(bin + src));
  fs.writeFileSync(dest, out, mode ? { mode } : undefined);
  console.log("   " + dest + "  " + (out.length / 1048576).toFixed(1) + " MB");
};
write("chromium.br", process.env.CHROMIUM || "/tmp/chromium-bin", 0o755);
write("al2023.tar.br", "/tmp/al2023.tar");
write("fonts.tar.br", "/tmp/fonts.tar");
'

mkdir -p "$LIBDIR"
tar -xf /tmp/al2023.tar -C "$(dirname "$LIBDIR")" 2>/dev/null || true
[ -d "$LIBDIR" ] || tar -xf /tmp/al2023.tar -C /tmp

export LD_LIBRARY_PATH="$LIBDIR"
"$CHROMIUM" --version

cat <<EOF

==> ready

  chromium : $CHROMIUM
  libs     : $LIBDIR
  puppeteer: $NODE_DIR

Run the visual gate:
  PYTHONPATH=/home/user/pylibs python3 tools/render_check.py
EOF
