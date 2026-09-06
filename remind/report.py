"""Сборка текста отчёта."""

import datetime as dt

from remind.parse import parse_log, parse_plan

START_DATE = dt.date(2026, 9, 7)  # понедельник первой недели
TOTAL_WEEKS = 36


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
