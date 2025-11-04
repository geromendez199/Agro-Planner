"""Cliente asincrónico para interactuar con las APIs de John Deere."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import httpx

from .config import get_settings

logger = logging.getLogger(__name__)


class JohnDeereClient:
    """Cliente para consumir las APIs de John Deere con OAuth 2."""

    def __init__(self, settings: Optional[Any] = None) -> None:
        self.settings = settings or get_settings()
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    async def _authenticate(self, force_refresh: bool = False) -> None:
        if self.settings.jd_fake_token:
            self._access_token = self.settings.jd_fake_token
            self._token_expires_at = time.time() + 3600
            return
        if not force_refresh and self._access_token and time.time() < self._token_expires_at - 30:
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
            self._access_token = token_json.get("access_token")
            expires_in = token_json.get("expires_in", 3600)
            self._token_expires_at = time.time() + int(expires_in)
            logger.info("Token de John Deere renovado correctamente")

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        *,
        retry_on_unauthorized: bool = True,
    ) -> Any:
        await self._authenticate()
        url = f"{self.settings.jd_api_base}{path}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, params=params, json=json, headers=headers)
            if response.status_code == 401 and retry_on_unauthorized:
                logger.info("Token expirado, renovando y reintentando solicitud")
                await self._authenticate(force_refresh=True)
                return await self._request(
                    method, path, params=params, json=json, retry_on_unauthorized=False
                )
            response.raise_for_status()
            if response.content:
                return response.json()
            return None

    async def list_equipment(self, item_limit: int = 100) -> Dict[str, Any]:
        page_offset = 0
        all_values: list[dict] = []
        while True:
            params = {
                "organizationIds": self.settings.org_id,
                "pageOffset": page_offset,
                "itemLimit": item_limit,
            }
            payload = await self._request("GET", "/equipment", params=params)
            values = payload.get("values", []) if payload else []
            all_values.extend(values)
            total = payload.get("total", 0) if payload else 0
            if not values or len(all_values) >= total:
                break
            page_offset += item_limit
        return {"values": all_values}

    async def list_fields(self) -> Dict[str, Any]:
        params = {
            "organizationId": self.settings.org_id,
        }
        return await self._request("GET", "/fields", params=params)

    async def list_field_operations(self, item_limit: int = 100) -> Dict[str, Any]:
        page_offset = 0
        operations: list[dict] = []
        while True:
            params = {
                "organizationId": self.settings.org_id,
                "pageOffset": page_offset,
                "itemLimit": item_limit,
            }
            payload = await self._request("GET", "/fieldOperations", params=params)
            values = payload.get("values", []) if payload else []
            operations.extend(values)
            total = payload.get("total", 0) if payload else 0
            if not values or len(operations) >= total:
                break
            page_offset += item_limit
        return {"values": operations}

    async def get_measurements(self, operation_id: str, measurement_type: Optional[str] = None) -> Any:
        path = f"/fieldOperations/{operation_id}/measurementTypes"
        if measurement_type:
            path = f"{path}/{measurement_type}"
        return await self._request("GET", path)

    async def create_work_plan(self, data: Dict[str, Any]) -> Any:
        path = f"/organizations/{self.settings.org_id}/workPlans"
        return await self._request("POST", path, json=data)

    async def update_work_plan(self, work_plan_id: str, data: Dict[str, Any]) -> Any:
        path = f"/organizations/{self.settings.org_id}/workPlans/{work_plan_id}"
        return await self._request("PUT", path, json=data)

    async def delete_work_plan(self, work_plan_id: str) -> Any:
        path = f"/organizations/{self.settings.org_id}/workPlans/{work_plan_id}"
        return await self._request("DELETE", path)