# ai-learning

Учебный репозиторий курса AI-инженерии: 36 недель, ~5 часов в неделю, задания на Python.

<!-- progress -->
**Прогресс:** 1 из 39 (3%) · последнее: Неделя 1 · М0 · Подготовка
<!-- progress -->

## Структура

```
week-NN/      задания по неделям
projects/     проекты курса
data/logs/    логи вызовов (*.jsonl, в gitignore)
PLAN.md       план курса
LOG.md        дневник обучения
CHEATSHEET.md конспект по модулям
remind/       ежедневный отчёт об учёбе в Telegram
.githooks/    pre-commit: обновляет прогресс в README
```

## Запуск

```bash
uv sync
cp .env.example .env             # вписать ключи провайдеров
git config core.hooksPath .githooks   # прогресс в README обновляется при коммите
uv run week-01/hello.py
```

Реальные ключи хранятся только в `.env` — он в `.gitignore`. В репозиторий попадает только `.env.example` без значений.

## Провайдеры

`week-01/hello.py` шлёт один промпт в пять моделей. Ключи берутся из `.env`, провайдеры без ключа пропускаются.

| Провайдер | Ключ | Оплата |
|---|---|---|
| Claude | `ANTHROPIC_API_KEY` | по токенам, [console.anthropic.com](https://console.anthropic.com) |
| GPT | `OPENAI_API_KEY` | по токенам, [platform.openai.com](https://platform.openai.com) |
| Kimi | `MOONSHOT_API_KEY` | по токенам, [platform.moonshot.ai](https://platform.moonshot.ai) |
| Gemini | `GEMINI_API_KEY` | бесплатный тариф, [aistudio.google.com](https://aistudio.google.com/apikey) |
| Groq | `GROQ_API_KEY` | бесплатный тариф, [console.groq.com](https://console.groq.com/keys) |

## Отчёт в Telegram

Бот дважды в день присылает отчёт: пройдено (чекбоксы `[x]` в PLAN.md), повторить (поле «Не понял» из последних записей LOG.md), где остановились (последняя запись LOG.md), что дальше (первые `[ ]` в PLAN.md). Посмотреть сообщение без отправки: `uv run python -m remind --dry-run`.

1. Создай бота через @BotFather, токен — в `.env` как `TELEGRAM_BOT_TOKEN`.
2. Напиши боту любое сообщение, затем `uv run python -m remind` — он выведет `chat_id`, добавь его в `.env`.
3. Включи ежедневный запуск в 09:00 и 22:00 (launchd, время — в plist):

```bash
cp com.ai-learning.remind.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.ai-learning.remind.plist
```

Выключить: `launchctl bootout gui/$(id -u)/com.ai-learning.remind`.

## Проекты

- [ ] cli-tool
- [ ] doc-chat
- [ ] agent
