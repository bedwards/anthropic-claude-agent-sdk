#!/bin/bash
# Wrapper for anim2rbx that sets the correct library path for assimp@5
# This is needed because assimp@5 is keg-only in Homebrew

export DYLD_LIBRARY_PATH="/usr/local/opt/assimp@5/lib:$DYLD_LIBRARY_PATH"
exec anim2rbx "$@"
