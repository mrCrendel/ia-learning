"""Один промпт — по весовым категориям моделей у пяти провайдеров.

Сравнивать цену имеет смысл только внутри одной категории: флагман против
дешёвой модели — это сравнение разных инструментов, а не провайдеров.

    uv run week-01/hello.py            # mid, рабочая лошадка
    uv run week-01/hello.py frontier   # сложное рассуждение
    uv run week-01/hello.py small      # классификация, извлечение
    uv run week-01/hello.py all
"""

import asyncio
import os
import sys
import time

from dotenv import load_dotenv

PROMPT = "Объясни в двух предложениях, что такое токен в LLM."

# Категории:
#   frontier — сложное рассуждение, агенты, код. Дорого и медленно.
#   mid      — RAG, суммаризация, чат. Закрывает большинство продуктовых задач.
#   small    — классификация, извлечение полей, роутинг. Дёшево и быстро.
#
# Цены — USD за 1M токенов (input, output). Проверь актуальные у провайдера.
# У Groq и Kimi часть категорий пустая: линейка моделей их просто не покрывает.
PROVIDERS = {
    "claude": {
        "key": "ANTHROPIC_API_KEY",
        "models": {
            "frontier": ("claude-opus-5", 5.00, 25.00),
            "mid": ("claude-sonnet-5", 2.00, 10.00),
            "small": ("claude-haiku-4-5", 1.00, 5.00),
        },
    },
    "gpt": {
        "key": "OPENAI_API_KEY",
        "models": {
            "frontier": ("gpt-5", 1.25, 10.00),
            "mid": ("gpt-5-mini", 0.25, 2.00),
            "small": ("gpt-5-nano", 0.05, 0.40),
        },
    },
    "gemini": {
        "key": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": {
            "frontier": ("gemini-3.1-pro-preview", 0.0, 0.0),
            "mid": ("gemini-3.6-flash", 0.0, 0.0),
            "small": ("gemini-3.1-flash-lite", 0.0, 0.0),
        },
    },
    "groq": {
        "key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "models": {
            "mid": ("openai/gpt-oss-120b", 0.0, 0.0),
            "small": ("openai/gpt-oss-20b", 0.0, 0.0),
        },
    },
    "kimi": {
        "key": "MOONSHOT_API_KEY",
        "base_url": "https://api.moonshot.ai/v1",
        "models": {
            "frontier": ("kimi-k3", 0.60, 2.50),
            "mid": ("kimi-k2.6", 0.60, 2.50),
        },
    },
}

TIERS = ("frontier", "mid", "small")


def cost(price_in: float, price_out: float, tokens_in: int, tokens_out: int) -> float:
    return (tokens_in * price_in + tokens_out * price_out) / 1_000_000


async def ask_claude(cfg: dict, model: str) -> tuple[str, int, int]:
    from anthropic import AsyncAnthropic

    async with AsyncAnthropic(api_key=os.environ[cfg["key"]]) as client:
        resp = await client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": PROMPT}],
        )
    text = "".join(block.text for block in resp.content if block.type == "text")
    return text, resp.usage.input_tokens, resp.usage.output_tokens


async def ask_openai_compatible(cfg: dict, model: str) -> tuple[str, int, int]:
    """GPT, Gemini, Groq и Kimi говорят одним протоколом — меняется только base_url."""
    from openai import AsyncOpenAI

    async with AsyncOpenAI(api_key=os.environ[cfg["key"]], base_url=cfg.get("base_url")) as client:
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": PROMPT}],
        )
    return resp.choices[0].message.content or "", resp.usage.prompt_tokens, resp.usage.completion_tokens


async def ask(name: str, tier: str) -> dict | None:
    cfg = PROVIDERS[name]
    model, price_in, price_out = cfg["models"][tier]
    call = ask_claude if name == "claude" else ask_openai_compatible
    started = time.perf_counter()
    try:
        text, tokens_in, tokens_out = await call(cfg, model)
    except Exception as e:
        print(f"[{tier}] {name} · {model} — ошибка {type(e).__name__}: {e}")
        return None
    elapsed = time.perf_counter() - started
    print(f"[{tier}] {name} · {model}\n{text.strip()}\n")
    return {
        "tier": tier,
        "name": name,
        "model": model,
        "in": tokens_in,
        "out": tokens_out,
        "cost": cost(price_in, price_out, tokens_in, tokens_out),
        "sec": elapsed,
    }


def print_table(rows: list[dict]) -> None:
    print(f"{'категория':<10} {'провайдер':<8} {'модель':<26} {'in':>5} {'out':>5} {'$':>10} {'сек':>6}")
    for r in sorted(rows, key=lambda r: (TIERS.index(r["tier"]), r["cost"])):
        print(
            f"{r['tier']:<10} {r['name']:<8} {r['model']:<26} "
            f"{r['in']:>5} {r['out']:>5} {r['cost']:>10.6f} {r['sec']:>6.1f}"
        )


async def main() -> None:
    load_dotenv()
    arg = sys.argv[1] if len(sys.argv) > 1 else "mid"
    if arg not in TIERS and arg != "all":
        sys.exit(f"Категория: {', '.join(TIERS)} или all")
    tiers = TIERS if arg == "all" else (arg,)

    jobs = [
        (name, tier)
        for tier in tiers
        for name, cfg in PROVIDERS.items()
        if os.getenv(cfg["key"]) and tier in cfg["models"]
    ]
    if not jobs:
        sys.exit("Нет ключей. Скопируй .env.example в .env и заполни.")

    results = await asyncio.gather(*(ask(name, tier) for name, tier in jobs))
    print_table([r for r in results if r])


if __name__ == "__main__":
    assert cost(5.0, 25.0, 1_000_000, 0) == 5.0
    asyncio.run(main())
