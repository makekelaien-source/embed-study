"""Bounded network routing without real Internet or credential disclosure."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "close_network.py"


def load_module():
    if not MODULE_PATH.exists():
        return None
    spec = importlib.util.spec_from_file_location("close_network_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CloseNetworkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="close-network-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-b", "main", str(self.root)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.root), "remote", "add", "origin", "https://github.com/example/study.git"], check=True, capture_output=True)
        self.module = load_module()

    def session(self, **kwargs):
        self.assertIsNotNone(self.module, "bounded close-network helper is not implemented")
        return self.module.NetworkSession(self.root, **kwargs)

    def test_route_environment_preserves_existing_git_config_and_disables_prompts(self):
        session = self.session()
        with patch.dict(os.environ, {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "http.extraHeader", "GIT_CONFIG_VALUE_0": "unrelated"}):
            env = session.route_env("http://127.0.0.1:7897")
        self.assertEqual(env["GIT_CONFIG_KEY_0"], "http.extraHeader")
        self.assertEqual(env["GIT_CONFIG_VALUE_0"], "unrelated")
        entries = {env[f"GIT_CONFIG_KEY_{i}"]: env[f"GIT_CONFIG_VALUE_{i}"] for i in range(1, int(env["GIT_CONFIG_COUNT"]))}
        self.assertEqual(entries["http.proxy"], "http://127.0.0.1:7897")
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(env["GCM_INTERACTIVE"], "never")

    def test_cached_successful_route_is_tried_before_other_routes(self):
        session = self.session(proxy_hints=["http://127.0.0.1:7890"])
        session.cache_path.write_text(json.dumps({"route": "http://127.0.0.1:7897"}), encoding="utf-8")
        session = self.session(proxy_hints=["http://127.0.0.1:7890"])
        attempted = []
        with patch.object(session, "_probe", side_effect=lambda route: attempted.append(route) or "a" * 40):
            chosen = session.choose_route()
        self.assertEqual(chosen, "http://127.0.0.1:7897")
        self.assertEqual(attempted, [chosen])

    def test_uncached_probes_run_concurrently_and_pick_working_route(self):
        session = self.session(proxy_hints=["http://127.0.0.1:7897"])
        entered = set()
        lock = threading.Lock()
        both_started = threading.Event()
        def probe(route):
            with lock:
                entered.add(route)
                if len(entered) == 2:
                    both_started.set()
            if not both_started.wait(1):
                raise AssertionError("probes were serialized")
            if route is None:
                raise self.module.NetworkError("direct unavailable")
            return "a" * 40
        with patch.object(session, "_probe", side_effect=probe):
            self.assertEqual(session.choose_route(), "http://127.0.0.1:7897")

    def test_failed_probes_preserve_last_success_cache(self):
        session = self.session()
        cache = {"route": "http://127.0.0.1:7897", "verified_at": "old"}
        session.cache_path.write_text(json.dumps(cache), encoding="utf-8")
        session = self.session()
        with patch.object(session, "_probe", side_effect=self.module.NetworkError("offline")):
            with self.assertRaises(self.module.NetworkError):
                session.choose_route()
        self.assertEqual(json.loads(session.cache_path.read_text()), cache)

    def test_only_local_noncredential_proxy_hints_are_accepted(self):
        session = self.session(proxy_hints=["http://user:secret@127.0.0.1:7897", "http://elsewhere.example:7897", "http://127.0.0.1:7897"])
        self.assertEqual(session.routes, ["http://127.0.0.1:7897", None])

    def test_push_changes_route_once_and_verifies_remote_sha(self):
        session = self.session(proxy_hints=["http://127.0.0.1:7897"])
        session.chosen_route = None
        session.route_selected = True
        calls = []
        def run(args, route=None, limit=6, input=None):
            calls.append((args, route, limit))
            if args[:2] == ["rev-parse", "HEAD"] or args[:2] == ["rev-parse", "refs/heads/main"]:
                return "a" * 40 + "\n"
            if args[0] == "push" and route is None:
                raise self.module.NetworkError("connection unavailable")
            if args[0] == "ls-remote":
                return "a" * 40 + " refs/heads/main\n"
            return ""
        with patch.object(session, "_run_git", side_effect=run):
            result = session.push_verified("a" * 40)
        pushes = [item for item in calls if item[0][0] == "push"]
        self.assertEqual(len(pushes), 2)
        self.assertEqual([p[1] for p in pushes], [None, "http://127.0.0.1:7897"])
        self.assertTrue(all(p[2] <= 20 for p in pushes))
        self.assertTrue(result["verified"])

    def test_remote_mismatch_is_not_retried_or_force_pushed(self):
        session = self.session(proxy_hints=["http://127.0.0.1:7897"])
        session.chosen_route = None
        session.route_selected = True
        calls = []
        def run(args, route=None, limit=6, input=None):
            calls.append(args)
            if args[0] == "rev-parse":
                return "a" * 40 + "\n"
            if args[0] == "ls-remote":
                return "b" * 40 + " refs/heads/main\n"
            return ""
        with patch.object(session, "_run_git", side_effect=run):
            with self.assertRaises(self.module.NetworkError):
                session.push_verified("a" * 40)
        self.assertEqual(sum(args[0] == "push" for args in calls), 1)
        self.assertTrue(all("--force" not in args and "reset" not in args for args in calls))

    def test_remote_head_reads_selected_route_without_pushing(self):
        session = self.session(proxy_hints=["http://127.0.0.1:7897"])
        session.chosen_route = "http://127.0.0.1:7897"
        session.route_selected = True
        calls = []
        def run(args, route=None, limit=6, input=None):
            calls.append((args, route, limit))
            return "b" * 40 + " refs/heads/main\n"
        method = getattr(session, "remote_head", None)
        self.assertIsNotNone(method, "fresh remote-head lookup is not implemented")
        with patch.object(session, "_run_git", side_effect=run):
            self.assertEqual(method(), "b" * 40)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0][0], "ls-remote")
        self.assertEqual(calls[0][1], "http://127.0.0.1:7897")
        self.assertLessEqual(calls[0][2], 6)

    def test_subprocess_timeout_is_capped_and_error_does_not_expose_credentials(self):
        session = self.session(deadline_seconds=4)
        error = subprocess.TimeoutExpired(["git"], 4, output="password=TOP_SECRET", stderr="token=TOP_SECRET")
        with patch.object(self.module.subprocess, "run", side_effect=error) as run:
            with self.assertRaises(self.module.NetworkError) as caught:
                session._run_git(["ls-remote", "origin"], limit=20)
        self.assertLessEqual(run.call_args.kwargs["timeout"], 4)
        self.assertNotIn("TOP_SECRET", str(caught.exception))

    def test_expired_deadline_stops_before_network_process(self):
        session = self.session(deadline_seconds=0)
        with patch.object(self.module.subprocess, "run") as run:
            with self.assertRaises(self.module.NetworkError):
                session._run_git(["ls-remote", "origin"])
        run.assert_not_called()

    def test_visibility_requires_boolean_and_matching_authorization(self):
        session = self.session()
        for value in [None, "false", True]:
            with self.subTest(value=value), patch.object(session, "_github_metadata", return_value={"private": value}):
                with self.assertRaises(self.module.NetworkError):
                    session.verify_visibility("public")
        with patch.object(session, "_github_metadata", return_value={"private": False}):
            self.assertTrue(session.verify_visibility("public")["verified"])
        with patch.object(session, "_github_metadata", return_value={"private": True}):
            self.assertTrue(session.verify_visibility("private")["verified"])

    def test_public_api_rate_limit_reuses_existing_credential_once_without_logging_it(self):
        session = self.session()
        requests = []
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit): return b'{"private":false}'
        class Opener:
            def open(self, request, timeout):
                requests.append(request)
                if len(requests) == 1:
                    raise self_module.urllib.error.HTTPError(request.full_url, 403, "rate limit", {}, None)
                return Response()
        self_module = self.module
        with patch.object(self.module.urllib.request, "build_opener", return_value=Opener()), \
                patch.object(session, "_existing_token", return_value="TOP_SECRET"):
            try:
                result = session.verify_visibility("public")
            except self.module.NetworkError as error:
                self.fail("Anonymous rate limiting must reuse an existing credential once: " + str(error))
        self.assertTrue(result["verified"])
        self.assertEqual(len(requests), 2)
        self.assertIsNone(requests[0].get_header("Authorization"))
        self.assertEqual(requests[1].get_header("Authorization"), "Bearer TOP_SECRET")
        self.assertNotIn("TOP_SECRET", repr(session.events))

    def test_real_local_bare_remote_is_verified_and_pushable_without_github(self):
        self.assertIsNotNone(self.module, "bounded close-network helper is not implemented")
        remote = self.root / "backup.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        def git(*args):
            return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()
        git("remote", "set-url", "origin", str(remote))
        git("config", "user.name", "Network Test")
        git("config", "user.email", "network@example.invalid")
        path = self.root / "source.txt"
        path.write_text("first", encoding="utf-8")
        git("add", "source.txt")
        git("commit", "-m", "Baseline")
        git("push", "origin", "main")
        path.write_text("second", encoding="utf-8")
        git("add", "source.txt")
        git("commit", "-m", "New snapshot")
        expected = git("rev-parse", "HEAD")
        session = self.session()
        self.assertIsNone(session.choose_route())
        visibility = session.verify_visibility("public")
        self.assertTrue(visibility.get("local_bare"), "local backup must be distinguished from a public GitHub repo")
        self.assertIsNone(visibility["private"])
        self.assertTrue(session.push_verified(expected)["verified"])
        self.assertEqual(session.remote_head(), expected)

    def test_credential_lookup_never_prompts_or_retains_token_in_events(self):
        session = self.session()
        response = subprocess.CompletedProcess([], 0, "protocol=https\npassword=TOP_SECRET\n", "")
        with patch.object(self.module.subprocess, "run", return_value=response) as run:
            self.assertEqual(session._existing_token(), "TOP_SECRET")
        self.assertEqual(run.call_args.kwargs["env"]["GCM_INTERACTIVE"], "never")
        self.assertNotIn("TOP_SECRET", repr(session.events))
        self.assertNotIn("TOP_SECRET", session.cache_path.read_text() if session.cache_path.exists() else "")


if __name__ == "__main__":
    unittest.main()
