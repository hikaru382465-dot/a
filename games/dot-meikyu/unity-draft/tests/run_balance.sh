#!/bin/sh
# 強さの釣り合いを見る：sh tests/run_balance.sh   （mono と mcs が必要）
cd "$(dirname "$0")/.." || exit 1
export LANG=C.UTF-8 LC_ALL=C.UTF-8
mcs -out:tests/balance.exe Assets/Scripts/Core/*.cs tests/Program.cs tests/PlayerChecks.cs tests/SimChecks.cs tests/EffectChecks.cs tests/Balance.cs 2>&1 | grep -v warning
mono tests/balance.exe ../design balance
rm -f tests/balance.exe
