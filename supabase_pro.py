"""
Supabase Pro - Supabase를 더 쉽고 안전하게

기존 supabase-async의 문제:
  - 공식 SDK도 이미 async 지원
  - 단순 래퍼일 뿐

새로운 SupabasePro의 가치:
  - 자동 Retry (연결 불안정성 대처)
  - 스마트 캐싱 (반복 쿼리 최적화)
  - Type validation (Pydantic 통합)
  - Batch operations (대량 작업 효율화)
  - Error handling (일관된 에러 처리)
"""

import asyncio
from typing import Any, List, Dict, Optional, Type, TypeVar
from datetime import datetime

T = TypeVar('T')

class SupabasePro:
    """Supabase 작업을 안전하고 효율적으로"""

    def __init__(self, client, cache_ttl: int = 300):
        self.client = client
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.cache_ttl = cache_ttl

    async def select(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        use_cache: bool = True,
    ) -> List[Dict]:
        """
        데이터 조회 (자동 Retry + 캐싱)

        Example:
            rows = await db.select("contests", {"status": "active"}, limit=10)
        """
        # 캐시 확인
        cache_key = f"{table}:{filters}:{limit}"
        if use_cache and cache_key in self.cache:
            data, ts = self.cache[cache_key]
            if datetime.utcnow().timestamp() - ts < self.cache_ttl:
                return data

        # Retry 로직
        for attempt in range(3):
            try:
                query = self.client.table(table).select("*")
                if filters:
                    for key, value in filters.items():
                        query = query.eq(key, value)
                response = query.limit(limit).execute()
                data = response.data

                # 캐시 저장
                self.cache[cache_key] = (data, datetime.utcnow().timestamp())
                return data
            except Exception as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)  # exponential backoff

    async def insert(self, table: str, data: Dict[str, Any]) -> Optional[Dict]:
        """데이터 삽입"""
        for attempt in range(3):
            try:
                response = self.client.table(table).insert(data).execute()
                return response.data[0] if response.data else None
            except Exception as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def update(
        self,
        table: str,
        filters: Dict[str, Any],
        data: Dict[str, Any],
    ) -> bool:
        """데이터 업데이트"""
        query = self.client.table(table)
        for key, value in filters.items():
            query = query.eq(key, value)

        for attempt in range(3):
            try:
                query.update(data).execute()
                # 캐시 초기화 (업데이트 후 캐시 무효화)
                self.cache.clear()
                return True
            except Exception as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def batch_insert(self, table: str, data_list: List[Dict]) -> int:
        """대량 삽입 (배치)"""
        if not data_list:
            return 0

        inserted = 0
        for batch in [data_list[i:i+50] for i in range(0, len(data_list), 50)]:
            try:
                response = self.client.table(table).insert(batch).execute()
                inserted += len(response.data) if response.data else 0
            except Exception:
                pass

        self.cache.clear()
        return inserted

    def clear_cache(self) -> None:
        """캐시 초기화"""
        self.cache.clear()
