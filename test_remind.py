import datetime as dt

from remind import build_message, parse_log, parse_plan

PLAN = "# План\n- [x] Модуль 0\n- [ ] Модуль 1\n- [ ] Модуль 2\n"
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
    assert parse_plan(PLAN) == (["Модуль 0"], ["Модуль 1", "Модуль 2"])
    assert parse_log(LOG) == [{"title": "Неделя 1 — 2026-09-06", "Сделал": "настроил репо", "Не понял": "кэш токенов", "Время": "2 ч"}]


def test_message():
    msg = build_message(PLAN, LOG, dt.date(2026, 9, 15))
    assert "неделя 2 из 36" in msg
    assert "Пройдено: 1 из 3" in msg
    assert "Повторить: кэш токенов" in msg
    assert "Остановились: Неделя 1 — 2026-09-06 — настроил репо" in msg
    assert "• Модуль 1" in msg and "Модуль 2" in msg
