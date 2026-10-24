#!/usr/bin/env bash
# Build a static, redistributable ffmpeg + ffprobe for macOS (host architecture).
#
#   tools/ffmpeg-build/build-macos.sh [--work DIR] [--update-lock]
#
# Produces  <work>/dist/{ffmpeg,ffprobe,BUILDCONF.txt,FFMPEG-LICENSES.txt,SOURCES.txt,sources/*}
# and refuses to finish if the result was configured with --enable-nonfree.
#
# Licence flavor: GPL-2.0-or-later (--enable-gpl for libx264/libx265). Never --enable-nonfree.
# No --enable-version3: nothing we link requires it.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="${TMPDIR:-/tmp}/videobeaux-ffmpeg-build"
UPDATE_LOCK=0
PRINT_PATHS=0
while [ $# -gt 0 ]; do
  case "$1" in
    --work) WORK="$2"; shift 2 ;;
    --update-lock) UPDATE_LOCK=1; shift ;;
    --print-paths) PRINT_PATHS=1; shift ;;       # (used by the tests) print the resolved folders and exit
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
# Everything below cd's around and hands paths to ./configure (which insists on an absolute --prefix), so --work must be
# absolute — `npm run ffmpeg:local` passes a relative one (.ffmpeg-build).
mkdir -p "$WORK"
WORK="$(cd "$WORK" && pwd)"
# shellcheck disable=SC1091
source "$HERE/versions.env"

ARCH="$(uname -m)"                      # arm64 | x86_64
JOBS="$(sysctl -n hw.ncpu)"
SRC="$WORK/src"; BUILD="$WORK/build"; PREFIX="$WORK/prefix"; DIST="$WORK/dist"; TOOLS="$WORK/tools"
mkdir -p "$SRC" "$BUILD" "$PREFIX" "$DIST/sources" "$TOOLS"
echo "work dir: $WORK"
if [ "$PRINT_PATHS" = 1 ]; then echo "WORK=$WORK"; echo "PREFIX=$PREFIX"; echo "DIST=$DIST"; exit 0; fi

if [ "$ARCH" = "arm64" ]; then MINVER=11.0; else MINVER=10.15; fi
export MACOSX_DEPLOYMENT_TARGET="$MINVER"
export PATH="$PREFIX/bin:$TOOLS/bin:$PATH"
# Only ever see libraries we built ourselves (never Homebrew's).
export PKG_CONFIG_LIBDIR="$PREFIX/lib/pkgconfig:$PREFIX/share/pkgconfig"
export PKG_CONFIG_PATH="$PKG_CONFIG_LIBDIR"
export CPPFLAGS="-I$PREFIX/include"
export LDFLAGS="-L$PREFIX/lib"
export CFLAGS="-O2 -mmacosx-version-min=$MINVER"
export CXXFLAGS="-O2 -mmacosx-version-min=$MINVER"

once() { [ -f "$PREFIX/.stamp-$1" ]; }
done_() { touch "$PREFIX/.stamp-$1"; }
log() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

# ── build tools (private; pip wheels for cmake/ninja/meson) ──────────────────
if [ ! -x "$TOOLS/bin/cmake" ] || ! "$TOOLS/bin/cmake" --version | head -1 | grep -q "version 3\."; then
  log "build tools (cmake, ninja, meson)"
  python3 -m venv "$TOOLS"
  "$TOOLS/bin/pip" -q install "cmake>=3.28,<4" ninja meson
fi
command -v nasm >/dev/null 2>&1 || [ "$ARCH" = "arm64" ] || { echo "nasm is required on x86_64 (brew install nasm)"; exit 1; }

