import json

from bento_lib.logging import LogLevelLiteral
from fastapi import Depends
from functools import lru_cache
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, EnvSettingsSource, PydanticBaseSettingsSource, SettingsConfigDict
from typing import Annotated, Any, Literal

from .constants import SERVICE_TYPE

__all__ = [
    "Config",
    "get_config",
    "ConfigDependency",
]


class CorsOriginsParsingSource(EnvSettingsSource):
    def prepare_field_value(self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool) -> Any:
        if field_name == "cors_origins":
            return tuple(x.strip() for x in value.split(";")) if value is not None else ()
        return json.loads(value) if value_is_complex else value


class Config(BaseSettings):
    bento_debug: bool = False
    bento_container_local: bool = False

    service_id: str = str(":".join(list(SERVICE_TYPE.values())[:2]))
    service_name: str = "Bento Drop Box Service"
    service_description: str = "Drop box service for a Bento platform node."
    service_contact_url: str = "mailto:info@c3g.ca"
    service_url: str = "http://127.0.0.1:5000"  # base URL to construct object URIs from

    service_data: str = "data/"
    service_data_source: Literal["local"] = "local"
    traversal_limit: int = 16

    bento_authz_service_url: str  # Bento authorization service base URL
    authz_enabled: bool = True

    cors_origins: tuple[str, ...]

    log_level: LogLevelLiteral = "debug"

    # Make Config instances hashable + immutable
    model_config = SettingsConfigDict(frozen=True)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (CorsOriginsParsingSource(settings_cls),)


@lru_cache()
def get_config() -> Config:
    return Config()


ConfigDependency = Annotated[Config, Depends(get_config)]
