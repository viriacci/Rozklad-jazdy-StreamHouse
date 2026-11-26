"""Publish a new calendar, then remove the previous webhook message."""
import json
import time
from pathlib import Path
from urllib.parse import urlsplit
import requests
import config

ROLES = ["1395506395549532217", "1395333302558134434"]
STATE = Path("state/publication.json")
LEGACY = Path(config.STATE_FILE)

def load_state():
    if STATE.exists():
        data = json.loads(STATE.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("pending_delete", []), list):
            raise ValueError("Niepoprawny stan publikacji")
        return data
    return {"message_id": LEGACY.read_text().strip() if LEGACY.exists() else None, "pending_delete": []}

def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(STATE)

def webhook_base():
    url = urlsplit(config.DISCORD_WEBHOOK_URL)
    if url.scheme != "https" or url.hostname not in ("discord.com", "discordapp.com", "canary.discord.com", "ptb.discord.com"):
        raise ValueError("Niepoprawny webhook Discord")
    return url.scheme + "://" + url.netloc + url.path.rstrip("/")

def request(method, url, **kwargs):
    for attempt in range(4):
        try:
            response = requests.request(method, url, timeout=30, **kwargs)
        except requests.RequestException:
            # A POST may have succeeded despite a timeout; do not blindly ping again.
            if method == "POST" or attempt == 3:
                raise RuntimeError("Discord: błąd połączenia") from None
            time.sleep(2 ** attempt)
            continue
        if response.status_code == 429 and attempt < 3:
            time.sleep(min(60, max(1, float(response.json().get("retry_after", 1)))))
            continue
        if method == "DELETE" and response.status_code >= 500 and attempt < 3:
            time.sleep(2 ** attempt)
            continue
        return response

def clean_pending(state):
    pending = list(state.get("pending_delete", []))
    for message_id in pending:
        if not message_id or message_id == state.get("message_id"):
            state["pending_delete"].remove(message_id)
            save_state(state)
            continue
        resp = request("DELETE", webhook_base() + "/messages/" + str(message_id))
        if resp.status_code not in (204, 404):
            raise RuntimeError(f"Discord: nie usunięto poprzedniego rozkładu (HTTP {resp.status_code})")
        print(f"Poprzedni rozkład {message_id}: HTTP {resp.status_code} (usunięty lub już nie istnieje)")
        state["pending_delete"].remove(message_id)
        save_state(state)

def publish(image_path, digest, state):
    payload = {
        "content": " ".join(f"<@&{role}>" for role in ROLES),
        "allowed_mentions": {"parse": [], "roles": ROLES},
        "attachments": [{"id": 0, "filename": "calendar.png"}],
    }
    response = request("POST", webhook_base() + "?wait=true",
        data={"payload_json": json.dumps(payload)},
        files={"files[0]": ("calendar.png", Path(image_path).read_bytes(), "image/png")})
    if not response.ok:
        raise RuntimeError(f"Discord: nie opublikowano rozkładu (HTTP {response.status_code})")
    message = response.json()
    new_id = message["id"]
    print("Role w nowej wiadomości: " + ", ".join(message.get("mention_roles", [])))
    old_id = state.get("message_id")
    state.update(message_id=new_id, fingerprint=digest)
    if old_id and old_id != new_id:
        state.setdefault("pending_delete", []).append(old_id)
    save_state(state)
    print(f"Nowy rozkład: {new_id}")
    clean_pending(state)
