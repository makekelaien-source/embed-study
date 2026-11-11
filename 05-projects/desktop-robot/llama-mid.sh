#!/bin/sh
# llama-server 绑 CPU4-7（2 个 A76 大核 + 2 个 A55 小核）
exec taskset -c 4-7 "$HOME/desktop-robot/.local/llama/llama-server" "$@"
