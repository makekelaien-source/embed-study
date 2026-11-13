$ErrorActionPreference = 'Stop'
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script in Administrator PowerShell.'
}
Restart-Service SharedAccess
$manager = New-Object -ComObject HNetCfg.HNetShare
$connections = @($manager.EnumEveryConnection())
$public = @($connections | Where-Object { $manager.NetConnectionProps($_).Name -eq 'WLAN' })
$private = @($connections | Where-Object { $manager.NetConnectionProps($_).Name -eq ([string][char]0x4ee5 + [char]0x592a + [char]0x7f51) })
if ($public.Count -ne 1 -or $private.Count -ne 1) {
    throw 'Expected exactly one WLAN and one Ethernet connection; no changes made.'
}
$snapshot = foreach ($connection in $connections) {
    $props = $manager.NetConnectionProps($connection)
    $config = $manager.INetSharingConfigurationForINetConnection($connection)
    [pscustomobject]@{ Name=$props.Name; Shared=$config.SharingEnabled; Type=$config.SharingConnectionType }
}
$snapshot | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $PSScriptRoot ('.local/sharing-before-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.json'))
foreach ($connection in @($public[0], $private[0])) {
    $config = $manager.INetSharingConfigurationForINetConnection($connection)
    if ($config.SharingEnabled) { $config.DisableSharing() }
}
$manager.INetSharingConfigurationForINetConnection($public[0]).EnableSharing(0)
$manager.INetSharingConfigurationForINetConnection($private[0]).EnableSharing(1)
Start-Sleep -Seconds 3
$ethernetName = $manager.NetConnectionProps($private[0]).Name
$addressOutput = netsh interface ipv4 show config name="$ethernetName"
$addressOutput | Out-Host
if (($addressOutput -join "`n") -notmatch "192\.168\.137\.1(?![0-9])") {
    throw "ICS did not assign 192.168.137.1; sharing is not verified. Send this output to the assistant."
}
Get-Service SharedAccess | Format-Table Status, Name
Write-Output 'Host address verified. The assistant must still check board DHCP and SSH.'
