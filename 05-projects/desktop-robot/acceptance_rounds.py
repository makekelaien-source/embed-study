"""Offline acceptance bookkeeping; never runs models, hardware, or shutdown.

Human judgments and acoustic evidence must be supplied by the operator. This
checks completeness and arithmetic, not the truth of an external measurement.
CLI: python acceptance_rounds.py PLAN.json ROUNDS.json
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

CHECKS = ("identity", "facts", "execution", "framework")
STATUSES = ("pass", "fail", "unmeasured", "blocked")
ACOUSTIC_METHODS = ("microphone_acoustic", "external_acoustic_sensor")


def plan_sha256(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _gate(status, reason):
    return {"status": status, "reason": reason}


def _combine(statuses):
    values = list(statuses)
    if not values:
        return "unmeasured"
    for status in ("fail", "blocked", "unmeasured"):
        if status in values:
            return status
    return "pass"


def _validate_plan(plan):
    if not isinstance(plan, dict) or type(plan.get("schema_version")) is not int or plan.get("schema_version") != 1 or not _text(plan.get("rubric_id")):
        raise ValueError("plan requires schema_version=1 and rubric_id")
    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("plan.tasks must be a nonempty list")
    ids, covered = set(), set()
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("task must be an object")
        for key in ("id", "language", "group", "prompt", "rubric", "kind"):
            if not _text(task.get(key)):
                raise ValueError("task requires nonempty " + key)
        if task["kind"] not in ("identity", "knowledge", "followup", "tool", "uncertainty"):
            raise ValueError("unsupported task kind")
        if task["id"] in ids:
            raise ValueError("duplicate planned id: " + task["id"])
        ids.add(task["id"])
        checks = task.get("checks")
        if (not isinstance(checks, list) or not checks or len(set(checks)) != len(checks)
                or not all(check in CHECKS for check in checks)):
            raise ValueError("task.checks must be a nonempty unique subset of " + str(CHECKS))
        covered.update(checks)
    if covered != set(CHECKS):
        raise ValueError("plan must explicitly cover identity/facts/execution/framework")
    earlier = set()
    for task in tasks:
        prerequisite = task.get("prerequisite")
        if prerequisite is not None:
            deps = prerequisite.get("task_ids") if isinstance(prerequisite, dict) else None
            if not isinstance(deps, list) or not deps or not all(dep in earlier for dep in deps):
                raise ValueError("prerequisite task_ids must refer to earlier planned tasks")
        earlier.add(task["id"])
    return tasks


def _blocker(blocker):
    if blocker is None:
        return False
    if not isinstance(blocker, dict) or not all(_text(blocker.get(k)) for k in ("reason", "evidence")):
        raise ValueError("blocker needs reason and evidence")
    if blocker.get("kind") == "thermal_limit":
        observed, limit = blocker.get("observed_c"), blocker.get("threshold_c")
        if not (_finite(observed) and _finite(limit) and 0 < limit <= 70 and observed >= limit):
            raise ValueError("thermal block needs real observed_c >= threshold_c, threshold <=70C")
    elif blocker.get("kind") == "missing_hardware":
        if not _text(blocker.get("component")):
            raise ValueError("missing_hardware block needs component")
    else:
        raise ValueError("only thermal_limit/missing_hardware are stop blockers")
    return True


def _judgment(value, has_blocker):
    if value is None:
        return _gate("unmeasured", "required judgment missing")
    if not isinstance(value, dict) or value.get("status") not in STATUSES:
        raise ValueError("judgment requires pass/fail/unmeasured/blocked")
    status = value["status"]
    if not _text(value.get("reason")):
        return _gate("unmeasured", "judgment reason missing")
    if status == "blocked" and not has_blocker:
        return _gate("fail", "blocked judgment lacks valid round blocker")
    if status in ("pass", "fail") and not _text(value.get("evidence")):
        return _gate("unmeasured", "review evidence missing")
    return _gate(status, value["reason"])


def _acoustic(value, has_blocker):
    if value is None:
        return _gate("unmeasured", "no acoustic measurement")
    if not isinstance(value, dict):
        raise ValueError("acoustic must be an object")
    if value.get("status") in ("unmeasured", "blocked"):
        return _judgment(value, has_blocker)
    if value.get("status") != "measured":
        return _gate("fail", "acoustic status must be measured/unmeasured/blocked")
    seconds = value.get("seconds")
    if not _finite(seconds) or not 0 <= seconds <= 2:
        return _gate("fail", "each acoustic response must be finite and within [0,2] seconds")
    if value.get("method") not in ACOUSTIC_METHODS:
        return _gate("fail", "file-ready, digital loopback and software playback timestamps are not acoustic")
    if value.get("start_event") != "user_speech_end" or value.get("end_event") != "first_substantive_audible_response":
        return _gate("fail", "must measure speech end to substantive acoustic response, not placeholder")
    if not _text(value.get("evidence")) or not _text(value.get("measurement_id")):
        return _gate("unmeasured", "acoustic evidence/measurement_id missing")
    return {"status": "pass", "reason": "reported acoustic evidence meets per-item bound", "seconds": seconds,
            "measurement_id": value["measurement_id"], "evidence": value["evidence"]}


def _task(task, result, has_blocker):
    if result is None:
        gates = {check: _gate("unmeasured", "planned item has no result") for check in task["checks"]}
        gates.update(response=_gate("unmeasured", "planned item has no result"),
                     acoustic=_gate("unmeasured", "planned item has no result"))
    else:
        if result.get("status", "completed") not in ("completed", "blocked", "unmeasured"):
            raise ValueError("unsupported result status")
        values = result.get("checks", {})
        if not isinstance(values, dict) or set(values) - set(task["checks"]):
            raise ValueError("result checks must match applicable planned checks")
        gates = {check: _judgment(values.get(check), has_blocker) for check in task["checks"]}
        blocked = result.get("status") == "blocked"
        if blocked:
            gates["response"] = _gate("blocked" if has_blocker else "fail", "item blocked by reported safety/hardware condition")
        elif result.get("status") == "unmeasured":
            gates["response"] = _gate("unmeasured", "item explicitly not measured")
        elif not _text(result.get("response")):
            gates["response"] = _gate("unmeasured", "actual response missing")
        elif result.get("errors") != [] or result.get("guessed") is not False:
            gates["response"] = _gate("fail", "zero tolerance: errors/guessing must explicitly be []/false")
        elif result.get("answer_kind") not in ("answer", "refusal"):
            gates["response"] = _gate("fail", "placeholder/guess/unspecified answer kind cannot pass")
        elif result["answer_kind"] == "refusal" and task["kind"] in ("knowledge", "followup"):
            gates["response"] = _gate("fail", "refusal is not a correct knowledge/followup answer")
        else:
            gates["response"] = _gate("pass", "substantive response declared; correctness judged separately")
        gates["acoustic"] = _acoustic(result.get("acoustic"), has_blocker)
    return {"id": task["id"], "language": task["language"], "group": task["group"], "gates": gates,
            "status": _combine(g["status"] for g in gates.values())}


def evaluate(plan, rounds):
    """Return latest-round verdict and all historical gates; malformed contracts raise ValueError."""
    tasks = _validate_plan(plan)
    digest = plan_sha256(plan)
    if not isinstance(rounds, list) or len(rounds) > 3:
        raise ValueError("rounds must be a list: initial + at most two improvement rounds")
    reports, seen_measurements = [], set()
    blocked = False
    for index, row in enumerate(rounds):
        if blocked:
            raise ValueError("no further stress rounds after safety/hardware block")
        if not isinstance(row, dict) or type(row.get("index")) is not int or row.get("index") != index:
            raise ValueError("round indices must be consecutive 0,1,2")
        if row.get("plan_sha256") != digest:
            raise ValueError("frozen rubric/plan hash mismatch")
        blocked = _blocker(row.get("blocker"))
        results = row.get("results")
        if not isinstance(results, list):
            raise ValueError("each round requires results list")
        by_id, planned = {}, {task["id"] for task in tasks}
        for result in results:
            if not isinstance(result, dict) or result.get("id") not in planned:
                raise ValueError("unknown/non-object result")
            if result["id"] in by_id:
                raise ValueError("duplicate result id")
            by_id[result["id"]] = result
        items = [_task(task, by_id.get(task["id"]), blocked) for task in tasks]
        for task, item in zip(tasks, items):
            deps = task.get("prerequisite", {}).get("task_ids", [])
            if deps and item["status"] != "blocked":
                has_context = _text(by_id.get(task["id"], {}).get("context_evidence"))
                executed = all(_text(by_id.get(dep, {}).get("response"))
                               and by_id[dep].get("status", "completed") == "completed" for dep in deps)
                if not has_context or not executed:
                    item["gates"]["response"] = _gate("unmeasured", "followup requires executed prerequisites and actual context evidence")
                    item["status"] = _combine(g["status"] for g in item["gates"].values())
        for item in items:
            acoustic = item["gates"]["acoustic"]
            if acoustic["status"] == "pass":
                mid = acoustic["measurement_id"]
                if mid in seen_measurements:
                    acoustic.update(status="fail", reason="acoustic measurement reused across items/rounds")
                    item["status"] = _combine(g["status"] for g in item["gates"].values())
                seen_measurements.add(mid)
        gates = {check: _combine(item["gates"][check]["status"] for item in items if check in item["gates"])
                 for check in CHECKS + ("response", "acoustic")}
        groups = {}
        for item in items:
            key = item["language"] + "/" + item["group"]
            groups.setdefault(key, []).append(item["status"])
        status = _combine(gates.values())
        if blocked and status == "pass":
            status = "blocked"
        reports.append({"index": index, "name": ("initial", "improvement_1", "improvement_2")[index],
                        "status": status, "gates": gates, "items": items,
                        "groups": {k: _combine(v) for k, v in groups.items()},
                        "coverage": {"planned": len(tasks), "reported": len(by_id), "missing": sorted(planned-set(by_id))},
                        "blocker": row.get("blocker")})
    overall = reports[-1]["status"] if reports else "unmeasured"
    return {"schema_version": 1, "rubric_id": plan["rubric_id"], "plan_sha256": digest,
            "overall": overall, "rounds": reports, "improvements_used": max(0, len(reports)-1),
            "may_improve": overall != "pass" and not blocked and len(reports) < 3,
            "evidence_note": "Validates supplied records only; acoustic capture and human judgments require independent review."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("rounds", type=Path)
    args = parser.parse_args(argv)
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
        rounds = json.loads(args.rounds.read_text(encoding="utf-8-sig"))
        report = evaluate(plan, rounds)
    except (ValueError, OSError, TypeError) as exc:
        print(json.dumps({"overall": "fail", "contract_error": str(exc)}, ensure_ascii=True))
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False))
    return 0 if report["overall"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
