"""Use the measured board profile without hiding the actual robot/bench CLI."""
import json
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def profile_arguments(profile,language,bench):
    settings=dict(profile["common"])
    settings.update(profile.get("language_overrides",{}).get(language,{}))
    if not bench:
        settings.update(profile["microphone"])
    flags=[]
    for key,value in settings.items():
        flags += ["--"+key.replace("_","-"),str(value)]
    return flags


def main():
    args = sys.argv[1:]
    bench = "--bench" in args
    if bench:
        args.remove("--bench")
    profile = json.loads((ROOT/"fast-profile.json").read_text(encoding="utf8"))
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument("--language",choices=("zh","en"),default="zh")
    known,_=parser.parse_known_args(args)
    flags=profile_arguments(profile,known.language,bench)
    command = [sys.executable,str(ROOT/("bench.py" if bench else "robot.py")),*flags,*args]
    print("启动配置：",json.dumps(command,ensure_ascii=False),flush=True)
    raise SystemExit(subprocess.call(command,cwd=ROOT))


if __name__ == "__main__":
    main()
