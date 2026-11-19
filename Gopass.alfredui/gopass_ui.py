import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit


class WorkflowError(Exception):
    pass


FIELDS = {
    "username": re.compile(r"^(?:username|user|login):[ \t]*(.*)$", re.I),
    "url": re.compile(r"^(?:url|website):[ \t]*(.*)$", re.I),
}


def run(command, content=None):
    try:
        return subprocess.run(
            command, input=content, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, check=True, timeout=30,
        ).stdout
    except FileNotFoundError:
        raise WorkflowError(f"{command[0]} is required.") from None
    except subprocess.TimeoutExpired:
        raise WorkflowError("Operation timed out. Check the gopass unlock prompt.") from None
    except subprocess.CalledProcessError:
        raise WorkflowError("Operation failed. Check gopass setup and unlock the store.") from None


def status(message, target="status"):
    return {"update": {"ids": {target: {"text": message}}}}


def read_entry(path):
    return run(["gopass", "show", "--nofuzzysearch", "--noparsing", "--unsafe", "--", path])


def field_value(lines, field):
    for line in lines[1:]:
        match = FIELDS[field].fullmatch(line)
        if match:
            return match[1]
    return ""


def website(value):
    if not value or any(char.isspace() or ord(char) < 32 for char in value):
        raise WorkflowError("Enter a valid HTTP or HTTPS website.")
    try:
        url = urlsplit(value)
        if url.scheme in ("http", "https") and url.hostname and not url.username and not url.password:
            return value
    except ValueError:
        pass
    raise WorkflowError("Enter a valid HTTP or HTTPS website.")


def edit(path, raw):
    lines = raw.decode().split("\n")
    editor = json.loads(Path("editor.json").read_text())
    for component in editor["components"]:
        values = {
            "editPath": path,
            "editUsername": field_value(lines, "username"),
            "editSite": field_value(lines, "url"),
        }
        if component.get("id") in values:
            component["text"] = values[component["id"]]
    digest = hashlib.sha256(raw).hexdigest()
    save_actions = [editor["shortcuts"][0]["action"], editor["components"][-1]["components"][-1]["events"][0]["action"]]
    for action in save_actions:
        action["args"][1:1] = [path, digest]
    return {"sheet": {"id": "entryEditor", "root": editor}}


def save(path, digest, username, url):
    password = os.environ.pop("GOPASS_UI_NEW_PASSWORD", "")
    if any("\n" in value or "\r" in value for value in (username, url, password)):
        raise WorkflowError("Fields must contain a single line.")
    if url:
        website(url)
    raw = read_entry(path)
    if hashlib.sha256(raw).hexdigest() != digest:
        raise WorkflowError("This entry changed. Reopen it before saving.")
    first, *lines = raw.decode().split("\n")
    changes = {"username": username, "url": url}
    pending = {key: value for key, value in changes.items() if value != field_value([first, *lines], key)}
    updated = [password or first]
    for line in lines:
        field = next((key for key in pending if FIELDS[key].fullmatch(line)), None)
        if field is None:
            updated.append(line)
        elif pending[field]:
            label = line.split(":", 1)[0]
            updated.append(f"{label}: {pending[field]}")
            pending[field] = ""
    for field, value in pending.items():
        if value:
            updated.insert(1, f"{field}: {value}")
    content = "\n".join(updated).encode()
    if content != raw:
        run(["gopass", "insert", "--force", "--multiline", "--", path], content)
    return {"sheet": {"close": "entryEditor"}, **status("Entry saved")}


def dispatch(operation, *args):
    if operation == "list":
        rows = []
        for path in run(["gopass", "list", "--flat"]).decode().splitlines():
            parent, _, name = path.rpartition("/")
            rows.append({"uid": path, "name.text": name, "path.text": parent})
        return {"update": {"ids": {"entries": {"data": {"src": rows}}}}}

    path, *values = args
    if not path:
        raise WorkflowError("Select an entry first.")
    if operation == "password":
        run(["gopass", "show", "--nofuzzysearch", "--clip", "--", path])
        return status("Password copied")
    if operation == "save":
        return save(path, *values)
    raw = read_entry(path)
    if operation == "edit":
        return edit(path, raw)
    lines = raw.decode().split("\n")
    if operation == "username":
        username = field_value(lines, "username")
        if not username:
            raise WorkflowError("This entry has no username.")
        run(["/usr/bin/pbcopy"], username.encode())
        return status("Username copied")
    url = field_value(lines, "url")
    if not url:
        raise WorkflowError("This entry has no website.")
    run(["/usr/bin/open", website(url)])
    return status("Website opened")


if __name__ == "__main__":
    operation, *args = sys.argv[1:]
    try:
        result = dispatch(operation, *args)
    except (WorkflowError, UnicodeError) as error:
        message = str(error) if isinstance(error, WorkflowError) else "This entry is not UTF-8 text."
        result = status(message, "editStatus" if operation == "save" else "status")
    if operation == "save":
        result["variables"] = {"GOPASS_UI_NEW_PASSWORD": ""}
    print(json.dumps(result))
