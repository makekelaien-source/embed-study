#!/bin/bash
# 汇总三组优化实验日志的退出码与延迟分布（在板上运行）
cd ~/desktop-robot/.local || exit 1
for f in zhll enbig2 enmid4; do
  echo "== $f =="
  grep -h EXIT bench-opi-$f.log 2>/dev/null
  grep 文件输入到音频就绪 bench-opi-$f.log 2>/dev/null | grep -oE '[0-9.]+s$' | tr -d s | sort -n | awk '{v[NR]=$1} END {if (NR==0) {print "n=0"; exit} print "n="NR; print "med="v[int((NR+1)/2)]; print "p90="v[int(NR*0.9)+1]; print "min="v[1]; print "max="v[NR]}'
done
