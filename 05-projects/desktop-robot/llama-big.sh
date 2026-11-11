#!/bin/sh
# llama-server 只绑 2 个 A76 大核（实测本板 CPU6-7 为 A76 @2.0GHz）
exec taskset -c 6-7 "$HOME/desktop-robot/.local/llama/llama-server" "$@"
