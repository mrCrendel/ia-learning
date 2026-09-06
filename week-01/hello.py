"""Один промпт — в Claude и в GPT. Печатает ответ, токены и стоимость."""

import asyncio
import os
import sys

from dotenv import load_dotenv

CLAUDE_MODEL = "claude-opus-5"
GPT_MODEL = "gpt-5"

# USD за 1M токенов (input, output). Проверь актуальные цены на сайтах провайдеров.
PRICES = {
    CLAUDE_MODEL: (5.00, 25.00),
    GPT_MODEL: (1.25, 10.00),
}

PROMPT = "Объясни в двух предложениях, что такое токен в LLM."


def cost(model: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = PRICES[model]
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000


def report(model: str, text: str, input_tokens: int, output_tokens: int) -> None:
    print(f"=== {model} ===")
    print(text.strip())
    print(f"tokens: in={input_tokens} out={output_tokens}  cost=${cost(model, input_tokens, output_tokens):.6f}\n")


async def ask_claude() -> None:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic()
    resp = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": PROMPT}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text")
    report(CLAUDE_MODEL, text, resp.usage.input_tokens, resp.usage.output_tokens)


async def ask_gpt() -> None:
    from openai import AsyncOpenAI

    client = AsyncOpenAI()
    resp = await client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": PROMPT}],
    )
    report(GPT_MODEL, resp.choices[0].message.content or "", resp.usage.prompt_tokens, resp.usage.completion_tokens)


async def main() -> None:
    load_dotenv()
    missing = [k for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY") if not os.getenv(k)]
    if missing:
        sys.exit(f"Нет ключей: {', '.join(missing)}. Скопируй .env.example в .env и заполни.")

    results = await asyncio.gather(ask_claude(), ask_gpt(), return_exceptions=True)
    for name, r in zip(("Claude", "GPT"), results):
        if isinstance(r, Exception):
            print(f"{name}: ошибка — {type(r).__name__}: {r}")


if __name__ == "__main__":
    assert cost(CLAUDE_MODEL, 1_000_000, 0) == PRICES[CLAUDE_MODEL][0]
    asyncio.run(main())