# ── fetch + verify ──────────────────────────────────────────────────────────
LOCK="$HERE/sources.sha256"
fetch() {  # name url  → echoes tarball path
  local name="$1" url="$2"
  local file="$SRC/$(basename "$url")"
  if [ ! -f "$file" ]; then curl -fsSL --retry 3 -o "$file.part" "$url" && mv "$file.part" "$file"; fi
  local sum; sum="$(shasum -a 256 "$file" | cut -d' ' -f1)"
  if [ "$UPDATE_LOCK" = 1 ]; then
    grep -v " $(basename "$file")\$" "$LOCK" 2>/dev/null > "$LOCK.tmp" || true
    echo "$sum  $(basename "$file")" >> "$LOCK.tmp"; mv "$LOCK.tmp" "$LOCK"
  elif [ -f "$LOCK" ] && grep -q " $(basename "$file")\$" "$LOCK"; then
    local want; want="$(grep " $(basename "$file")\$" "$LOCK" | cut -d' ' -f1)"
    [ "$want" = "$sum" ] || { echo "CHECKSUM MISMATCH: $name ($(basename "$file"))" >&2; exit 1; }
  else
    echo "warning: no pinned checksum for $(basename "$file") (run with --update-lock)" >&2
  fi
  cp -n "$file" "$DIST/sources/" 2>/dev/null || true
  echo "$file"
}
unpack() {  # tarball → dir (fresh)
  local tb="$1" dir="$BUILD/$(basename "$1" | sed -E 's/\.(tar\.(gz|xz|bz2)|tgz)$//')"
  rm -rf "$dir"; mkdir -p "$dir"; tar -xf "$tb" -C "$dir" --strip-components=1; echo "$dir"
}

# ── private autotools (for zimg's git archive: needs GNU m4, autoconf, automake and libtool) ──
if [ ! -x "$PREFIX/bin/autoreconf" ] || [ ! -x "$PREFIX/bin/m4" ] || [ ! -x "$PREFIX/bin/glibtoolize" ]; then
  log "m4 + autoconf + automake + libtool (private)"
  for pair in "m4:$M4_URL" "autoconf:$AUTOCONF_URL" "automake:$AUTOMAKE_URL" "libtool:$LIBTOOL_URL"; do
    d="$(unpack "$(fetch "${pair%%:*}" "${pair#*:}")")"
    extra=(); [ "${pair%%:*}" = "libtool" ] && extra=(--program-prefix=g)   # glibtool/glibtoolize: never shadow Apple's libtool
    ( cd "$d" && ./configure --prefix="$PREFIX" ${extra[@]+"${extra[@]}"} >/dev/null && make -j"$JOBS" >/dev/null && make install >/dev/null )
  done
fi
export ACLOCAL_PATH="$PREFIX/share/aclocal"
export LIBTOOLIZE="$PREFIX/bin/glibtoolize"

AUTOT=(--prefix="$PREFIX" --disable-shared --enable-static)
build_autotools() {  # stamp name url [extra configure args...]
  local stamp="$1" name="$2" url="$3"; shift 3
  once "$stamp" && return 0
  log "$name"
  local d; d="$(unpack "$(fetch "$name" "$url")")"
  ( cd "$d" && ./configure "${AUTOT[@]}" "$@" && make -j"$JOBS" && make install )
  done_ "$stamp"
}

build_autotools ogg    libogg    "$OGG_URL"
once vorbis || {
  log libvorbis
  d="$(unpack "$(fetch vorbis "$VORBIS_URL")")"
  sed -i '' 's/-force_cpusubtype_ALL//g' "$d/configure"      # old libvorbis configure passes a flag modern ld rejects
  ( cd "$d" && ./configure "${AUTOT[@]}" && make -j"$JOBS" && make install ); done_ vorbis; }
