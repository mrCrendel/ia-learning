import datetime as dt

from remind.parse import parse_log, parse_plan
from remind.report import build_message, update_readme

PLAN = """# План
- [ ] критерий проекта, в прогресс не идёт

## Чеклист

- [x] Модуль 0
- [ ] Модуль 1
- [ ] Модуль 2
"""
LOG = """# Дневник

## Шаблон

## Неделя N — дата
- Сделал:
- Не понял:

---

## Неделя 1 — 2026-09-06
- Сделал: настроил репо
- Не понял: кэш токенов
- Время: 2 ч
"""


def test_parse():
    assert parse_plan(PLAN) == (["Модуль 0"], ["Модуль 1", "Модуль 2"])  # критерии вне «## Чеклист» пропущены
    assert parse_log(LOG) == [{"title": "Неделя 1 — 2026-09-06", "Сделал": "настроил репо", "Не понял": "кэш токенов", "Время": "2 ч"}]


def test_message():
    msg = build_message(PLAN, LOG, dt.date(2026, 9, 15))
    assert "неделя 2 из 36" in msg
    assert "Пройдено: 1 из 3" in msg
    assert "Повторить: кэш токенов" in msg
    assert "Остановились: Неделя 1 — 2026-09-06 — настроил репо" in msg
    assert "• Модуль 1" in msg and "Модуль 2" in msg


def test_readme():
    readme = "# ai-learning\n\n<!-- progress -->\n<!-- progress -->\n\n## Структура\n"
    out = update_readme(readme, PLAN)
    assert "**Прогресс:** 1 из 3 (33%) · последнее: Модуль 0" in out
    assert out.endswith("\n## Структура\n")  # хвост не съеден
    assert update_readme("# без маркеров\n", PLAN) == "# без маркеров\n"  # no-op
