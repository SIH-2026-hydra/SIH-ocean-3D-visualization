from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env files."""

    app_name: str = 'Ocean Intelligence API'
    app_env: str = 'development'
    api_v1_prefix: str = '/api/v1'
    host: str = '127.0.0.1'
    port: int = 8000
    frontend_origin: str = 'http://127.0.0.1:5173'
    # Prefer locally staged operational data. JSON remains available when it is
    # explicitly selected for fixtures and development.
    ocean_provider: str = 'auto'
    copernicus_temperature_path: str | None = None
    copernicus_salinity_path: str | None = None
    copernicus_current_u_path: str | None = None
    copernicus_current_v_path: str | None = None
    copernicus_data_dir: str | None = None
    copernicus_file_pattern: str = '*.nc'
    copernicus_validate_on_startup: bool = True
    copernicus_log_level: str = 'INFO'
    copernicus_cache_dir: str = 'app/data/operational_cache'
    copernicus_acquisition_enabled: bool = False
    # A bundle must span this regional envelope before ``auto`` treats it as
    # the operational Indian Ocean source. Small real-data extracts remain
    # useful for explicit development validation, but must never be promoted
    # to the default live platform dataset.
    copernicus_operational_min_latitude: float = -30.0
    copernicus_operational_max_latitude: float = 30.0
    copernicus_operational_min_longitude: float = 40.0
    copernicus_operational_max_longitude: float = 105.0
    max_response_cells: int = 100_000
    max_grid_dimension: int = 1_000
    max_response_size_bytes: int = 10_000_000

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )


settings = Settings()
