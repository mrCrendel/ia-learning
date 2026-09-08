"""Неделя 2 · LLMClient — единый интерфейс к провайдерам.

Каркас: сигнатуры и типы заданы, тела методов писать тебе.
Проверка — `uv run pytest week-02/`.

Что нужно сделать:
  1. complete() — обычный вызов, вернуть Completion с текстом и статистикой.
  2. stream() — асинхронный итератор кусков текста; итоговый Usage
     доступен после того, как поток закончился.
  3. Один и тот же код вызова работает и для Anthropic, и для OpenAI-совместимых.

Подумай до кода: как stream() отдаст и куски текста, и статистику в конце?
Варианта два — отдельный метод/атрибут после итерации, или последний
элемент потока особого типа. Оба рабочие, выбери и объясни почему.
"""

from dataclasses import dataclass
from typing import AsyncIterator, Literal

Tier = Literal["frontier", "mid", "small"]

# USD за 1M токенов (input, output). Цены меняются — проверяй у провайдера.
MODELS: dict[str, dict[Tier, tuple[str, float, float]]] = {
    "claude": {
        "frontier": ("claude-opus-5", 5.00, 25.00),
        "mid": ("claude-sonnet-5", 2.00, 10.00),
        "small": ("claude-haiku-4-5", 1.00, 5.00),
    },
    "gpt": {
        "frontier": ("gpt-5", 1.25, 10.00),
        "mid": ("gpt-5-mini", 0.25, 2.00),
        "small": ("gpt-5-nano", 0.05, 0.40),
    },
}

BASE_URLS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "groq": "https://api.groq.com/openai/v1",
    "kimi": "https://api.moonshot.ai/v1",
}

API_KEYS = {
    "claude": "ANTHROPIC_API_KEY",
    "gpt": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "kimi": "MOONSHOT_API_KEY",
}


@dataclass
class Usage:
    """Расход одного вызова."""

    input_tokens: int
    output_tokens: int
    cost: float
    seconds: float


@dataclass
class Completion:
    """Результат complete(): текст плюс статистика."""

    text: str
    usage: Usage
    model: str


def cost(price_in: float, price_out: float, tokens_in: int, tokens_out: int) -> float:
    """Стоимость вызова в USD. Реализовано — образец того, как считать."""
    return (tokens_in * price_in + tokens_out * price_out) / 1_000_000


class LLMClient:
    """Единый интерфейс к провайдеру.

    Anthropic ходит своим SDK, остальные — OpenAI-совместимым.
    Разница должна остаться внутри класса: снаружи вызов выглядит одинаково.
    """

    def __init__(self, provider: str, tier: Tier = "mid") -> None:
        self.provider = provider
        self.tier = tier
        model, price_in, price_out = MODELS[provider][tier]
        self.model = model
        self.price_in = price_in
        self.price_out = price_out

    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> Completion:
        """Один вызов, полный ответ.

        system идёт отдельным полем у Anthropic и первым сообщением
        с ролью "system" у OpenAI — это одно из мест, где протоколы расходятся.
        """

        call = ask_claude if self.provider == "claude" else ask_openai_compatible
        started = time.perf_counter()
        try:
            text, tokens_in, tokens_out = await call(cfg, self.model)
        except Exception as e:
            return None
        
        elapsed = time.perf_counter() - started
        usage = Completion(
            input_tokens = resp.usage.input_tokens,
            output_tokens = resp.usage.output_tokens,
            cost = cost(self.price_in, self.price_out, tokens_in, tokens_out),
            seconds = elapsed
        )
        
        return Completion(text, usage, self.model)

    async def stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """Куски текста по мере генерации.

        Полное число токенов известно только в конце потока —
        реши, как отдать Usage после того, как итерация закончилась.
        """
        # raise NotImplementedError
        yield self.complete(prompt, system, temperature, max_tokens)

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
        
    async def cost(price_in: float, price_out: float, tokens_in: int, tokens_out: int) -> float:
        return (tokens_in * price_in + tokens_out * price_out) / 1_000_000