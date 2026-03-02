"""Dependency injection for FastAPI."""

from __future__ import annotations

from functools import lru_cache

from benchlab.config import BenchLabConfig, load_config
from benchlab.runner.ollama_client import OllamaClient
from benchlab.storage.elasticsearch import ElasticsearchStorage


@lru_cache
def get_config() -> BenchLabConfig:
    return load_config()


_storage: ElasticsearchStorage | None = None
_ollama: OllamaClient | None = None


def get_storage() -> ElasticsearchStorage:
    global _storage
    if _storage is None:
        config = get_config()
        _storage = ElasticsearchStorage(config.elasticsearch)
    return _storage


def get_ollama() -> OllamaClient:
    global _ollama
    if _ollama is None:
        config = get_config()
        _ollama = OllamaClient(config.ollama)
    return _ollama


async def cleanup() -> None:
    global _storage, _ollama
    if _storage:
        await _storage.close()
        _storage = None
    if _ollama:
        await _ollama.close()
        _ollama = None
