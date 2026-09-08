"""Тесты недели 2. Пока падают — это нормально, их и надо погасить.

    uv run pytest weeks/m1-api/week-02/              # только быстрые, без сети и денег
    uv run pytest weeks/m1-api/week-02/ -m live      # реальные вызовы, тратит токены
"""

import pytest

from client import MODELS, Completion, LLMClient, Usage, cost

PROMPT = "Ответь одним словом: столица Франции?"

# Модели с ризонингом сначала тратят бюджет на невидимые размышления.
# При max_tokens=100 gpt-5-nano уходит в ноль видимого текста — на ответ
# из одного слова нужен запас в тысячи токенов, а не в сотни.
MAX_TOKENS = 2000


def test_cost():
    """Считается по цене за миллион токенов."""
    assert cost(5.0, 25.0, 1_000_000, 0) == 5.0
    assert cost(5.0, 25.0, 0, 1_000_000) == 25.0
    assert cost(1.0, 2.0, 500_000, 500_000) == pytest.approx(1.5)
    assert cost(5.0, 25.0, 0, 0) == 0.0


def test_output_costs_more():
    """Выход дороже входа у всех провайдеров — цены не перепутаны местами."""
    for tiers in MODELS.values():
        for _, price_in, price_out in tiers.values():
            assert price_out > price_in


def test_client_picks_model():
    """Категория выбирает модель и цены."""
    client = LLMClient("claude", tier="small")
    assert client.model == "claude-haiku-4-5"

    other = LLMClient("gpt", tier="frontier")
    assert other.model == "gpt-5"


def test_unknown_provider():
    """Неизвестный провайдер — понятная ошибка, а не KeyError."""
    with pytest.raises(ValueError):
        LLMClient("нет-такого")


@pytest.mark.live
@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["claude", "gpt"])
async def test_complete(provider):
    """Оба провайдера отвечают одинаковым интерфейсом."""
    client = LLMClient(provider, tier="small")
    result = await client.complete(PROMPT, max_tokens=MAX_TOKENS)

    assert isinstance(result, Completion)
    assert "ариж" in result.text.lower()  # Париж / Paris
    assert isinstance(result.usage, Usage)
    assert result.usage.input_tokens > 0
    assert result.usage.output_tokens > 0
    assert result.usage.cost > 0
    assert result.usage.seconds > 0


@pytest.mark.live
@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["claude", "gpt"])
async def test_stream(provider):
    """Стриминг отдаёт куски текста; статистика доступна после потока."""
    client = LLMClient(provider, tier="small")
    chunks = [chunk async for chunk in client.stream(PROMPT, max_tokens=MAX_TOKENS)]

    assert len(chunks) > 1, "должно прийти несколько кусков, иначе это не стриминг"
    assert "ариж" in "".join(chunks).lower()

    # Статистика появляется только после того, как поток закончился.
    assert client.last_usage is not None
    assert client.last_usage.output_tokens > 0
    assert client.last_usage.cost > 0


@pytest.mark.live
@pytest.mark.asyncio
async def test_system_prompt():
    """system влияет на ответ."""
    client = LLMClient("claude", tier="small")
    result = await client.complete(
        "Столица Франции?",
        system="Отвечай только заглавными буквами.",
        max_tokens=MAX_TOKENS,
    )
    assert result.text.strip() == result.text.strip().upper()
