#!/bin/sh
# Unityが無くても、決まりを確認する：sh tests/run_tests.sh   （mono と mcs が必要）
cd "$(dirname "$0")/.." || exit 1
export LANG=C.UTF-8 LC_ALL=C.UTF-8
mcs -out:tests/check.exe Assets/Scripts/Core/*.cs tests/Program.cs tests/PlayerChecks.cs tests/SimChecks.cs tests/EffectChecks.cs && mono tests/check.exe ../design
rm -f tests/check.exe
