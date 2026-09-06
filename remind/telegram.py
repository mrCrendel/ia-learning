"""Отправка через Telegram Bot API."""

import httpx


def _api(token: str) -> str:
    return f"https://api.telegram.org/bot{token}"


def last_chat_id(token: str) -> int | None:
    """chat_id последнего входящего сообщения боту, None если сообщений нет."""
    updates = httpx.get(f"{_api(token)}/getUpdates", timeout=10).raise_for_status().json()["result"]
    return updates[-1]["message"]["chat"]["id"] if updates else None


def send(token: str, chat_id: str, text: str) -> None:
    httpx.post(f"{_api(token)}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10).raise_for_status()
