#!/usr/bin/env python3
"""Sign a project in to Confident AI and confirm its traces arrive.

A coding agent runs this so the user never handles an API key and the agent
never sees one. The key goes straight from Confident AI into `.env.local`, and
nothing this script prints contains it or the setup token.

Commands, run from the project directory:

  check-key           Is there already a working key? Prints its status only.
  login               Start a browser sign-in. Prints the link and code.
                      --browser says who opens it: system (this script, the
                      default), agent (the agent's own browser), or manual.
  wait                Wait for the browser sign-in, then print the account,
                      its projects, or the new-account questionnaire.
  complete            Create the key for a project and save it to .env.local.
  labels              Add the issues to watch for to the project's "Issues"
                      classifier, creating it if missing. Always exits 0.
  seed              Send the bundled sample traces, for when the app cannot
                      run here. Fresh ids, timed to end now, sent as OTLP JSON.
  verify              Wait for traces sent since the key was saved, then hand
                      off to the web app in the browser used for sign-in.

Every command prints one JSON object on stdout. Exit codes: 0 done, 1 error,
2 still waiting (run `wait` again).

Standard library only, Python 3.8 or newer.
"""

import argparse
import hashlib
import json
import os
import secrets
import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

KEY_NAME = "CONFIDENT_API_KEY"
SOURCE = "confident-onboard"
API_URLS = {
    "us": "https://api.confident-ai.com",
    "eu": "https://eu.api.confident-ai.com",
}
# One web app serves both regions; the sign-in link carries the region.
APP_URL = "https://app.confident-ai.com"
OTEL_ENDPOINTS = {
    "us": "https://otel.confident-ai.com/v1/traces",
    "eu": "https://eu.otel.confident-ai.com/v1/traces",
}
# Agents cap a single command at a few minutes, so one `wait` stays under that
# and the agent calls it again while the link is still valid.
WAIT_SLICE_SECONDS = 240
VERIFY_INTERVAL_SECONDS = 5
VERIFY_TIMEOUT_SECONDS = 180
# Who opens links. Sign-in and the handoff after traces arrive must use the
# same browser, because that browser holds the Confident AI session.
BROWSERS = ("agent", "system", "manual")
SAME_BROWSER = "Open handoffUrl in the same browser you used for sign-in."
SAMPLES_URL = (
    "https://raw.githubusercontent.com/confident-ai/confident-skills/main/"
    "plugins/confident-onboard/skills/confident-onboard/assets/sample-traces.json"
)


class Failure(Exception):
    """An error worth showing the user as is."""


# ---------------------------------------------------------------- output


def emit(payload, code=0):
    print(json.dumps(payload, indent=2))
    sys.exit(code)


def fail(message, **extra):
    emit({"status": "error", "error": message, **extra}, 1)


# ---------------------------------------------------------------- state


def project_dir(args):
    path = Path(args.project_dir).resolve()
    if not path.is_dir():
        raise Failure(f"{path} is not a directory.")
    return path


def state_path(directory):
    """Outside the project, private to this user, one per project folder."""
    digest = hashlib.sha256(str(directory).encode()).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"confident-onboard-{digest}.json"


def load_state(directory):
    path = state_path(directory)
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def save_state(directory, state):
    path = state_path(directory)
    temporary = path.with_suffix(f".{os.getpid()}.tmp")
    fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(state, handle)
    os.replace(str(temporary), str(path))


def forget_secrets(state):
    for key in ("deviceCode", "setupToken"):
        state.pop(key, None)


# ---------------------------------------------------------------- http


def ssl_context():
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def request(method, url, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    merged = {"accept": "application/json", **(headers or {})}
    if data is not None:
        merged["content-type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=merged, method=method)
    try:
        with urllib.request.urlopen(req, context=ssl_context(), timeout=30) as response:
            return response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read() or b"null")
        except ValueError:
            payload = None
        return error.code, payload
    except ssl.SSLError as error:
        raise Failure(
            f"TLS error reaching Confident AI ({error}). On macOS with a python.org "
            "install, run 'Install Certificates.command', or pip install certifi."
        )
    except urllib.error.URLError as error:
        raise Failure(f"Could not reach {urllib.parse.urlsplit(url).netloc}: {error.reason}")


def error_message(status, payload):
    if isinstance(payload, dict) and isinstance(payload.get("error"), str):
        return f"{payload['error']} (HTTP {status})"
    # OTLP errors carry a google.rpc.Status: {"code": ..., "message": ...}.
    if isinstance(payload, dict) and isinstance(payload.get("message"), str):
        return f"{payload['message']} (HTTP {status})"
    return f"Confident AI request failed (HTTP {status})."


def data_of(status, payload):
    if status >= 400 or not isinstance(payload, dict):
        raise Failure(error_message(status, payload))
    if payload.get("success") is True and isinstance(payload.get("data"), dict):
        return payload["data"]
    return payload


# ---------------------------------------------------------------- .env.local


def parse_env(text):
    values = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :].lstrip()
        name, sep, raw = stripped.partition("=")
        if not sep or not name.strip().isidentifier():
            continue
        raw = raw.strip()
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
            raw = raw[1:-1]
        else:
            raw = raw.split(" #", 1)[0].strip()
        values[name.strip()] = raw
    return values


