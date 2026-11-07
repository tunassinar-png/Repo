#!/bin/bash
# Install a speech recogniser that works in the cloud container (Hugging Face and the OpenAI
# model host are blocked, but PyPI and GitHub release assets are reachable).
#
#   bash asr_setup.sh [turbo|large-v3|small|medium] DEST_DIR      # default: turbo
#
# turbo (564 MB) = Whisper large-v3-turbo: fast, very good Malay. large-v3 (1.07 GB) is the
# second opinion for doubtful words (it dropped words in one phrase, turbo looped in another;
# agreement of both = trustworthy). DEST_DIR must be a new, empty directory.
set -e
M="${1:-turbo}"; D="${2:?usage: asr_setup.sh MODEL DEST_DIR}"
pip install -q sherpa-onnx scipy numpy 2>&1 | tail -1 || true
mkdir -p "$D" && cd "$D"
curl -sSL -m 900 -o model.tar.bz2 "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-$M.tar.bz2"
tar -xjf model.tar.bz2 && rm model.tar.bz2
ls "$D"/sherpa-onnx-whisper-$M
