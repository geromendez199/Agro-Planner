"""
Módulo de configuración para el proyecto Agro Planner.

Utiliza Pydantic para cargar variables de entorno de forma tipada.  Las opciones se
pueden configurar mediante un archivo `.env` en la raíz del repositorio o a través
de variables de entorno del sistema.  Para acceder a la configuración desde
otros módulos, importa y llama a `get_settings()`.
"""

from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Clase de configuración principal.

    Atributos:
        client_id: Identificador de cliente OAuth 2 proporcionado por John Deere.
        client_secret: Secreto de cliente OAuth 2.
        org_id: Identificador de la organización en Operations Center.
        jd_auth_url: URL del endpoint de autenticación de John Deere.
        jd_api_base: URL base para las APIs de John Deere (Equipment API).
        db_url: Cadena de conexión a la base de datos.
        backend_cors_origins: Comma‑separated list de orígenes permitidos para CORS.
        scheduler_interval_seconds: Intervalo en segundos para las tareas programadas.
        secret_key: Clave secreta para firmar JWT (si se usa autenticación local).
        algorithm: Algoritmo de firma JWT.
        access_token_expire_minutes: Tiempo de expiración del token JWT.
    """

    client_id: str = Field(..., env="CLIENT_ID")
    client_secret: str = Field(..., env="CLIENT_SECRET")
    org_id: str = Field(..., env="ORG_ID")
    jd_auth_url: str = Field(..., env="JD_AUTH_URL")
    jd_api_base: str = Field(..., env="JD_API_BASE")
    db_url: str = Field("sqlite:///./agroplanner.db", env="DB_URL")
    backend_cors_origins: str = Field("", env="BACKEND_CORS_ORIGINS")
    scheduler_interval_seconds: int = Field(300, env="SCHEDULER_INTERVAL_SECONDS")
    secret_key: str = Field("", env="SECRET_KEY")
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Obtiene una instancia de Settings cacheada para reutilizar en toda la aplicación."""
    return Settings()