"""
Wysyła / edytuje wiadomość na Discordzie przez webhook, podmieniając
załączony obrazek kalendarza.

WAŻNE: webhook NIE MOŻE sam przypiąć wiadomości (brak uprawnień w API
webhooków). Przypinasz JEDEN RAZ ręcznie w Discordzie po pierwszym
uruchomieniu - potem ten sam skrypt tylko EDYTUJE tę wiadomość (nie
tworzy nowej), więc pozostaje przypięta.
"""
import re
import requests

import config

WEBHOOK_URL_RE = re.compile(r"/webhooks/(\d+)/([^/?]+)")


def _webhook_id_and_token():
    match = WEBHOOK_URL_RE.search(config.DISCORD_WEBHOOK_URL)
    if not match:
        raise ValueError("Nie udało się sparsować DISCORD_WEBHOOK_URL")
    return match.group(1), match.group(2)


def _read_message_id():
    try:
        with open(config.STATE_FILE, "r") as f:
            content = f.read().strip()
            return content or None
    except FileNotFoundError:
        return None


def _write_message_id(message_id):
    with open(config.STATE_FILE, "w") as f:
        f.write(str(message_id))


def post_or_edit_calendar(image_path, content_text=""):
    webhook_id, webhook_token = _webhook_id_and_token()
    message_id = _read_message_id()

    with open(image_path, "rb") as f:
        files = {"file": ("calendar.png", f, "image/png")}
        payload = {"content": content_text}

        if message_id:
            url = (
                f"https://discord.com/api/webhooks/{webhook_id}/"
                f"{webhook_token}/messages/{message_id}"
            )
            resp = requests.patch(url, data=payload, files=files)
            if resp.status_code == 404:
                # wiadomość została ręcznie usunięta - tworzymy nową
                message_id = None
            else:
                resp.raise_for_status()
                print(f"Zedytowano wiadomość {message_id}")
                return message_id

        if not message_id:
            url = f"https://discord.com/api/webhooks/{webhook_id}/{webhook_token}?wait=true"
            resp = requests.post(url, data=payload, files=files)
            resp.raise_for_status()
            new_id = resp.json()["id"]
            _write_message_id(new_id)
            print(f"Utworzono nową wiadomość {new_id} - PRZYPNIJ JĄ RĘCZNIE w Discordzie.")
            return new_id


if __name__ == "__main__":
    post_or_edit_calendar("test_output.png", content_text="Test kalendarza streamów")
