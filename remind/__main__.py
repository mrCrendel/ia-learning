"""Ежедневный отчёт об учёбе в Telegram. Запускается launchd (см. README).

`uv run python -m remind --dry-run` — показать сообщение без отправки.
"""

import datetime as dt
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from remind import telegram
from remind.report import build_message

ROOT = Path(__file__).parent.parent


def main() -> None:
    load_dotenv(ROOT / ".env")
    text = build_message((ROOT / "PLAN.md").read_text(), (ROOT / "LOG.md").read_text(), dt.date.today())
    if "--dry-run" in sys.argv:
        print(text)
        return

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token:
        sys.exit("Нет TELEGRAM_BOT_TOKEN в .env. Создай бота через @BotFather и вставь токен.")
    if not chat_id:
        # Первый запуск: напиши боту любое сообщение, затем запусти скрипт — он покажет chat_id.
        found = telegram.last_chat_id(token)
        if found is None:
            sys.exit("Нет TELEGRAM_CHAT_ID. Напиши своему боту в Telegram любое сообщение и запусти снова.")
        sys.exit(f"Твой chat_id: {found} — добавь его в .env как TELEGRAM_CHAT_ID.")

    telegram.send(token, chat_id, text)


if __name__ == "__main__":
    main()
