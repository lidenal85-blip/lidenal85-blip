from typing import Dict, Type, Optional
from survey_finder.adapters.base import BaseAdapter, AdapterConfig
from survey_finder.logging.logger import init_logger

logger = init_logger()


class AdapterRegistry:
    """Registry for survey source adapters."""

    _adapters: Dict[str, Type[BaseAdapter]] = {}

    @classmethod
    def register(cls, name: str, adapter_class: Type[BaseAdapter]) -> None:
        cls._adapters[name] = adapter_class
        logger.info("adapter_registered", name=name)

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseAdapter]]:
        return cls._adapters.get(name)

    @classmethod
    def list_sources(cls) -> list[str]:
        return list(cls._adapters.keys())

    @classmethod
    def create_adapter(cls, name: str, config: AdapterConfig) -> BaseAdapter:
        adapter_class = cls.get(name)
        if not adapter_class:
            raise ValueError(f"Adapter '{name}' not registered")
        return adapter_class(config)


class AdapterService:
    """Service for managing adapters."""

    def __init__(self):
        self.registry = AdapterRegistry()
        self._active_adapters: Dict[str, BaseAdapter] = {}

    def get_adapter(self, name: str, config: Optional[AdapterConfig] = None) -> BaseAdapter:
        if name in self._active_adapters:
            return self._active_adapters[name]

        if config is None:
            config = AdapterConfig(source=name)

        adapter = self.registry.create_adapter(name, config)
        self._active_adapters[name] = adapter
        return adapter

    async def close_all(self) -> None:
        for name, adapter in self._active_adapters.items():
            await adapter.close()
            logger.info("adapter_closed", name=name)
        self._active_adapters.clear()


# Register adapters
try:
    from survey_finder.adapters.prolific.adapter import ProlificAdapter
    AdapterRegistry.register("prolific", ProlificAdapter)
except ImportError:
    pass

try:
    from survey_finder.adapters.cloudresearch.adapter import CloudResearchAdapter
    AdapterRegistry.register("cloudresearch", CloudResearchAdapter)
except ImportError:
    pass

try:
    from survey_finder.adapters.respondent.adapter import RespondentAdapter
    AdapterRegistry.register("respondent", RespondentAdapter)
except ImportError:
    pass
