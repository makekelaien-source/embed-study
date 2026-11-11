"""Deadline-bounded Git transport for daily close; secrets stay in memory.

This helper never changes repository/global proxy configuration and never forces a
push. The caller owns Git mutation ordering; concurrent work here is read-only.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request


class NetworkError(RuntimeError):
    def __init__(self, message, *, retryable=True):
        super().__init__(message)
        self.retryable = retryable


def _redact(message):
    message = re.sub(r"(https?://)[^/\s@]+@", r"\1[redacted]@", str(message))
    message = re.sub(r"(?i)(password|token|authorization)\s*[=:]\s*[^\s]+", r"\1=[redacted]", message)
    message = re.sub(r"(?i)bearer\s+[^\s]+", "Bearer [redacted]", message)
    message = re.sub(r"\b(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]+", "[redacted]", message)
    return message.strip()[:500]


def _valid_route(route):
    if not isinstance(route, str):
        return False
    try:
        url = urllib.parse.urlsplit(route)
        return (url.scheme in ("http", "https") and
                url.hostname in ("127.0.0.1", "localhost", "::1") and
                url.port is not None and 0 < url.port < 65536 and
                url.username is None and url.password is None and
                url.path in ("", "/") and not url.query and not url.fragment)
    except ValueError:
        return False


class NetworkSession:
    def __init__(self, root, deadline_seconds=90, *, proxy_hints=None):
        self.root = Path(root).resolve()
        self.deadline = time.monotonic() + max(0, float(deadline_seconds))
        self.events = []
        self.chosen_route = None
        self.route_selected = False
        self.remote_sha = None
        raw_path = self._local(["rev-parse", "--git-path", "study-close-route.json"]).strip()
        path = Path(raw_path)
        self.cache_path = path if path.is_absolute() else self.root / path
        self.remote = self._local(["remote", "get-url", "origin"]).strip()
        self.cached_route = None
        self.has_cached_route = False
        try:
            cache = json.loads(self.cache_path.read_text(encoding="utf-8"))
            if "route" in cache and (cache["route"] is None or _valid_route(cache["route"])):
                self.cached_route = cache["route"]
                self.has_cached_route = True
        except (OSError, ValueError, TypeError):
            pass
        hints = list(proxy_hints or [])
        try:
            previous = json.loads((self.root / "00-memory/local-close-work.json").read_text(encoding="utf-8-sig"))
            hints.append(previous.get("git_proxy"))
        except (OSError, ValueError, TypeError):
            pass
        routes = ([self.cached_route] if self.has_cached_route else [])
        routes += [value for value in hints if _valid_route(value)]
        routes.append(None)
        self.routes = list(dict.fromkeys(routes))[:3]

    @staticmethod
    def _base_env():
        return os.environ | {"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never",
                             "GCM_GUI_PROMPT": "0"}

    def _local(self, args):
        try:
            result = subprocess.run(["git", *args], cwd=self.root, capture_output=True,
                                    text=True, timeout=3, env=self._base_env())
        except (OSError, subprocess.TimeoutExpired):
            raise NetworkError("Local Git setup check failed", retryable=False) from None
        if result.returncode:
            raise NetworkError("Local Git setup check failed", retryable=False)
        return result.stdout

    def _timeout(self, limit):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise NetworkError("Network deadline exceeded; synchronization remains pending", retryable=False)
        return min(float(limit), remaining)

    def route_env(self, route=None):
        if route is not None and not _valid_route(route):
            raise NetworkError("Only credential-free loopback HTTP(S) proxies are accepted", retryable=False)
        env = self._base_env()
        for key in list(env):
            if key.lower() in ("http_proxy", "https_proxy", "all_proxy"):
                env.pop(key)
        if route:
            env.update(HTTP_PROXY=route, HTTPS_PROXY=route)
        try:
            count = int(env.get("GIT_CONFIG_COUNT", "0"))
        except ValueError:
            raise NetworkError("Invalid inherited Git configuration count", retryable=False) from None
        if count < 0:
            raise NetworkError("Invalid inherited Git configuration count", retryable=False)
        additions = [("http.proxy", route or ""), ("http.version", "HTTP/1.1"),
                     ("http.lowSpeedLimit", "1"), ("http.lowSpeedTime", "8")]
        for index, (key, value) in enumerate(additions, count):
            env[f"GIT_CONFIG_KEY_{index}"] = key
            env[f"GIT_CONFIG_VALUE_{index}"] = value
        env["GIT_CONFIG_COUNT"] = str(count + len(additions))
        return env

    def _run_git(self, args, route=None, limit=6, input=None):
        timeout = self._timeout(limit)
        started = time.monotonic()
        try:
            result = subprocess.run(["git", *args], cwd=self.root, capture_output=True,
                                    text=True, timeout=timeout, env=self.route_env(route), input=input)
        except subprocess.TimeoutExpired:
            raise NetworkError(f"Git {args[0]} timed out after at most {timeout:.1f}s") from None
        except OSError:
            raise NetworkError(f"Git {args[0]} could not be started", retryable=False) from None
        self.events.append({"operation": args[0], "route": route,
                            "seconds": round(time.monotonic() - started, 3), "exit": result.returncode})
        if result.returncode:
            retryable = not any(marker in result.stderr.lower() for marker in
                                ("non-fast-forward", "fetch first", "[rejected]"))
            raise NetworkError(f"Git {args[0]} failed: {_redact(result.stderr)}", retryable=retryable)
        return result.stdout

    def _probe(self, route):
        if route is not None:
            url = urllib.parse.urlsplit(route)
            try:
                with socket.create_connection((url.hostname, url.port), timeout=self._timeout(1)):
                    pass
            except OSError:
                raise NetworkError("Configured local proxy is not listening") from None
        output = self._run_git(["ls-remote", "--exit-code", "origin", "refs/heads/main"], route, limit=6)
        parts = output.split()
        if not parts or not re.fullmatch(r"[0-9a-fA-F]{40,64}", parts[0]):
            raise NetworkError("Remote main SHA was not returned", retryable=False)
        return parts[0]

    def _remember(self, route):
        payload = {"route": route, "verified_at": datetime.now(timezone.utc).isoformat()}
        try:
            temporary = self.cache_path.with_name(self.cache_path.name + ".tmp")
            temporary.write_text(json.dumps(payload) + "\n", encoding="utf-8")
            temporary.replace(self.cache_path)
        except OSError:
            self.events.append({"operation": "cache", "status": "unavailable"})

    def choose_route(self):
        errors = []
        if self.has_cached_route:
            try:
                self.remote_sha = self._probe(self.cached_route)
                self.chosen_route = self.cached_route
                self.route_selected = True
                self._remember(self.chosen_route)
                return self.chosen_route
            except NetworkError as error:
                errors.append(str(error))
        routes = [route for route in self.routes if not self.has_cached_route or route != self.cached_route]
        if not routes:
            raise NetworkError("No working Git route; synchronization remains pending")
        executor = ThreadPoolExecutor(max_workers=min(3, len(routes)))
        futures = {executor.submit(self._probe, route): route for route in routes}
        try:
            for future in as_completed(futures, timeout=self._timeout(7)):
                try:
                    sha = future.result()
                except NetworkError as error:
                    errors.append(str(error))
                    continue
                self.chosen_route = futures[future]
                self.remote_sha = sha
                self.route_selected = True
                self._remember(self.chosen_route)
                return self.chosen_route
        except TimeoutError:
            errors.append("route probes exceeded their time budget")
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        summary = "; ".join(errors[-2:])
        raise NetworkError("No working Git route; synchronization remains pending. " + summary)

    def remote_head(self):
        """Read main afresh without writing the remote or trusting a cached SHA."""
        if not self.route_selected:
            self.choose_route()
        output = self._run_git(["ls-remote", "--exit-code", "origin", "refs/heads/main"],
                               self.chosen_route, limit=6)
        parts = output.split()
        if not parts or not re.fullmatch(r"[0-9a-fA-F]{40,64}", parts[0]):
            raise NetworkError("Remote main SHA was not returned", retryable=False)
        self.remote_sha = parts[0]
        return self.remote_sha

    def push_verified(self, expected_sha):
        if not re.fullmatch(r"[0-9a-fA-F]{40,64}", expected_sha):
            raise NetworkError("Expected commit must be a full SHA", retryable=False)
        for ref in ("HEAD", "refs/heads/main"):
            if self._run_git(["rev-parse", ref], limit=3).strip() != expected_sha:
                raise NetworkError("Local HEAD/main changed; synchronization stopped", retryable=False)
        if not self.route_selected:
            self.choose_route()
        routes = [self.chosen_route] + [route for route in self.routes if route != self.chosen_route]
        errors = []
        for route in routes[:2]:
            try:
                self._run_git(["push", "origin", "main"], route, limit=20)
                output = self._run_git(["ls-remote", "--exit-code", "origin", "refs/heads/main"], route, limit=6)
                parts = output.split()
                if not parts or parts[0] != expected_sha:
                    raise NetworkError("Remote main differs from expected commit; reconciliation required", retryable=False)
                self.chosen_route = route
                self.remote_sha = expected_sha
                self.route_selected = True
                self._remember(route)
                return {"sha": expected_sha, "route": route, "verified": True}
            except NetworkError as error:
                if not error.retryable:
                    raise
                errors.append(str(error))
        raise NetworkError("Upload failed after bounded route fallback; synchronization remains pending. " + "; ".join(errors))

    def _existing_token(self):
        try:
            response = subprocess.run(["git", "-c", "credential.interactive=never", "credential", "fill"],
                                      input="protocol=https\nhost=github.com\n\n", cwd=self.root,
                                      capture_output=True, text=True, env=self._base_env(), timeout=self._timeout(4))
        except (OSError, subprocess.TimeoutExpired):
            return None
        if response.returncode:
            return None
        fields = dict(line.split("=", 1) for line in response.stdout.splitlines() if "=" in line)
        return fields.get("password")

    def _github_metadata(self, require_token=False):
        remote = self.remote
        if remote.startswith("git@github.com:"):
            slug = remote[len("git@github.com:"):]
        else:
            url = urllib.parse.urlsplit(remote)
            if url.scheme != "https" or url.hostname != "github.com" or url.username or url.password:
                raise NetworkError("Visibility verification only supports GitHub HTTPS/SSH remotes", retryable=False)
            slug = url.path.lstrip("/")
        slug = slug.removesuffix(".git").rstrip("/")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", slug):
            raise NetworkError("Invalid GitHub repository path", retryable=False)
        token = self._existing_token() if require_token else None
        if require_token and not token:
            raise NetworkError("Existing private-repository credential unavailable; synchronization pending", retryable=False)
        route = self.chosen_route if self.route_selected else (self.cached_route if self.has_cached_route else None)
        proxy = urllib.request.ProxyHandler({"http": route, "https": route} if route else {})
        opener = urllib.request.build_opener(proxy)
        for attempt in range(2):
            headers = {"Accept": "application/vnd.github+json", "User-Agent": "study-daily-close"}
            if token:
                headers["Authorization"] = "Bearer " + token
            request = urllib.request.Request("https://api.github.com/repos/" + slug, headers=headers)
            try:
                with opener.open(request, timeout=self._timeout(6)) as response:
                    payload = json.loads(response.read(1024 * 1024).decode("utf-8"))
            except urllib.error.HTTPError as error:
                self.events.append({"operation": "github-visibility", "http_status": error.code})
                if attempt == 0 and token is None and error.code in (401, 403, 429):
                    token = self._existing_token()
                    if token:
                        continue
                raise NetworkError("GitHub visibility could not be verified within the time budget", retryable=False) from None
            except (OSError, ValueError):
                raise NetworkError("GitHub visibility could not be verified within the time budget", retryable=False) from None
            if not isinstance(payload, dict):
                raise NetworkError("GitHub visibility response is not a metadata object", retryable=False)
            payload["_repository"] = slug
            return payload
        raise NetworkError("GitHub visibility retry exhausted", retryable=False)

    def verify_visibility(self, expected_visibility):
        if expected_visibility not in ("public", "private"):
            raise NetworkError("Explicit expected visibility must be public or private", retryable=False)
        local = Path(self.remote)
        if not local.is_absolute():
            local = self.root / local
        if local.is_dir():
            result = self._local(["--git-dir", str(local), "rev-parse", "--is-bare-repository"])
            if result.strip() != "true":
                raise NetworkError("Local backup remote is not bare", retryable=False)
            return {"repository": str(local), "local_bare": True, "private": None, "visibility": "local-bare", "verified": True}
        metadata = self._github_metadata(require_token=expected_visibility == "private")
        actual = metadata.get("private")
        if type(actual) is not bool or actual != (expected_visibility == "private"):
            raise NetworkError(f"Expected {expected_visibility} GitHub visibility was not verified", retryable=False)
        return {"repository": metadata.get("_repository", self.remote), "private": actual,
                "visibility": expected_visibility, "verified": True}
