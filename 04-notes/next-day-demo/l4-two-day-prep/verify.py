"""Teacher-only preflight for lesson plans; never supplies student cores."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_name("validation.json")
FLAGS = ["-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic"]
DEMOS = [
    ("04-notes/next-day-demo/l4-2026-11-12/pointer-demo.c", "a=7,26 b=7,25\n"),
    ("04-notes/next-day-demo/l4-2026-11-12/copy-demo.c", "inside=99\nafter_value=25\nafter_pointer=99\n"),
    ("04-notes/next-day-demo/l4-2026-11-12/layout-demo.c", None),
    ("04-notes/next-day-demo/l4-2026-11-13/width-demo.c", "bits=8,16,32 values=0,1000,4096\n"),
    ("04-notes/next-day-demo/l4-2026-11-13/array-demo.c", "first=10 second=27 read=27\n"),
    ("04-notes/next-day-demo/l4-2026-11-13/multi-mask-demo.c", "partial=1,0\ncomplete=1,1\n"),
]
CORES = [
    "03-code_codex/l4-switch-at.c",
    "03-code_codex/l4-2026-11-12/sample-set-value.c",
    "03-code_codex/l4-2026-11-12/sample-refresh.c",
    "03-code_codex/l4-2026-11-13/count-flagged.c",
    "03-code_codex/l4-2026-11-13/sample-set-batch.c",
]
HARNESSES = [
    "03-code_codex/l4-switch-at-main.c",
    "03-code_codex/l4-2026-11-12/sample-main.c",
    "03-code_codex/l4-2026-11-13/filter-main.c",
]

def command(argv):
    return subprocess.run(argv, cwd=ROOT, text=True, encoding="utf-8", errors="replace",
                          capture_output=True, timeout=20)

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

report = {"status": "running", "teacher_preparation_only": True,
          "student_functionality_tested": False,
          "created_at": datetime.now(timezone.utc).isoformat(),
          "compiler": command(["gcc", "--version"]).stdout.splitlines()[0],
          "compile_flags": FLAGS, "demos": [], "harnesses": [], "cores": []}
with tempfile.TemporaryDirectory(prefix="l4-two-day-preflight-") as temp:
    work = Path(temp)
    for index, (name, expected) in enumerate(DEMOS):
        source = ROOT / name
        exe = work / f"demo-{index}.exe"
        built = command(["gcc", *FLAGS, str(source), "-o", str(exe)])
        require(built.returncode == 0 and not built.stderr, f"Build failed {name}: {built.stderr}")
        ran = command([str(exe)])
        require(ran.returncode == 0, f"Run failed {name}")
        if expected is not None:
            require(ran.stdout == expected, f"Output mismatch {name}: {ran.stdout!r}")
        else:
            found = re.fullmatch(r"size=(\d+) align=(\d+) offsets=(\d+),(\d+),(\d+)\n", ran.stdout)
            require(found is not None, "Invalid layout observation")
            size, alignment, first, second, third = map(int, found.groups())
            require(first == 0 and 0 < second < third < size and alignment > 0,
                    "Invalid observed member layout")
        report["demos"].append({"path": name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                                "compile_exit": built.returncode, "run_exit": ran.returncode,
                                "stdout": ran.stdout, "passed": True})
    for index, name in enumerate(HARNESSES):
        source = ROOT / name
        built = command(["gcc", *FLAGS, "-c", str(source), "-o", str(work / f"harness-{index}.o")])
        require(built.returncode == 0 and not built.stderr, f"Harness compile failed {name}: {built.stderr}")
        report["harnesses"].append({"path": name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                                    "compile_only": True, "passed": True})
    # The lesson teaches that const rejects this write. Failure is the expected observation.
    negative = work / "const-write.c"
    negative.write_text("struct Reading { int value; };\nvoid bad(const struct Reading *p) { p->value = 1; }\n", encoding="utf-8")
    failed = command(["gcc", *FLAGS, "-c", str(negative), "-o", str(work / "negative.o")])
    require(failed.returncode != 0 and "error:" in failed.stderr, "const write was not rejected")
    report["const_write_rejected"] = {"passed": True, "compiler_exit": failed.returncode}
for name in CORES:
    source = ROOT / name
    require(source.is_file(), f"Missing student core: {name}")
    require(source.stat().st_size == 0, f"Student already wrote {name}; preserve it and revise preflight")
    report["cores"].append({"path": name, "bytes": 0, "preserved_blank": True})
report["lessons"] = []
for day in ["2026-11-12", "2026-11-13"]:
    source = ROOT / f"04-notes/lesson-{day}.md"
    body = source.read_text(encoding="utf-8")
    schedule = body.split("## 二、", 1)[1].split("## 三、", 1)[0]
    minutes = [int(x) for x in re.findall(r"^\|\s*\d+\s*\|[^\n]*?\|\s*(\d+)\s*\|", schedule, re.MULTILINE)]
    require(sum(minutes) == 300, f"Budget mismatch {day}: {minutes}")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", body):
        if "://" in target or target.startswith("#"):
            continue
        path = (source.parent / target.split("#", 1)[0]).resolve()
        if path == OUT.resolve():
            continue
        require(path.is_file(), f"Broken lesson link {day}: {target}")
    report["lessons"].append({"path": str(source.relative_to(ROOT)).replace("\\", "/"),
                               "minutes": sum(minutes), "units": len(minutes),
                               "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "links_verified": True})
report["status"] = "passed"
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": report["status"], "teacher_demos_run": len(DEMOS),
                  "harnesses_compile_only": len(HARNESSES), "blank_student_cores": len(CORES),
                  "const_write_rejected": True, "lesson_minutes": [x["minutes"] for x in report["lessons"]]}, ensure_ascii=False))