def env_local(directory):
    return directory / ".env.local"


def read_saved_key(directory):
    path = env_local(directory)
    if not path.is_file():
        return None
    return parse_env(path.read_text(encoding="utf-8")).get(KEY_NAME) or None


def write_key(directory, key):
    """Replace the key in place or append it, keep everything else, mode 0600."""
    path = env_local(directory)
    if path.is_symlink():
        raise Failure("Refusing to replace a symbolic-link .env.local file.")
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    assignment = f"{KEY_NAME}={json.dumps(key)}"

    def assigns(line):
        stripped = line.strip()
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :].lstrip()
        return stripped.split("=", 1)[0].strip() == KEY_NAME and "=" in stripped

    merged, replaced = [], False
    for line in lines:
        if assigns(line):
            if not replaced:
                merged.append(assignment)
                replaced = True
            continue
        merged.append(line)
    if not replaced:
        if merged and merged[-1].strip():
            merged.append("")
        merged.append(assignment)
    while merged and not merged[-1].strip():
        merged.pop()

    temporary = directory / f".env.local.{os.getpid()}.tmp"
    fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write("\n".join(merged) + "\n")
        os.replace(str(temporary), str(path))
        os.chmod(str(path), 0o600)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def ensure_ignored(directory):
    """Add .env.local to .gitignore unless git already ignores it."""
    import subprocess

    try:
        subprocess.run(
            ["git", "check-ignore", "-q", ".env.local"],
            cwd=str(directory),
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return False
    except (OSError, subprocess.CalledProcessError):
        pass
    path = directory / ".gitignore"
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    if content and not content.endswith("\n"):
        content += "\n"
    path.write_text(content + ".env.local\n", encoding="utf-8")
    return True


# ---------------------------------------------------------------- regions


def region_for_key(key):
    return "eu" if key.startswith("confident_eu_") else "us"


def api_url(args, state, key=None):
    if getattr(args, "api_url", None):
        return args.api_url.rstrip("/")
    if key:
        return API_URLS[region_for_key(key)]
    if state.get("apiUrl"):
        return state["apiUrl"]
    return API_URLS[args.region]


def traces_url(app_url, project_id):
    if not project_id:
        return app_url
    return f"{app_url}/project/{urllib.parse.quote(project_id)}/observatory/traces"


def handoff_url(app_url, state):
    """New accounts finish onboarding in the web app; others see their traces."""
    if state.get("account") == "new":
        return f"{app_url}/onboarding"
    return traces_url(app_url, state.get("projectId"))


def open_browser(url):
    try:
        return bool(webbrowser.open(url))
    except Exception:
        return False


def utc_iso(moment):
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# ---------------------------------------------------------------- commands


def cmd_check_key(args):
    directory = project_dir(args)
    saved = read_saved_key(directory)
    shell = (os.environ.get(KEY_NAME) or "").strip() or None
    key = saved or shell
    if not key:
        emit({"status": "none", "message": "No CONFIDENT_API_KEY in .env.local or the environment."})
    where = ".env.local" if saved else "environment"
    status, payload = request(
        "GET",
        f"{api_url(args, {}, key)}/v2/traces?pageSize=1",
        headers={KEY_NAME: key},
    )
    if status == 401:
        emit({"status": "rejected", "source": where, "message": "The saved key no longer works. Sign in to create a new one."})
    if status >= 400 and status != 403:
        fail(error_message(status, payload), source=where)
    region = region_for_key(key)
    state = load_state(directory)
    state.update(
        {
            "apiUrl": api_url(args, {}, key),
            "appUrl": APP_URL,
            "account": "reused",
            "browser": "system",
            "since": utc_iso(datetime.now(timezone.utc) - timedelta(minutes=1)),
        }
    )
    state.pop("projectId", None)
    save_state(directory, state)
    emit(
        {
            "status": "accepted",
            "source": where,
            "region": region.upper(),
            "otelEndpoint": OTEL_ENDPOINTS[region],
            "shellKeyDiffers": bool(saved and shell and saved != shell),
            "note": "Listing traces is not enabled for this key's plan." if status == 403 else None,
        }
    )


def cmd_login(args):
    directory = project_dir(args)
    browser = "manual" if args.no_browser else args.browser
    base = api_url(args, {})
    context = {"source": SOURCE}
    if args.org_id:
        context["organizationId"] = args.org_id
    if args.proj_id:
        context["projectId"] = args.proj_id
    session = data_of(*request("POST", f"{base}/cli/auth/sessions", {"context": context}))
    for field in ("deviceCode", "userCode", "verificationUri", "verificationUriComplete", "expiresIn", "interval"):
        if field not in session:
            raise Failure(f"Unexpected sign-in response: missing {field}.")
    app_url = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(session["verificationUri"]))
    save_state(
        directory,
        {
            "apiUrl": base,
            "appUrl": app_url,
            "deviceCode": session["deviceCode"],
            "interval": session["interval"],
            "expiresAt": time.time() + float(session["expiresIn"]),
            "browser": browser,
        },
    )
    opened = browser == "system" and open_browser(session["verificationUriComplete"])
    emit(
        {
            "status": "pending",
            "url": session["verificationUriComplete"],
            "code": session["userCode"],
            "browser": browser,
            "browserOpened": opened,
            "expiresInMinutes": round(float(session["expiresIn"]) / 60),
            "next": (
                "Open the url in your own browser, show the user the code, then run `wait`."
                if browser == "agent"
                else "Show the user the url and code, then run `wait`."
            ),
        }
    )


