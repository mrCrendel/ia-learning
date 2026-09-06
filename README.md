# ai-learning

Учебный репозиторий курса AI-инженерии: 36 недель, ~5 часов в неделю, задания на Python.

## Структура

```
week-NN/      задания по неделям
projects/     проекты курса
data/logs/    логи вызовов (*.jsonl, в gitignore)
PLAN.md       план курса
LOG.md        дневник обучения
CHEATSHEET.md конспект по модулям
```

## Запуск

```bash
uv sync
cp .env.example .env   # вписать ключи
uv run week-01/hello.py
```

Реальные ключи хранятся только в `.env` — он в `.gitignore`. В репозиторий попадает только `.env.example` без значений.

## Проекты

- [ ] cli-tool
- [ ] doc-chat
- [ ] agent
