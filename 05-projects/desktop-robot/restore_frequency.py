"""Restore the board-advertised maximum, without overclock or thermal changes."""
from pathlib import Path


def rated_maximum(cpuinfo_max, available):
    values=[int(v) for v in available.split() if int(v)<=int(cpuinfo_max)]
    if not values:
        raise ValueError("没有可验证的额定频率")
    return max(values)


def main():
    compatible=Path('/proc/device-tree/compatible').read_bytes()
    if b'orangepi-4-pro' not in compatible:
        raise RuntimeError("此配置仅针对已验证的Orange Pi 4 Pro")
    for policy in Path('/sys/devices/system/cpu/cpufreq').glob('policy*'):
        target=rated_maximum((policy/'cpuinfo_max_freq').read_text(),
                             (policy/'scaling_available_frequencies').read_text())
        path=policy/'scaling_max_freq'
        old=path.read_text().strip()
        path.write_text(str(target))
        print(f'{policy.name}: {old} -> {path.read_text().strip()} kHz',flush=True)


if __name__=='__main__':main()
