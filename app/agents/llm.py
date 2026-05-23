from langchain_anthropic import ChatAnthropic

from app.config import get_settings


def get_llm(temperature: float = 0.3, max_tokens: int = 2048) -> ChatAnthropic:
    s = get_settings()
    return ChatAnthropic(
        model=s.anthropic_model,
        api_key=s.anthropic_api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=60,
    )