build_autotools opus   opus      "$OPUS_URL"   --disable-doc --disable-extra-programs
build_autotools lame   lame      "$LAME_URL"   --disable-frontend --disable-decoder
build_autotools webp   libwebp   "$WEBP_URL"   --disable-gl --disable-sdl --disable-png --disable-jpeg --disable-tiff --disable-gif --disable-libwebpdemux --disable-libwebpmux
once vpx || {
  log libvpx
  d="$(unpack "$(fetch vpx "$LIBVPX_URL")")"
  ( cd "$d" && ./configure --prefix="$PREFIX" --disable-shared --enable-static --disable-examples --disable-tools --disable-docs --disable-unit-tests --enable-vp9-highbitdepth --enable-pic && make -j"$JOBS" && make install ); done_ vpx; }
once x264 || {
  log x264
  d="$(unpack "$(fetch x264 "$X264_URL")")"
  ( cd "$d" && ./configure --prefix="$PREFIX" --enable-static --enable-pic --disable-cli && make -j"$JOBS" && make install ); done_ x264; }
once x265 || {
  log x265
  d="$(unpack "$(fetch x265 "$X265_URL")")"
  ( cd "$d/source" && cmake -G Ninja -DCMAKE_INSTALL_PREFIX="$PREFIX" -DENABLE_SHARED=OFF -DENABLE_CLI=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
      -DCMAKE_OSX_DEPLOYMENT_TARGET="$MINVER" -DCMAKE_BUILD_TYPE=Release . && ninja && ninja install ); done_ x265; }
once svtav1 || {
  log "SVT-AV1 (AV1 encoder)"
  d="$(unpack "$(fetch svtav1 "$SVTAV1_URL")")"
  ( cd "$d" && cmake -G Ninja -DCMAKE_INSTALL_PREFIX="$PREFIX" -DBUILD_SHARED_LIBS=OFF -DBUILD_APPS=OFF -DBUILD_DEC=OFF \
      -DBUILD_TESTING=OFF -DCMAKE_OSX_DEPLOYMENT_TARGET="$MINVER" -DCMAKE_BUILD_TYPE=Release -DCMAKE_POSITION_INDEPENDENT_CODE=ON . \
      && ninja && ninja install ); done_ svtav1; }
once dav1d || {
  log "dav1d (AV1 decoder)"
  d="$(unpack "$(fetch dav1d "$DAV1D_URL")")"
  ( cd "$d" && meson setup out --prefix="$PREFIX" --default-library=static --buildtype=release \
      -Denable_tools=false -Denable_tests=false -Denable_examples=false && ninja -C out install ); done_ dav1d; }
once zimg || {
  log zimg
  d="$(unpack "$(fetch zimg "$ZIMG_URL")")"
  ( cd "$d" && autoreconf -if >/dev/null 2>&1 && ./configure "${AUTOT[@]}" && make -j"$JOBS" && make install ); done_ zimg; }
build_autotools freetype freetype "$FREETYPE_URL" --with-harfbuzz=no --with-png=no --with-bzip2=no --with-brotli=no
build_autotools fribidi  fribidi  "$FRIBIDI_URL"  --disable-docs
once harfbuzz || {
  log harfbuzz
  d="$(unpack "$(fetch harfbuzz "$HARFBUZZ_URL")")"
  ( cd "$d" && meson setup out --prefix="$PREFIX" --default-library=static --buildtype=release -Dfreetype=enabled -Dglib=disabled -Dgobject=disabled -Dcairo=disabled -Dicu=disabled -Dtests=disabled -Ddocs=disabled -Dcoretext=enabled && ninja -C out install ); done_ harfbuzz; }
build_autotools libass   libass   "$LIBASS_URL"   --disable-fontconfig --disable-require-system-font-provider

