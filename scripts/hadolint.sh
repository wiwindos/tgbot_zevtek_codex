#!/bin/sh
set -e
if command -v hadolint >/dev/null 2>&1; then
    DL=hadolint
else
    DL=/tmp/hadolint
    if [ ! -x "$DL" ]; then
        curl -L -o "$DL" https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64
        chmod +x "$DL"
    fi
fi
exec "$DL" "$@"
