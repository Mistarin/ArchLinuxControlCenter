#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$SCRIPT_DIR/AppDir"
OUT_APPIMAGE="$SCRIPT_DIR/CachyOS_Control_Center-x86_64.AppImage"

echo "=========================================="
echo " Building CachyOS Control Center AppImage "
echo "=========================================="

echo "[1/4] Preparing AppDir layout..."
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/share/applications"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"

echo "[2/4] Copying application code and assets..."
cp -r "$ROOT_DIR/cachy_control" "$APP_DIR/usr/bin/"
cp "$ROOT_DIR/main.py" "$APP_DIR/usr/bin/"
chmod +x "$APP_DIR/usr/bin/main.py"

# Copy Icon
if [ -f "$SCRIPT_DIR/cachy-control-center.png" ]; then
    cp "$SCRIPT_DIR/cachy-control-center.png" "$APP_DIR/cachy-control-center.png"
    cp "$SCRIPT_DIR/cachy-control-center.png" "$APP_DIR/usr/share/icons/hicolor/256x256/apps/cachy-control-center.png"
elif [ -f "$ROOT_DIR/cachy_control/ui/assets/logo_256.png" ]; then
    cp "$ROOT_DIR/cachy_control/ui/assets/logo_256.png" "$APP_DIR/cachy-control-center.png"
    cp "$ROOT_DIR/cachy_control/ui/assets/logo_256.png" "$APP_DIR/usr/share/icons/hicolor/256x256/apps/cachy-control-center.png"
fi

# Copy Desktop Entry
cp "$SCRIPT_DIR/cachy-control-center.desktop" "$APP_DIR/cachy-control-center.desktop"
cp "$SCRIPT_DIR/cachy-control-center.desktop" "$APP_DIR/usr/share/applications/cachy-control-center.desktop"

# Create AppRun entrypoint
cat << 'APPRUN_EOF' > "$APP_DIR/AppRun"
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/bin:${PYTHONPATH}"
exec /usr/bin/python3 "${HERE}/usr/bin/main.py" "$@"
APPRUN_EOF
chmod +x "$APP_DIR/AppRun"

echo "[3/4] Checking for appimagetool..."
if ! command -v appimagetool &> /dev/null; then
    echo "appimagetool is required. Install it from a trusted distribution package or verify its upstream release before use."
    exit 1
fi

echo "[4/4] Generating AppImage..."
export ARCH=x86_64
appimagetool "$APP_DIR" "$OUT_APPIMAGE"

echo "=========================================="
echo " AppImage successfully created:"
echo " $OUT_APPIMAGE"
echo "=========================================="
