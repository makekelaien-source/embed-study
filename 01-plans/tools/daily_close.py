"""Run a prepared daily-close plan under one deadline; delete only after final push."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

import study_book
from close_network import NetworkError, NetworkSession, _redact


class CloseError(ValueError):
    pass


def run_close(root, plan, budget_seconds=300, resume=False):
    """Return a receipt, including a resumable pending status on any failed gate.

    Preparation belongs in the lesson: the explicit manifest, complete intro,
    next lesson and validation commands must already exist when this is called.
    """
    root = Path(root).resolve()
    started = time.monotonic()
    budget = float(budget_seconds)
    deadline = started + max(0, budget) - min(3, max(0, budget) * .05)
    preparation_seconds = 0
    state = {"status": "pending_validation", "date": plan.get("date"), "phase": "preflight"}
    state_path = None
    network = None

    def remaining():
        value = deadline - time.monotonic()
        if value <= 0:
            raise CloseError("Daily close deadline reached; originals remain on disk")
        return value

    def git(*args):
        result = subprocess.run(["git", *args], cwd=root, capture_output=True,
                                timeout=min(20, remaining()),
                                env=os.environ | {"GIT_TERMINAL_PROMPT": "0",
                                                  "GCM_INTERACTIVE": "never", "GCM_GUI_PROMPT": "0"})
        if result.returncode:
            raise CloseError("Local Git operation failed: " + _redact(result.stderr.decode("utf-8", "replace")))
        return result.stdout

    def save():
        state["execution_seconds"] = round(time.monotonic() - started, 3)
        state["preparation_seconds_before_command"] = round(preparation_seconds, 3)
        state["elapsed_seconds"] = round(preparation_seconds + time.monotonic() - started, 3)
        state["clock_basis"] = "resume_attempt" if resume else (
            "classroom_stop" if plan.get("classroom_ended_at") else "command_start_only")
        state["budget_seconds"] = budget
        state["within_budget"] = state["elapsed_seconds"] <= budget
        if network is not None:
            state["network_events"] = list(network.events)
        if state_path is not None:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = state_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temporary.replace(state_path)

    def checked_sources():
        if not state.get("book_built") and study_book.digest(intro_path.read_bytes()) != state["intro_sha256"]:
            raise CloseError("Prepared intro changed; review before resuming")
        for name, sha in state["source_hashes"].items():
            if name == book and state.get("book_built"):
                wanted = state["book_sha256"]
            else:
                wanted = sha
            path = study_book.safe(root, name)
            if not path.is_file() or study_book.digest(path.read_bytes()) != wanted:
                raise CloseError("Source changed; no cleanup permitted: " + name)

    def no_unrelated_index():
        staged = {p.decode("utf-8") for p in git("diff", "--cached", "--name-only", "-z").split(b"\0") if p}
        if staged - set(stage_paths):
            raise CloseError("Unrelated staged work must stay outside daily close")

    def run_job(job, restored, work):
        commands = job.get("commands", [])
        if not commands or not all(isinstance(command, list) and command for command in commands):
            raise CloseError("Validation requires explicit argv command lists")
        output = ""
        local_deadline = min(deadline, time.monotonic() + float(job.get("timeout_seconds", 40)))
        for index, command in enumerate(commands):
            argv = [str(arg).replace("{root}", str(root)).replace("{restored}", str(restored))
                    .replace("{work}", str(work)) for arg in command]
            if Path(argv[0]).stem.lower() == "git":
                raise CloseError("Git operations belong to the single coordinator, not validation jobs")
            timeout = min(remaining(), local_deadline - time.monotonic())
            if timeout <= 0:
                raise CloseError("Validation deadline reached: " + job["name"])
            result = subprocess.run(argv, cwd=restored, input=job.get("stdin", "") if index == len(commands) - 1 else "",
                                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                                    timeout=timeout, env=os.environ | {"PYTHONIOENCODING": "utf-8"})
            if result.returncode:
                raise CloseError("Validation failed: " + job["name"] + ": " + _redact(result.stderr))
            output = result.stdout
        if "expected_stdout" in job and output != job["expected_stdout"]:
            raise CloseError("Validation output mismatch: " + job["name"])
        return {"name": job["name"], "passed": True, "stdout": _redact(output)}

    def parallel(jobs, restored, work, include_network=False):
        def ready_network():
            network.choose_route()
            return network.verify_visibility(visibility)

        results = []
        executor = ThreadPoolExecutor(max_workers=4)
        futures = {executor.submit(run_job, job, restored, work): job["name"] for job in jobs}
        if include_network:
            futures[executor.submit(ready_network)] = "network"
        try:
            for future in as_completed(futures, timeout=remaining()):
                value = future.result()
                if futures[future] == "network":
                    state["visibility_verified"] = value
                else:
                    results.append(value)
            return results
        finally:
            # Each worker shares the deadline. Reap its timed-out process before
            # returning, otherwise Windows can keep the workspace/temp dir open.
            executor.shutdown(wait=True, cancel_futures=True)

    @contextmanager
    def writer_lock():
        nonlocal state_path
        value = git("rev-parse", "--git-path", "study-close.lock").decode().strip()
        path = Path(value) if Path(value).is_absolute() else root / value
        try:
            with path.open("x", encoding="utf-8") as stream:
                stream.write(str(os.getpid()))
        except FileExistsError:
            # An unsuccessful contender must not replace the active writer's receipt.
            state_path = None
            raise CloseError("Another close writer owns the repository lock") from None
        try:
            yield
        finally:
            path.unlink(missing_ok=True)

    try:
        if plan.get("classroom_ended_at") and not resume:
            stopped = datetime.fromisoformat(plan["classroom_ended_at"])
            if stopped.tzinfo is None:
                raise CloseError("classroom_ended_at requires a timezone")
            preparation_seconds = max(0, (datetime.now(timezone.utc) - stopped).total_seconds())
            available = max(0, budget - preparation_seconds)
            deadline = started + available - min(3, available * .05)
            remaining()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(plan.get("date", ""))):
            raise CloseError("Plan needs an ISO date")
        book = str(plan["book"]).replace("\\", "/")
        study_book.safe(root, book)
        visibility = plan.get("visibility", "private")
        if visibility not in ("private", "public"):
            raise CloseError("Plan needs explicit authorized visibility")
        manifest = plan["manifest"]
        if not isinstance(manifest, list) or not manifest:
            raise CloseError("Plan needs a nonempty explicit manifest")
        names = [item["path"] for item in manifest]
        if len(set(name.casefold() for name in names)) != len(names):
            raise CloseError("Duplicate manifest source")
        if any(Path(name).suffix in (".c", ".py") for name in names) and not plan.get("restore_checks"):
            raise CloseError("Program sources require representative offline execution checks")
        intro_path = Path(plan["intro"])
        if not intro_path.is_absolute():
            intro_path = study_book.safe(root, plan["intro"])
        for item in manifest:
            study_book.safe(root, item["path"])
            if item.get("cleanup", False):
                study_book.check_cleanup_path(item["path"])
                if item["path"] == book or item["path"].startswith("03-code_codex/shared-text/"):
                    raise CloseError("Book and continuing modules are protected")
        stage_paths = sorted(set(plan.get("stage_paths", names) + names + [book, ".gitattributes"]))
        for name in stage_paths:
            study_book.safe(root, name)
        digest = study_book.digest(json.dumps(plan, sort_keys=True, ensure_ascii=False).encode())
        value = git("rev-parse", "--git-path", "study-close/" + plan["date"] + ".json").decode().strip()
        state_path = Path(value) if Path(value).is_absolute() else root / value
        with writer_lock():
            if state_path.exists():
                prior = json.loads(state_path.read_text(encoding="utf-8"))
                if not resume or prior.get("plan_sha256") != digest:
                    state_path = None
                    raise CloseError("Existing close receipt requires --resume with the same plan")
                state = prior
                if state.get("status") == "complete":
                    save()
                    return state
            else:
                if resume:
                    raise CloseError("No saved close to resume")
                for name in plan.get("required_paths", []):
                    if not study_book.safe(root, name).is_file():
                        raise CloseError("Prepare next-lesson artifact before closing: " + name)
                state.update(plan_sha256=digest, source_hashes={},
                             intro_sha256=study_book.digest(intro_path.read_bytes()))
                for name in sorted(set(names + plan.get("required_paths", []) + plan.get("stage_paths", []))):
                    path = study_book.safe(root, name)
                    if not path.is_file():
                        raise CloseError("Prepare source before closing: " + name)
                    state["source_hashes"][name] = study_book.digest(path.read_bytes())
                state["started_at"] = datetime.now(timezone.utc).isoformat()
            network = NetworkSession(root, deadline_seconds=remaining())
            no_unrelated_index()
            checked_sources()
            if not state.get("snapshot"):
                state["phase"] = "parallel_preflight"
                save()
                with tempfile.TemporaryDirectory(prefix="study-preflight-") as directory:
                    state["checks"] = parallel(plan.get("checks", []), root, Path(directory), include_network=True)
                checked_sources()
                attributes = study_book.safe(root, ".gitattributes")
                raw = attributes.read_bytes() if attributes.exists() else b""
                additions = ["/" + name + " -text" for name in names if ("/" + name + " -text").encode() not in raw]
                if additions:
                    attributes.write_bytes(raw.rstrip(b"\r\n") + b"\n" + "\n".join(additions).encode() + b"\n")
                if ".gitattributes" in state["source_hashes"]:
                    state["source_hashes"][".gitattributes"] = study_book.digest(attributes.read_bytes())
                git("add", "--", *stage_paths)
                git("add", "--renormalize", "--", *names)
                no_unrelated_index()
                checked_sources()
                # Check the index tree before creating/uploading a snapshot. This
                # catches CRLF/filter differences on already tracked files too.
                index_tree = git("write-tree").decode().strip()
                study_book.snapshot_sources(root, {"snapshot_commit": index_tree,
                    "sources": [{"path": name, "sha256": state["source_hashes"][name]} for name in names]})
                if git("diff", "--cached", "--name-only").strip():
                    git("commit", "-q", "-m", "Preserve daily originals " + plan["date"])
                state["snapshot"] = git("rev-parse", "HEAD").decode().strip()
                state["phase"] = "snapshot_upload"
                save()
            if state.get("final_commit"):
                if git("rev-parse", "HEAD").decode().strip() != state["final_commit"]:
                    raise CloseError("HEAD changed after final commit; review before resume")
            else:
                if git("rev-parse", "HEAD").decode().strip() != state["snapshot"]:
                    raise CloseError("HEAD changed after original snapshot; review before resume")
                state["phase"] = "snapshot_upload"
                save()
                network.push_verified(state["snapshot"])
                state["snapshot_remote_verified"] = True
                checked_sources()
                if not state.get("book_built"):
                    study_book.build(root, book, plan["date"], state["snapshot"], manifest,
                                     intro_path.read_text(encoding="utf-8-sig"))
                    state["book_built"] = True
                    state["book_sha256"] = study_book.digest(study_book.safe(root, book).read_bytes())
                    save()
                data = study_book.verify(root, book)
                state["phase"] = "restore_validation"
                save()
                if not state.get("restore_verified"):
                    with tempfile.TemporaryDirectory(prefix="study-offline-") as directory:
                        work = Path(directory).resolve()
                        restored = work / "restored"
                        restored.mkdir()
                        for item in data["sources"]:
                            target = study_book.safe(restored, item["path"])
                            target.parent.mkdir(parents=True, exist_ok=True)
                            raw = base64.b64decode(item["bytes_b64"], validate=True)
                            with target.open("xb") as stream:
                                stream.write(raw)
                            if study_book.digest(target.read_bytes()) != item["sha256"]:
                                raise CloseError("Offline recovery checksum mismatch")
                        state["restore_checks"] = parallel(plan.get("restore_checks", []), restored, work)
                    state.update(restore_verified=True, restored_sources=len(data["sources"]))
                    save()
                checked_sources()
                state["phase"] = "final_commit"
                save()
                cleanup = [item["path"] for item in manifest if item.get("cleanup", False)]
                # Stage deletion only. Originals remain on disk through BOTH uploads.
                git("add", "--", *[name for name in stage_paths if name not in cleanup])
                if cleanup:
                    git("update-index", "--force-remove", "--", *cleanup)
                no_unrelated_index()
                git("commit", "-q", "-m", "Archive verified daily study book " + plan["date"])
                state["final_commit"] = git("rev-parse", "HEAD").decode().strip()
                state["phase"] = "final_upload"
                save()
            checked_sources()
            network.push_verified(state["final_commit"])
            state["phase"] = "cleanup_gate"
            save()
            if network.remote_head() != state["final_commit"]:
                raise NetworkError("Final remote HEAD changed; originals retained", retryable=False)
            state["visibility_verified"] = network.verify_visibility(visibility)
            data = study_book.verify(root, book)
            study_book.snapshot_sources(root, data)
            git("merge-base", "--is-ancestor", state["snapshot"], state["final_commit"])
            if git("show", state["final_commit"] + ":" + book) != study_book.safe(root, book).read_bytes():
                raise CloseError("Final remote commit does not contain the verified local book")
            checked_sources()
            selected = [item for item in data["sources"] if item["cleanup"]]
            # Check ALL candidates before the first unlink; repeat each check against
            # concurrent editor saves. Source bytes are also in the verified book.
            for item in selected:
                path = study_book.safe(root, item["path"])
                if study_book.digest(path.read_bytes()) != item["sha256"]:
                    raise CloseError("Concurrent source edit; originals retained")
            remaining()
            state["cleaned_sources"] = []
            for item in selected:
                path = study_book.safe(root, item["path"])
                if study_book.digest(path.read_bytes()) != item["sha256"]:
                    raise CloseError("Concurrent source edit; cleanup stopped")
                path.unlink()
                state["cleaned_sources"].append(item["path"])
            state.update(status="complete", phase="complete", remote_main=state["final_commit"])
            state.pop("error", None)
            save()
            return state
    except (CloseError, NetworkError, OSError, ValueError, KeyError,
            subprocess.TimeoutExpired, TimeoutError) as error:
        state["status"] = "pending_sync" if isinstance(error, NetworkError) else "pending_validation"
        state["error"] = _redact(str(error))
        save()
        return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="Prepared JSON plan; local paths and explicit file manifest")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--budget-seconds", type=float, default=300)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8-sig"))
    result = run_close(args.root, plan, args.budget_seconds, resume=args.resume)
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["status"] == "complete" else 2)


if __name__ == "__main__":
    main()
