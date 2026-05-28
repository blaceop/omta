from openai import OpenAI

from app.config import get_settings
from app.utils.errors import ValidationError


def get_openai_client() -> OpenAI:
    settings = get_settings()
    if not settings.llm_api_key.strip():
        raise ValidationError(
            "LLM API key is missing. Set LLM_API_KEY in backend/.env before running LLM steps. "
            "For Alibaba Cloud Bailian, also set LLM_BASE_URL and LLM_MODEL."
        )
    client_kwargs = {"api_key": settings.llm_api_key}
    if settings.llm_base_url:
        client_kwargs["base_url"] = settings.llm_base_url
    return OpenAI(**client_kwargs)


def get_default_model() -> str:
    return get_settings().llm_model
