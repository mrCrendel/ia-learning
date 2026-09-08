"""Неделя 2 · LLMClient — единый интерфейс к провайдерам.

Anthropic ходит своим SDK, остальные — OpenAI-совместимым. Вся разница
спрятана внутри класса: снаружи complete() и stream() выглядят одинаково.

    uv run pytest weeks/m1-api/week-02/          # быстрые, без денег
    uv run pytest weeks/m1-api/week-02/ -m live  # реальные вызовы
"""

import os
import time
from dataclasses import dataclass
from typing import AsyncIterator, Literal

from dotenv import load_dotenv

load_dotenv()  # ключи из .env в корне репозитория

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

# temperature пережила две зачистки:
#   - у Anthropic её вырезали из API целиком, в SDK такого аргумента больше нет;
#   - у OpenAI модели с ризонингом (gpt-5*) принимают только значение по умолчанию.
# Остаётся рабочей у gemini, groq, kimi. Проверяй при смене модели.
NO_TEMPERATURE = {"gpt-5", "gpt-5-mini", "gpt-5-nano"}


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
    """Стоимость вызова в USD."""
    return (tokens_in * price_in + tokens_out * price_out) / 1_000_000


class LLMClient:
    """Единый интерфейс к провайдеру.

    После stream() статистика лежит в last_usage — полное число токенов
    приходит только в конце потока, раньше его физически нет.
    """

    def __init__(self, provider: str, tier: Tier = "mid") -> None:
        if provider not in MODELS:
            raise ValueError(f"Неизвестный провайдер {provider!r}. Есть: {', '.join(MODELS)}")

        self.provider = provider
        self.tier = tier
        self.model, self.price_in, self.price_out = MODELS[provider][tier]
        self.base_url = BASE_URLS.get(provider)
        self.last_usage: Usage | None = None

    def _key(self) -> str:
        """Ключ читается при вызове, а не в __init__ — клиент создаётся без секретов."""
        name = API_KEYS[self.provider]
        key = os.getenv(name)
        if not key:
            raise RuntimeError(f"Нет {name} в .env")
        return key

    def _usage(self, tokens_in: int, tokens_out: int, started: float) -> Usage:
        return Usage(
            input_tokens=tokens_in,
            output_tokens=tokens_out,
            cost=cost(self.price_in, self.price_out, tokens_in, tokens_out),
            seconds=time.perf_counter() - started,
        )

    def _anthropic_args(self, prompt: str, system: str | None, max_tokens: int) -> dict:
        """У Anthropic system — отдельное поле запроса, не сообщение.

        temperature здесь нет намеренно: SDK её больше не принимает.
        """
        args: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            args["system"] = system
        return args

    def _openai_args(self, prompt: str, system: str | None, temperature: float, max_tokens: int) -> dict:
        """У OpenAI system — первое сообщение в списке, отдельного поля нет."""
        messages = [{"role": "user", "content": prompt}]
        if system:
            messages.insert(0, {"role": "system", "content": system})

        args: dict = {
            "model": self.model,
            "messages": messages,
            "max_completion_tokens": max_tokens,  # gpt-5 не принимает max_tokens
        }
        if self.model not in NO_TEMPERATURE:
            args["temperature"] = temperature
        return args

    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> Completion:
        """Один вызов, полный ответ."""
        started = time.perf_counter()

        if self.provider == "claude":
            from anthropic import AsyncAnthropic

            async with AsyncAnthropic(api_key=self._key()) as client:
                resp = await client.messages.create(
                    **self._anthropic_args(prompt, system, max_tokens)
                )
            text = "".join(block.text for block in resp.content if block.type == "text")
            tokens_in, tokens_out = resp.usage.input_tokens, resp.usage.output_tokens
        else:
            from openai import AsyncOpenAI

            async with AsyncOpenAI(api_key=self._key(), base_url=self.base_url) as client:
                resp = await client.chat.completions.create(
                    **self._openai_args(prompt, system, temperature, max_tokens)
                )
            text = resp.choices[0].message.content or ""
            tokens_in, tokens_out = resp.usage.prompt_tokens, resp.usage.completion_tokens

        self.last_usage = self._usage(tokens_in, tokens_out, started)
        return Completion(text=text, usage=self.last_usage, model=self.model)

    async def stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """Куски текста по мере генерации; статистика — в last_usage после потока.

        Почему через атрибут, а не последним элементом потока: тогда каждый
        элемент — просто текст, и вызывающему не надо на каждой итерации
        проверять, не приехала ли вместо текста статистика.
        """
        started = time.perf_counter()
        tokens_in = tokens_out = 0
        self.last_usage = None

        if self.provider == "claude":
            from anthropic import AsyncAnthropic

            async with AsyncAnthropic(api_key=self._key()) as client:
                async with client.messages.stream(
                    **self._anthropic_args(prompt, system, max_tokens)
                ) as stream:
                    async for chunk in stream.text_stream:
                        yield chunk
                    final = await stream.get_final_message()
                    tokens_in, tokens_out = final.usage.input_tokens, final.usage.output_tokens
        else:
            from openai import AsyncOpenAI

            async with AsyncOpenAI(api_key=self._key(), base_url=self.base_url) as client:
                stream = await client.chat.completions.create(
                    **self._openai_args(prompt, system, temperature, max_tokens),
                    stream=True,
                    stream_options={"include_usage": True},  # иначе usage в потоке не придёт
                )
                async for event in stream:
                    if event.usage:  # последнее событие: текста нет, только статистика
                        tokens_in, tokens_out = event.usage.prompt_tokens, event.usage.completion_tokens
                    if event.choices and (piece := event.choices[0].delta.content):
                        yield piece

        self.last_usage = self._usage(tokens_in, tokens_out, started)