# ── ffmpeg ───────────────────────────────────────────────────────────────────
log "ffmpeg $FFMPEG_VERSION"
FF="$(unpack "$(fetch ffmpeg "$FFMPEG_URL")")"
( cd "$FF" && ./configure \
    --prefix="$WORK/ffout" --pkg-config-flags=--static \
    --extra-cflags="-I$PREFIX/include -mmacosx-version-min=$MINVER" \
    --extra-ldflags="-L$PREFIX/lib -mmacosx-version-min=$MINVER" \
    --extra-libs="-lc++ -lm -lpthread" \
    --enable-gpl \
    --enable-libx264 --enable-libx265 --enable-libvpx --enable-libopus --enable-libvorbis --enable-libmp3lame \
    --enable-libass --enable-libfreetype --enable-libharfbuzz --enable-libzimg --enable-libwebp \
    --enable-libsvtav1 --enable-libdav1d \
    --disable-autodetect --enable-zlib --enable-bzlib --enable-iconv --enable-videotoolbox --enable-audiotoolbox \
    --enable-indev=avfoundation \
    --disable-ffplay --disable-doc --disable-debug --disable-shared --enable-static \
    && make -j"$JOBS" && make install )

cp "$WORK/ffout/bin/ffmpeg" "$WORK/ffout/bin/ffprobe" "$DIST/"
strip -x "$DIST/ffmpeg" "$DIST/ffprobe"

# ── report + guard ────────────────────────────────────────────────────────────
"$DIST/ffmpeg" -hide_banner -buildconf > "$DIST/BUILDCONF.txt" 2>&1 || true
"$DIST/ffmpeg" -hide_banner -version | head -3 >> "$DIST/BUILDCONF.txt"
if grep -q -- "--enable-nonfree" "$DIST/BUILDCONF.txt"; then
  echo "FATAL: the build was configured with --enable-nonfree and cannot be redistributed." >&2; exit 1
fi
if otool -L "$DIST/ffmpeg" | grep -E "/opt/homebrew|/usr/local" ; then
  echo "FATAL: ffmpeg links against a non-system dynamic library (not self-contained)." >&2; exit 1
fi

{
  echo "Videobeaux FFmpeg build — licence summary"
  echo "=========================================="
  echo "FFmpeg $FFMPEG_VERSION, configured with --enable-gpl (GPL-2.0-or-later). Not built with --enable-nonfree."
  echo "Videobeaux runs this program as a separate process."
  echo
  echo "Components (see sources/ for the exact source archives used):"
  echo "  FFmpeg $FFMPEG_VERSION  - GPL-2.0-or-later (this build; LGPL-2.1+ core)"
  echo "  x264 ($X264_REV)        - GPL-2.0-or-later"
  echo "  x265 $X265_VERSION      - GPL-2.0-or-later"
  echo "  libvpx $LIBVPX_VERSION  - BSD-3-Clause"
  echo "  opus $OPUS_VERSION      - BSD-3-Clause"
  echo "  libvorbis $VORBIS_VERSION / libogg $OGG_VERSION - BSD-3-Clause"
  echo "  LAME $LAME_VERSION      - LGPL-2.0+"
  echo "  libass $LIBASS_VERSION  - ISC"
  echo "  FreeType $FREETYPE_VERSION - FreeType License (BSD-style) or GPL-2.0"
  echo "  HarfBuzz $HARFBUZZ_VERSION - MIT"
  echo "  FriBidi $FRIBIDI_VERSION - LGPL-2.1+"
  echo "  zimg $ZIMG_VERSION      - WTFPL-2.0"
  echo "  libwebp $WEBP_VERSION   - BSD-3-Clause"
  echo "  SVT-AV1 $SVTAV1_VERSION - BSD-3-Clause-Clear + AOMedia patent licence"
  echo "  dav1d $DAV1D_VERSION    - BSD-2-Clause"
  echo
  echo "Configure line:"; awk '/configuration:/{f=1} f&&NF==0{exit} f' "$DIST/BUILDCONF.txt"
} > "$DIST/FFMPEG-LICENSES.txt"
{ for f in "$DIST"/sources/*; do echo "$(shasum -a 256 "$f" | cut -d' ' -f1)  $(basename "$f")"; done; } > "$DIST/SOURCES.txt"

log "done"; ls -la "$DIST"; "$DIST/ffmpeg" -hide_banner -version | head -2
