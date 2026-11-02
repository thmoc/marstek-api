"""Async UDP client for the Marstek Device Local API (JSON-RPC over UDP)."""

from __future__ import annotations

import asyncio
import json
from typing import Any


class MarstekError(Exception):
    """Base error."""


class MarstekConnectionError(MarstekError):
    """Device did not answer."""


class MarstekApiError(MarstekError):
    """Device answered with an error."""


class _Protocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.queue: asyncio.Queue[bytes | Exception] = asyncio.Queue()

    def datagram_received(self, data: bytes, addr: Any) -> None:
        self.queue.put_nowait(data)

    def error_received(self, exc: Exception) -> None:
        self.queue.put_nowait(exc)


class MarstekClient:
    """Client talking to one Marstek device. Requests are serialised."""

    def __init__(
        self, host: str, port: int = 30000, timeout: float = 4.0, retries: int = 3
    ) -> None:
        self.host = host
        self.port = port
        self._timeout = timeout
        self._retries = retries
        self._lock = asyncio.Lock()
        self._id = 0

    async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Send a request and return the `result` object."""
        async with self._lock:
            for _ in range(self._retries):
                try:
                    return await self._once(method, params)
                except TimeoutError:
                    continue
                except OSError as err:
                    raise MarstekConnectionError(str(err)) from err
            raise MarstekConnectionError(
                f"No response from {self.host}:{self.port} for {method}"
            )

    async def _once(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._id = (self._id + 1) % 100000
        req_id = self._id
        loop = asyncio.get_running_loop()
        proto = _Protocol()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: proto, remote_addr=(self.host, self.port)
        )
        try:
            payload = {"id": req_id, "method": method, "params": params}
            transport.sendto(json.dumps(payload).encode())
            deadline = loop.time() + self._timeout
            while True:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    raise TimeoutError
                item = await asyncio.wait_for(proto.queue.get(), remaining)
                if isinstance(item, Exception):
                    raise item
                try:
                    msg = json.loads(item)
                except ValueError:
                    continue
                if msg.get("id") != req_id:
                    continue  # stale answer to an earlier request
                if "error" in msg:
                    raise MarstekApiError(str(msg["error"]))
                return msg.get("result", {})
        finally:
            transport.close()

    # --- reads -----------------------------------------------------------
    async def get_device(self) -> dict[str, Any]:
        return await self.request("Marstek.GetDevice", {"ble_mac": "0"})

    async def get_battery_status(self) -> dict[str, Any]:
        return await self.request("Bat.GetStatus", {"id": 0})

    async def get_es_status(self) -> dict[str, Any]:
        return await self.request("ES.GetStatus", {"id": 0})

    async def get_es_mode(self) -> dict[str, Any]:
        return await self.request("ES.GetMode", {"id": 0})

    # --- writes ----------------------------------------------------------
    async def set_mode(self, config: dict[str, Any]) -> None:
        result = await self.request("ES.SetMode", {"id": 0, "config": config})
        if not result.get("set_result"):
            raise MarstekApiError(f"Device rejected ES.SetMode: {config}")

    async def set_auto(self) -> None:
        await self.set_mode({"mode": "Auto", "auto_cfg": {"enable": 1}})

    async def set_ai(self) -> None:
        await self.set_mode({"mode": "AI", "ai_cfg": {"enable": 1}})

    async def set_ups(self) -> None:
        await self.set_mode({"mode": "UPS", "ups_cfg": {"enable": 1}})

    async def set_passive(self, power: int, duration: int) -> None:
        await self.set_mode(
            {"mode": "Passive", "passive_cfg": {"power": power, "cd_time": duration}}
        )

    async def set_manual(self, cfg: dict[str, Any]) -> None:
        await self.set_mode({"mode": "Manual", "manual_cfg": cfg})
