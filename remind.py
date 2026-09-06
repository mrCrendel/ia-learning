"""Ежедневный отчёт об учёбе в Telegram. Запускается launchd (см. README).

Источники: PLAN.md (чекбоксы) и LOG.md (записи по неделям).
`uv run remind.py --dry-run` — показать сообщение без отправки.
"""

import datetime as dt
import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

START_DATE = dt.date(2026, 9, 7)  # понедельник первой недели
TOTAL_WEEKS = 36
ROOT = Path(__file__).parent


def parse_plan(text: str) -> tuple[list[str], list[str]]:
    """Возвращает (сделанные пункты, несделанные пункты)."""
    done = re.findall(r"^\s*- \[x\] (.+)$", text, re.M | re.I)
    todo = re.findall(r"^\s*- \[ \] (.+)$", text, re.M)
    return done, todo


def parse_log(text: str) -> list[dict[str, str]]:
    """Записи LOG.md в порядке файла. Шаблон («Неделя N») пропускается."""
    entries = []
    for chunk in re.split(r"^## ", text, flags=re.M)[1:]:
        title, _, body = chunk.partition("\n")
        if not title.startswith("Неделя") or "Неделя N" in title:
            continue
        fields = dict(re.findall(r"^- (\w[^:]*): ?(.*)$", body, re.M))
        entries.append({"title": title.strip(), **fields})
    return entries


def build_message(plan: str, log: str, today: dt.date) -> str:
    done, todo = parse_plan(plan)
    entries = parse_log(log)
    week = max(1, (today - START_DATE).days // 7 + 1)
    lines = [f"📚 Учёба — неделя {week} из {TOTAL_WEEKS}", ""]

    lines.append(f"✅ Пройдено: {len(done)} из {len(done) + len(todo)} пунктов плана")
    lines += [f"   • {item}" for item in done[-3:]]

    repeat = [e["Не понял"] for e in entries[-3:] if e.get("Не понял")]
    lines.append("🔁 Повторить: " + ("; ".join(repeat) if repeat else "—"))

    if entries:
        last = entries[-1]
        lines.append(f"⏸ Остановились: {last['title']} — {last.get('Сделал', '—')}")
    else:
        lines.append("⏸ Остановились: записей в LOG.md нет")

    lines.append("➡️ Дальше:")
    lines += [f"   • {item}" for item in todo[:3]] or ["   • план пуст — заполни PLAN.md"]
    return "\n".join(lines)


def main() -> None:
    load_dotenv()
    text = build_message((ROOT / "PLAN.md").read_text(), (ROOT / "LOG.md").read_text(), dt.date.today())
    if "--dry-run" in sys.argv:
        print(text)
        return

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token:
        sys.exit("Нет TELEGRAM_BOT_TOKEN в .env. Создай бота через @BotFather и вставь токен.")
    api = f"https://api.telegram.org/bot{token}"

    if not chat_id:
        # Первый запуск: напиши боту любое сообщение, затем запусти скрипт — он покажет chat_id.
        updates = httpx.get(f"{api}/getUpdates", timeout=10).raise_for_status().json()["result"]
        if not updates:
            sys.exit("Нет TELEGRAM_CHAT_ID. Напиши своему боту в Telegram любое сообщение и запусти снова.")
        sys.exit(f"Твой chat_id: {updates[-1]['message']['chat']['id']} — добавь его в .env как TELEGRAM_CHAT_ID.")

    httpx.post(f"{api}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10).raise_for_status()


if __name__ == "__main__":
    main()
