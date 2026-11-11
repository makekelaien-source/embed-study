"""Summarize measured latency only; content quality needs a separate review."""
import argparse
import json
import math
from pathlib import Path
import statistics


def stats(rows):
    values=sorted(r["response_s"] for r in rows)
    if not values:
        return {"n":0}
    return {"n":len(values),"median_s":statistics.median(values),
            "p90_s":values[math.ceil(.9*len(values))-1],"max_s":max(values),
            "first_s":rows[0]["response_s"],
            "median_prompt_ms":statistics.median(r.get("llm",{}).get("prompt_ms",0) for r in rows),
            "content_quality":"not_scored"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("root",type=Path)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    report={}
    groups={"zh":[],"en":[]}
    for path in sorted(args.root.rglob("*.jsonl")):
        rows=[json.loads(line) for line in path.read_text(encoding="utf8").splitlines() if line.strip()]
        rows=[r for r in rows if "response_s" in r]
        if rows:
            report[str(path.relative_to(args.root))]=stats(rows)
            if path.stem.endswith("-zh"):groups["zh"].extend(rows)
            elif path.stem.endswith("-en"):groups["en"].extend(rows)
    for language,rows in groups.items():
        if rows:report["aggregate-"+language]=stats(rows)
    thermal=args.root/"thermal.jsonl"
    if thermal.exists():
        samples=[json.loads(line) for line in thermal.read_text().splitlines()]
        report["thermal"]={"n":len(samples),"duration_s":samples[-1]["monotonic"]-samples[0]["monotonic"],
            "cpu_peak_c":max(v for row in samples for k,v in row.items() if "thermal_zone" in k and "cpu" in k)}
    if args.output:args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__":main()