def cmd_wait(args):
    directory = project_dir(args)
    state = load_state(directory)
    if not state.get("setupToken"):
        if not state.get("deviceCode"):
            raise Failure("No sign-in in progress. Run `login` first.")
        if time.time() >= state["expiresAt"]:
            forget_secrets(state)
            save_state(directory, state)
            raise Failure("The sign-in link expired. Run `login` again.")
        deadline = min(state["expiresAt"], time.time() + args.timeout)
        token = None
        while time.time() < deadline:
            status, payload = request(
                "POST",
                f"{state['apiUrl']}/cli/auth/sessions/token",
                {"deviceCode": state["deviceCode"]},
            )
            if status in (403, 404, 409):
                forget_secrets(state)
                save_state(directory, state)
                raise Failure(error_message(status, payload) + " Run `login` again.")
            result = data_of(status, payload)
            if result.get("status") == "authenticated":
                token = result
                break
            time.sleep(float(state.get("interval", 3)))
        if token is None:
            emit(
                {
                    "status": "pending",
                    "message": "The user has not approved the sign-in yet.",
                    "minutesLeft": max(0, round((state["expiresAt"] - time.time()) / 60)),
                    "next": "Remind the user to approve it in the browser, then run `wait` again.",
                },
                2,
            )
        state.pop("deviceCode", None)
        state["setupToken"] = token["setupToken"]
        state["email"] = token.get("email")
        save_state(directory, state)

    onboarding = data_of(
        *request(
            "GET",
            f"{state['apiUrl']}/cli/onboarding",
            headers={"authorization": f"Bearer {state['setupToken']}"},
        )
    )
    kind = onboarding.get("state")
    if kind in ("new_user", "existing_user"):
        state["account"] = "new" if kind == "new_user" else "existing"
        save_state(directory, state)
    if kind == "new_user":
        state["questionnaireVersion"] = onboarding["questionnaire"]["version"]
        save_state(directory, state)
        emit(
            {
                "status": "signed_in",
                "account": "new",
                "email": state.get("email"),
                "name": (onboarding.get("user") or {}).get("name"),
                "questions": onboarding["questionnaire"]["questions"],
                "next": (
                    "Fill in every answer from the sign-in details and the code, show them to "
                    "the user in one message to confirm, then run `complete --answers '<json>'`."
                ),
            }
        )
    if kind != "existing_user":
        raise Failure("Unexpected onboarding response.")
    projects = onboarding.get("projects", [])
    usable = [p for p in projects if p.get("canCreateApiKey")]
    emit(
        {
            "status": "signed_in",
            "account": "existing",
            "email": state.get("email"),
            "organization": (onboarding.get("organization") or {}).get("name"),
            "projects": [
                {"id": p["id"], "name": p["name"], "canCreateApiKey": bool(p.get("canCreateApiKey"))}
                for p in projects
            ],
            "next": (
                "No project here lets this user create an API key. Ask an admin for access."
                if not usable
                else f"Use the only project with `complete --project-id {usable[0]['id']}`."
                if len(usable) == 1
                else "Ask the user which project to use, then run `complete --project-id <id>`."
            ),
        }
    )


