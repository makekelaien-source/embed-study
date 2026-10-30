# Align PowerShell native-process decoding with UTF-8 study programs.
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$global:OutputEncoding = [Console]::OutputEncoding
