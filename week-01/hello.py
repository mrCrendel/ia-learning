"""Один промпт — в пять моделей пяти провайдеров.

Печатает ответ, число токенов и стоимость каждого вызова.
Anthropic ходит своим SDK, остальные — OpenAI-совместимые эндпоинты.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

PROMPT = "Объясни в двух предложениях, что такое токен в LLM."

# USD за 1M токенов (input, output). Проверь актуальные цены на сайтах провайдеров.
# Бесплатные тарифы стоят 0, но лимитированы по запросам в минуту.
PROVIDERS = {
    "claude": {
        "model": "claude-opus-5",
        "key": "ANTHROPIC_API_KEY",
        "price": (5.00, 25.00),
    },
    "gpt": {
        "model": "gpt-5",
        "key": "OPENAI_API_KEY",
        "price": (1.25, 10.00),
    },
    "gemini": {
        "model": "gemini-2.5-flash",
        "key": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "price": (0.0, 0.0),  # бесплатный тариф
    },
    "groq": {
        "model": "llama-3.3-70b-versatile",
        "key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "price": (0.0, 0.0),  # бесплатный тариф
    },
    "kimi": {
        "model": "kimi-k2-0905-preview",
        "key": "MOONSHOT_API_KEY",
        "base_url": "https://api.moonshot.ai/v1",
        "price": (0.60, 2.50),
    },
}


def cost(name: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = PROVIDERS[name]["price"]
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000


async def ask_claude(cfg: dict) -> tuple[str, int, int]:
    from anthropic import AsyncAnthropic

    async with AsyncAnthropic(api_key=os.environ[cfg["key"]]) as client:
        resp = await client.messages.create(
            model=cfg["model"],
            max_tokens=1024,
            messages=[{"role": "user", "content": PROMPT}],
        )
    text = "".join(block.text for block in resp.content if block.type == "text")
    return text, resp.usage.input_tokens, resp.usage.output_tokens


async def ask_openai_compatible(cfg: dict) -> tuple[str, int, int]:
    """GPT, Gemini, Groq и Kimi говорят одним протоколом — меняется только base_url."""
    from openai import AsyncOpenAI

    async with AsyncOpenAI(api_key=os.environ[cfg["key"]], base_url=cfg.get("base_url")) as client:
        resp = await client.chat.completions.create(
            model=cfg["model"],
            messages=[{"role": "user", "content": PROMPT}],
        )
    return resp.choices[0].message.content or "", resp.usage.prompt_tokens, resp.usage.completion_tokens


async def ask(name: str) -> None:
    cfg = PROVIDERS[name]
    call = ask_claude if name == "claude" else ask_openai_compatible
    try:
        text, tokens_in, tokens_out = await call(cfg)
    except Exception as e:
        print(f"=== {name} · {cfg['model']} ===\nошибка — {type(e).__name__}: {e}\n")
        return
    print(f"=== {name} · {cfg['model']} ===")
    print(text.strip())
    print(f"tokens: in={tokens_in} out={tokens_out}  cost=${cost(name, tokens_in, tokens_out):.6f}\n")


async def main() -> None:
    load_dotenv()
    available = [name for name, cfg in PROVIDERS.items() if os.getenv(cfg["key"])]
    if not available:
        keys = ", ".join(cfg["key"] for cfg in PROVIDERS.values())
        sys.exit(f"Нет ни одного ключа. Скопируй .env.example в .env и заполни любой из: {keys}")

    skipped = [name for name in PROVIDERS if name not in available]
    if skipped:
        print(f"пропущены без ключа: {', '.join(skipped)}\n")

    await asyncio.gather(*(ask(name) for name in available))


if __name__ == "__main__":
    assert cost("claude", 1_000_000, 0) == PROVIDERS["claude"]["price"][0]
    asyncio.run(main())
