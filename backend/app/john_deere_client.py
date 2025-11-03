"""
Cliente asincrónico para interactuar con las APIs de John Deere.

Este módulo implementa la autenticación OAuth 2 mediante el flujo de credenciales
de cliente y proporciona métodos de alto nivel para llamar a los endpoints más
relevantes (Equipment, Fields, Field Operations y Work Plans).  Los métodos
devuelven objetos Python (dict) con los datos recibidos.

**Nota:** Este cliente no persiste información sensible y renueva el token
automáticamente cuando es necesario.  Los endpoints concretos pueden cambiar
con las actualizaciones de la API de John Deere; consulta la documentación
oficial para adaptarlos.
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx

from .config import get_settings


class JohnDeereClient:
    """Cliente para consumir las APIs de John Deere con OAuth 2.

    Args:
        settings: instancia de Settings con las configuraciones necesarias.
    """

    def __init__(self, settings: Optional[Any] = None) -> None:
        self.settings = settings or get_settings()
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    async def _authenticate(self) -> None:
        """Solicita un nuevo token de acceso cuando el actual expira.

        Realiza una solicitud POST al endpoint de autenticación configurado
        enviando las credenciales de cliente.  Almacena el token y su tiempo de
        expiración.
        """
        # Renueva sólo si el token está ausente o próximo a expirar (30 s de margen)
        if self._access_token and time.time() < self._token_expires_at - 30:
            return
        data = {
            "grant_type": "client_credentials",
            "client_id": self.settings.client_id,
            "client_secret": self.settings.client_secret,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.settings.jd_auth_url, data=data)
            response.raise_for_status()
            token_json = response.json()
            # La respuesta debe incluir `access_token` y `expires_in`
            self._access_token = token_json.get("access_token")
            expires_in = token_json.get("expires_in", 3600)
            self._token_expires_at = time.time() + int(expires_in)

    async def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None,
                       json: Optional[Dict[str, Any]] = None) -> Any:
        """Realiza una solicitud HTTP autenticada al API de John Deere.

        Args:
            method: Método HTTP (GET, POST, PUT...).
            path: Ruta relativa dentro del API base (debe comenzar con `/`).
            params: Parámetros de la query string.
            json: Cuerpo JSON para solicitudes POST o PUT.

        Returns:
            Un objeto Python con la respuesta JSON.
        """
        await self._authenticate()
        url = f"{self.settings.jd_api_base}{path}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, params=params, json=json, headers=headers)
            response.raise_for_status()
            if response.content:
                return response.json()
            return None

    # Equipos
    async def list_equipment(self, page_offset: int = 0, item_limit: int = 100) -> Any:
        """Lista el equipo de la organización utilizando la nueva Equipment API.

        Args:
            page_offset: Desplazamiento de página (0 = primera página).
            item_limit: Número de elementos por página.

        Returns:
            Un diccionario con los registros de equipo.
        """
        params = {
            "organizationIds": self.settings.org_id,
            "pageOffset": page_offset,
            "itemLimit": item_limit,
        }
        return await self._request("GET", "/equipment", params=params)

    # Campos
    async def list_fields(self) -> Any:
        """Obtiene los campos/boundaries de la organización.

        Este endpoint está sujeto a cambios.  Utiliza la API de campos para
        recuperar los límites geoespaciales de cada lote.
        """
        params = {
            "organizationId": self.settings.org_id,
        }
        return await self._request("GET", "/fields", params=params)

    # Field Operations
    async def get_field_operation(self, operation_id: str) -> Any:
        """Recupera una operación de campo específica.

        Args:
            operation_id: Identificador de la operación de campo.
        Returns:
            La operación de campo con sus detalles y la lista de productos.
        """
        return await self._request("GET", f"/fieldOperations/{operation_id}")

    async def get_field_operation_measurements(self, operation_id: str, measurement_type: Optional[str] = None) -> Any:
        """Obtiene las mediciones de una operación de campo.

        Args:
            operation_id: Identificador de la operación.
            measurement_type: Tipo de medición (opcional) para filtrar.

        Returns:
            Datos de medición asociados a la operación.
        """
        path = f"/fieldOperations/{operation_id}/measurementTypes"
        if measurement_type:
            path = f"{path}/{measurement_type}"
        return await self._request("GET", path)

    # Work Plans
    async def create_work_plan(self, data: Dict[str, Any]) -> Any:
        """Crea un plan de trabajo en Operations Center.

        Args:
            data: Objeto JSON con la información del plan (campo, tarea, fechas, productos).
        Returns:
            Respuesta de la API con el plan creado.
        """
        # El endpoint típico es /organizations/{org_id}/workPlans
        path = f"/organizations/{self.settings.org_id}/workPlans"
        return await self._request("POST", path, json=data)