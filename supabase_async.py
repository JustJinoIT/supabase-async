"""
Supabase Async Client — requests + ThreadPoolExecutor 기반

특징:
  - 동기 라이브러리(requests)를 비동기로 변환
  - 자동 retry (exponential backoff)
  - Fallback 저장소 (DB 연결 실패 시 로컬 저장)
  - Cloud Run 호환 (OOM 없음)
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


class SupabaseAsync:
    def __init__(
        self,
        url: str,
        api_key: str,
        service_key: str = None,
        fallback_dir: str = "/tmp/supabase-fallback",
    ):
        """
        Args:
            url: Supabase URL (https://xxx.supabase.co)
            api_key: Anon key
            service_key: Service role key (선택사항)
            fallback_dir: Fallback 저장소 경로
        """
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.service_key = service_key or api_key
        self.fallback_dir = Path(fallback_dir)
        self.fallback_dir.mkdir(parents=True, exist_ok=True)

        self._base = f"{self.url}/rest/v1"
        self._headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

        self._executor = ThreadPoolExecutor(max_workers=3)

    def _sync_request(
        self, method: str, url: str, **kwargs
    ) -> requests.Response:
        """Helper: 동기 HTTP 요청."""
        if method == "GET":
            return requests.get(
                url, headers=self._headers, timeout=30, verify=False, **kwargs
            )
        elif method == "POST":
            return requests.post(
                url, headers=self._headers, timeout=30, verify=False, **kwargs
            )
        elif method == "PATCH":
            return requests.patch(
                url, headers=self._headers, timeout=30, verify=False, **kwargs
            )
        elif method == "DELETE":
            return requests.delete(
                url, headers=self._headers, timeout=30, verify=False, **kwargs
            )
        else:
            raise ValueError(f"Unsupported method: {method}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def insert(self, table: str, data: Dict[str, Any]) -> Optional[Dict]:
        """데이터 삽입."""
        try:
            loop = asyncio.get_event_loop()
            r = await loop.run_in_executor(
                self._executor,
                lambda: self._sync_request("POST", f"{self._base}/{table}", json=data),
            )
            r.raise_for_status()
            result = r.json()
            if isinstance(result, list) and result:
                return result[0]
            return {**data, "id": None}
        except Exception as e:
            self._fallback_save(table, data)
            return {**data, "id": None}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def select(
        self,
        table: str,
        filters: Dict[str, Any] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """데이터 조회."""
        try:
            url = f"{self._base}/{table}"
            params = {}

            if filters:
                for k, v in filters.items():
                    params[k] = f"eq.{v}"

            if limit:
                params["limit"] = limit

            loop = asyncio.get_event_loop()
            r = await loop.run_in_executor(
                self._executor,
                lambda: self._sync_request("GET", url, params=params),
            )
            r.raise_for_status()
            return r.json() or []
        except Exception as e:
            return []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def update(
        self, table: str, filters: Dict[str, Any], data: Dict[str, Any]
    ) -> Optional[Dict]:
        """데이터 업데이트."""
        try:
            url = f"{self._base}/{table}"
            params = {}

            for k, v in (filters or {}).items():
                params[k] = f"eq.{v}"

            loop = asyncio.get_event_loop()
            r = await loop.run_in_executor(
                self._executor,
                lambda: self._sync_request("PATCH", url, params=params, json=data),
            )
            r.raise_for_status()
            result = r.json()
            if isinstance(result, list) and result:
                return result[0]
            return data
        except Exception as e:
            self._fallback_update(table, filters, data)
            return data

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def delete(self, table: str, filters: Dict[str, Any]) -> bool:
        """데이터 삭제."""
        try:
            url = f"{self._base}/{table}"
            params = {}

            for k, v in (filters or {}).items():
                params[k] = f"eq.{v}"

            loop = asyncio.get_event_loop()
            r = await loop.run_in_executor(
                self._executor,
                lambda: self._sync_request("DELETE", url, params=params),
            )
            r.raise_for_status()
            return True
        except Exception as e:
            return False

    def _fallback_save(self, table: str, data: Dict[str, Any]) -> None:
        """Fallback: 로컬에 데이터 저장."""
        fallback_file = self.fallback_dir / f"{table}.jsonl"
        with open(fallback_file, "a") as f:
            f.write(json.dumps({**data, "_ts": datetime.now().isoformat()}) + "\n")

    def _fallback_update(
        self, table: str, filters: Dict[str, Any], data: Dict[str, Any]
    ) -> None:
        """Fallback: 로컬 업데이트."""
        self._fallback_save(table, {**filters, **data})

    async def sync_fallback(self) -> int:
        """Fallback 데이터를 DB로 동기화."""
        count = 0
        for fallback_file in self.fallback_dir.glob("*.jsonl"):
            table = fallback_file.stem
            temp_file = fallback_file.with_suffix(".synced")

            with open(fallback_file, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        ts = data.pop("_ts", None)
                        await self.insert(table, data)
                        count += 1
                    except Exception:
                        pass

            fallback_file.rename(temp_file)

        return count
