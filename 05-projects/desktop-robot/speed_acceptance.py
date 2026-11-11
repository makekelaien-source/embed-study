"""Offline benchmark/soak. Run in a temporary network namespace for proof."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--duration",type=float,default=1800)
    p.add_argument("--output",type=Path,required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    network={}
    for label,cmd in [("addresses",["ip","-br","addr"]),("routes",["ip","route"]),
                      ("ipv6_routes",["ip","-6","route"])]:
        network[label]=subprocess.check_output(cmd,text=True)
    # Require isolation rather than assuming a disconnected Ethernet is enough.
    import socket
    network["interfaces"]=socket.if_nameindex()
    if any(name in ("wlan0","end0","eth0") for _,name in network["interfaces"]) or network["routes"].strip():
        raise RuntimeError("未处于无外网接口/路由的隔离网络，请通过 offline-speed-check.sh 启动")
    (args.output/"network-start.json").write_text(json.dumps(network,indent=2),encoding="utf8")
    stop=threading.Event()
    def thermal():
        with (args.output/"thermal.jsonl").open("w") as f:
            while not stop.is_set():
                row={"monotonic":time.monotonic()}
                for zone in Path("/sys/class/thermal").glob("thermal_zone*"):
                    try:row[zone.name+":"+(zone/"type").read_text().strip()]=int((zone/"temp").read_text())/1000
                    except OSError:pass
                for policy in Path("/sys/devices/system/cpu/cpufreq").glob("policy*"):
                    try:row[policy.name+"_khz"]=int((policy/"scaling_cur_freq").read_text())
                    except OSError:pass
                f.write(json.dumps(row)+"\n");f.flush();stop.wait(5)
    sampler=threading.Thread(target=thermal)
    sampler.start()
    started=time.monotonic()
    cycles=[]
    try:
        index=0
        while index<2 or time.monotonic()-started<args.duration:
            language="zh" if index%2==0 else "en"
            label=f"{index:02d}-{language}"
            with (args.output/(label+".log")).open("w") as f:
                result=subprocess.run([sys.executable,"run_fast.py","--bench","--language",language,
                    "--gap","8","--metrics",str(args.output/(label+".jsonl")),
                    "--input-cache",str(args.output/"inputs"),
                    "--output-dir",str(args.output/label)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
            cycles.append({"label":label,"exit":result.returncode,"elapsed_s":time.monotonic()-started})
            (args.output/"progress.json").write_text(json.dumps(cycles,indent=2),encoding="utf8")
            if result.returncode:
                raise RuntimeError(f"{label} 失败，退出码 {result.returncode}")
            index+=1
    finally:
        stop.set();sampler.join()
        (args.output/"result.json").write_text(json.dumps({"cycles":cycles,
            "elapsed_s":time.monotonic()-started,"network_end":subprocess.check_output(["ip","-br","addr"],text=True)},indent=2),encoding="utf8")


if __name__ == "__main__":
    main()