def cmd_complete(args):
    directory = project_dir(args)
    state = load_state(directory)
    if not state.get("setupToken"):
        raise Failure("Not signed in. Run `login`, then `wait`.")
    if bool(args.project_id) == bool(args.answers):
        raise Failure("Pass exactly one of --project-id or --answers.")
    if args.project_id:
        body = {"projectId": args.project_id}
    else:
        raw = args.answers
        if raw.startswith("@"):
            raw = Path(raw[1:]).read_text(encoding="utf-8")
        try:
            answers = json.loads(raw)
        except ValueError as error:
            raise Failure(f"--answers is not valid JSON: {error}")
        if not isinstance(answers, dict):
            raise Failure("--answers must be a JSON object of question id to answer.")
        body = {
            "questionnaireVersion": state.get("questionnaireVersion"),
            "questionnaireAnswers": answers,
        }
    # The same request with the same key is safe to retry; the server returns
    # the key it already made instead of a second one.
    request_hash = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    if state.get("completionHash") != request_hash:
        state["completionHash"] = request_hash
        state["idempotencyKey"] = str(uuid.uuid4())
        save_state(directory, state)
    status, payload = request(
        "POST",
        f"{state['apiUrl']}/cli/onboarding/complete",
        body,
        headers={
            "authorization": f"Bearer {state['setupToken']}",
            "idempotency-key": state["idempotencyKey"],
        },
    )
    if status >= 400 or not isinstance(payload, dict) or payload.get("status") != "completed":
        raise Failure(error_message(status, payload))
    key, project_id = payload.get("apiKey"), payload.get("projectId")
    if not key or not project_id:
        raise Failure("Confident AI did not return a key.")

    write_key(directory, key)
    ignored = ensure_ignored(directory)
    region = region_for_key(key)
    shell = (os.environ.get(KEY_NAME) or "").strip()
    forget_secrets(state)
    for field in ("completionHash", "idempotencyKey", "questionnaireVersion"):
        state.pop(field, None)
    state.update(
        {
            "projectId": project_id,
            "since": utc_iso(datetime.now(timezone.utc) - timedelta(minutes=1)),
        }
    )
    save_state(directory, state)
    emit(
        {
            "status": "completed",
            "projectId": project_id,
            "savedTo": str(env_local(directory)),
            "addedToGitignore": ignored,
            "region": region.upper(),
            "otelEndpoint": OTEL_ENDPOINTS[region],
            "shellKeyDiffers": bool(shell and shell != key),
            "tracesUrl": traces_url(state["appUrl"], project_id),
        }
    )


def load_samples(path):
    """The sample file next to this skill, or the published copy on GitHub."""
    local = Path(path) if path else Path(__file__).resolve().parent.parent / "assets" / "sample-traces.json"
    if local.is_file():
        return json.loads(local.read_text(encoding="utf-8"))
    if path:
        raise Failure(f"{local} does not exist.")
    status, payload = request("GET", SAMPLES_URL)
    if status >= 400 or not isinstance(payload, dict):
        raise Failure(error_message(status, payload))
    return payload


def fresh_batch(document):
    """New trace and span ids, parents kept, and the batch shifted to end now."""
    document = {key: value for key, value in document.items() if key == "resourceSpans"}
    spans = [
        span
        for resource in document.get("resourceSpans", [])
        for scope in resource.get("scopeSpans", [])
        for span in scope.get("spans", [])
    ]
    if not spans:
        raise Failure("The sample file has no spans.")
    trace_ids, span_ids = {}, {}
    for span in spans:
        trace_ids.setdefault(span["traceId"], secrets.token_hex(16))
        span_ids.setdefault(span["spanId"], secrets.token_hex(8))
    offset = time.time_ns() - max(int(span["endTimeUnixNano"]) for span in spans)
    for span in spans:
        span["traceId"] = trace_ids[span["traceId"]]
        span["spanId"] = span_ids[span["spanId"]]
        if span.get("parentSpanId"):
            span["parentSpanId"] = span_ids[span["parentSpanId"]]
        for field in ("startTimeUnixNano", "endTimeUnixNano"):
            span[field] = str(int(span[field]) + offset)
        for event in span.get("events", []):
            event["timeUnixNano"] = str(int(event["timeUnixNano"]) + offset)
    return document, len(trace_ids), len(spans)


