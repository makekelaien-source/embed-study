#!/bin/bash
# 优化对比实验：1) 中文换 zh-ll 音色；2) 英文 llama 绑大核两种配置。各 15 轮。
cd ~/desktop-robot || exit 1
PY=.venv/bin/python

echo "=== ZHLL start $(date -u +%FT%TZ) ===" >> .local/bench-opi-zhll.log
$PY bench.py --language zh --voice zh-ll-0 >> .local/bench-opi-zhll.log 2>&1
echo "ZHLL_EXIT=$?" >> .local/bench-opi-zhll.log

echo "=== ENBIG2 start $(date -u +%FT%TZ) ===" >> .local/bench-opi-enbig2.log
$PY bench.py --language en --server .local/llama-big.sh --threads 2 >> .local/bench-opi-enbig2.log 2>&1
echo "ENBIG2_EXIT=$?" >> .local/bench-opi-enbig2.log

echo "=== ENMID4 start $(date -u +%FT%TZ) ===" >> .local/bench-opi-enmid4.log
$PY bench.py --language en --server .local/llama-mid.sh --threads 4 >> .local/bench-opi-enmid4.log 2>&1
echo "ENMID4_EXIT=$?" >> .local/bench-opi-enmid4.log

echo "BENCH2_ALL_DONE $(date -u +%FT%TZ)" >> .local/bench-opi-enmid4.log
