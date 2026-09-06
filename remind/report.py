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


MARKER = "<!-- progress -->"


def build_progress(plan: str) -> str:
    """Строка прогресса для README: галочки и последняя закрытая неделя."""
    done, todo = parse_plan(plan)
    total = len(done) + len(todo)
    percent = round(100 * len(done) / total) if total else 0
    last = done[-1] if done else "ещё не начато"
    return f"**Прогресс:** {len(done)} из {total} ({percent}%) · последнее: {last}"


def update_readme(readme: str, plan: str) -> str:
    """Заменяет строку между маркерами MARKER. Без маркеров возвращает README как есть."""
    head, sep, rest = readme.partition(MARKER)
    if not sep:
        return readme
    _, sep2, tail = rest.partition(MARKER)
    return f"{head}{MARKER}\n{build_progress(plan)}\n{MARKER}{tail if sep2 else rest}"