def sample_service(document):
    """The service.name the sample file declares."""
    for resource in document.get("resourceSpans", []):
        for attribute in (resource.get("resource") or {}).get("attributes", []):
            if attribute.get("key") == "service.name":
                return (attribute.get("value") or {}).get("stringValue")
    return None


def cmd_seed(args):
    directory = project_dir(args)
    state = load_state(directory)
    key = read_saved_key(directory) or (os.environ.get(KEY_NAME) or "").strip()
    if not key:
        raise Failure("No CONFIDENT_API_KEY in .env.local or the environment.")
    samples = load_samples(args.file)
    document, trace_count, span_count = fresh_batch(samples)
    endpoint = args.otel_url or OTEL_ENDPOINTS[region_for_key(key)]
    status, payload = request(
        "POST", endpoint, document, headers={"x-confident-api-key": key}
    )
    if status >= 400:
        raise Failure(error_message(status, payload))
    rejected = ((payload or {}).get("partialSuccess") or {}).get("rejectedSpans") if isinstance(payload, dict) else None
    state["sampleTraces"] = True
    save_state(directory, state)
    emit(
        {
            "status": "sent",
            "traces": trace_count,
            "spans": span_count - int(rejected or 0),
            "rejectedSpans": int(rejected or 0),
            "service": sample_service(samples),
            "next": f"Run `verify --expect {trace_count}`.",
        }
    )


def cmd_verify(args):
    directory = project_dir(args)
    state = load_state(directory)
    key = read_saved_key(directory) or (os.environ.get(KEY_NAME) or "").strip()
    if not key:
        raise Failure("No CONFIDENT_API_KEY in .env.local or the environment.")
    since = args.since or state.get("since") or utc_iso(datetime.now(timezone.utc) - timedelta(minutes=15))
    app_url = state.get("appUrl") or APP_URL
    link = traces_url(app_url, state.get("projectId"))
    query = urllib.parse.urlencode({"start": since, "pageSize": str(args.expect)})
    url = f"{api_url(args, {}, key)}/v2/traces?{query}"
    deadline = time.time() + args.timeout
    found = []
    while True:
        status, payload = request("GET", url, headers={KEY_NAME: key})
        if status in (401, 403):
            fail(error_message(status, payload), tracesUrl=link)
        if status < 400 and isinstance(payload, dict):
            traces = ((payload.get("data") or {}).get("traces")) or []
            found = traces
            if len(found) >= args.expect:
                break
        if time.time() >= deadline:
            break
        time.sleep(VERIFY_INTERVAL_SECONDS)
    if not found:
        emit(
            {
                "status": "timeout",
                "traceCount": 0,
                "traces": [],
                "since": since,
                "tracesUrl": link,
                "message": "No traces yet. Ingestion can take a couple of minutes; run `verify` again, "
                "then check the run command loaded .env.local and flushed tracing before exit.",
            },
            2,
        )
    browser = state.get("browser") or "system"
    handoff = handoff_url(app_url, state)
    remote = os.environ.get("SSH_CONNECTION") or os.environ.get("CI")
    opened = browser == "system" and not remote and open_browser(handoff)
    emit(
        {
            "status": "found",
            "traceCount": len(found),
            "traces": [t.get("name") or t.get("uuid") for t in found],
            "since": since,
            "tracesUrl": link,
            "handoffUrl": handoff,
            "browser": browser,
            "browserOpened": opened,
            "next": None if opened else SAME_BROWSER,
        }
    )


# ---------------------------------------------------------------- labels

# Exactly this name: the classifier every new project is seeded with.
ISSUES_CLASSIFIER = "Issues"
PAGE_SIZE = 100


def find_or_create_issues_classifier(base, key):
    """Returns (classifier id, whether it was created)."""
    headers = {KEY_NAME: key}
    page = 1
    while True:
        query = urllib.parse.urlencode({"dataModel": "TRACE", "page": str(page), "pageSize": str(PAGE_SIZE)})
        data = data_of(*request("GET", f"{base}/v2/classifiers?{query}", headers=headers))
        classifiers = data.get("classifiers") or []
        for classifier in classifiers:
            if classifier.get("name") == ISSUES_CLASSIFIER:
                return classifier["id"], False
        if not classifiers or page * PAGE_SIZE >= (data.get("totalClassifiers") or 0):
            break
        page += 1
    body = {"name": ISSUES_CLASSIFIER, "dataModel": "TRACE", "preset": "ISSUES"}
    created = data_of(*request("POST", f"{base}/v2/classifiers", body, headers))
    return created["id"], True


def cmd_labels(args):
    """Never blocks onboarding: every outcome exits 0, and it stops at the first
    thing that fails."""
    uploaded = 0
    try:
        raw = args.file
        if raw.startswith("@"):
            raw = Path(raw[1:]).read_text(encoding="utf-8")
        try:
            labels = json.loads(raw)
        except ValueError as error:
            raise Failure(f"--file is not valid JSON: {error}")
        if not isinstance(labels, list) or not all(
            isinstance(label, dict) and label.get("name") and label.get("description") for label in labels
        ):
            raise Failure('--file must be a JSON array of {"name", "description"}.')
        directory = project_dir(args)
        key = read_saved_key(directory) or (os.environ.get(KEY_NAME) or "").strip()
        if not key:
            raise Failure("No CONFIDENT_API_KEY in .env.local or the environment.")
        base = api_url(args, {}, key)
        classifier_id, created = find_or_create_issues_classifier(base, key)
        for label in labels:
            body = {
                "name": label["name"],
                "description": label["description"],
                "status": "RECOMMENDED",
                "enabled": True,
                "polarity": "LOWER_IS_BETTER",
            }
            url = f"{base}/v2/classifiers/{urllib.parse.quote(classifier_id)}/labels"
            data_of(*request("POST", url, body, {KEY_NAME: key}))
            uploaded += 1
    except (Failure, OSError, KeyError, TypeError) as error:
        emit({"status": "failed", "error": str(error), "uploaded": uploaded, "next": "Continue onboarding."})
    emit({"status": "uploaded", "classifierId": classifier_id, "created": created, "labels": uploaded})


# ---------------------------------------------------------------- main


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--project-dir", default=".", help="the application's folder (default: .)")
    parser.add_argument("--region", choices=sorted(API_URLS), default="us", help="data region for a new sign-in")
    parser.add_argument("--api-url", help="override the API base URL (self-hosted)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check-key")
    login = sub.add_parser("login")
    login.add_argument(
        "--browser",
        choices=BROWSERS,
        default="system",
        help="who opens the sign-in link: system (default browser), agent, or manual",
    )
    login.add_argument("--no-browser", action="store_true", help="same as --browser manual")
    login.add_argument("--org-id")
    login.add_argument("--proj-id")
    wait = sub.add_parser("wait")
    wait.add_argument("--timeout", type=int, default=WAIT_SLICE_SECONDS)
    complete = sub.add_parser("complete")
    complete.add_argument("--project-id")
    complete.add_argument("--answers", help="JSON object, or @file containing one")
    labels = sub.add_parser("labels")
    labels.add_argument("--file", required=True, help='JSON array of {"name", "description"}, or @file containing one')
    seed = sub.add_parser("seed")
    seed.add_argument("--file", help="sample traces file (default: the bundled one, else GitHub)")
    seed.add_argument("--otel-url", help=argparse.SUPPRESS)
    verify = sub.add_parser("verify")
    verify.add_argument("--since", help="ISO time; default: when the key was saved")
    verify.add_argument("--expect", type=int, default=7, help="stop early at this many traces")
    verify.add_argument("--timeout", type=int, default=VERIFY_TIMEOUT_SECONDS)

    args = parser.parse_args()
    handlers = {
        "check-key": cmd_check_key,
        "login": cmd_login,
        "wait": cmd_wait,
        "complete": cmd_complete,
        "labels": cmd_labels,
        "seed": cmd_seed,
        "verify": cmd_verify,
    }
    try:
        handlers[args.command](args)
    except Failure as error:
        fail(str(error))
    except KeyboardInterrupt:
        fail("Interrupted.")


if __name__ == "__main__":
    main()
