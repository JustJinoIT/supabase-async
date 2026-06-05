# Supabase Async 🔄

비동기 Supabase 클라이언트. ThreadPoolExecutor로 동기→비동기 변환.

## 특징

- ⚡ **비동기 지원**: 모든 DB 작업이 async
- 🔄 **자동 Retry**: Exponential backoff
- 💾 **Fallback 저장소**: DB 연결 실패 시 로컬 저장
- 🌩️ **Cloud Run 최적화**: OOM 없음, requests 기반

## 설치

```bash
pip install supabase-async
```

## 사용법

```python
import asyncio
from supabase_async import SupabaseAsync

db = SupabaseAsync(
    url="https://xxx.supabase.co",
    api_key="eyJ...",
    service_key="eyJ..."
)

async def main():
    # Insert
    await db.insert("contests", {
        "title": "2024 디자인 공모전",
        "deadline": "2024-12-31"
    })

    # Select
    contests = await db.select("contests", limit=10)

    # Update
    await db.update(
        "contests",
        {"id": "123"},
        {"status": "submitted"}
    )

    # Delete
    await db.delete("contests", {"id": "123"})

asyncio.run(main())
```

## API

### `SupabaseAsync(url, api_key, service_key=None, fallback_dir="/tmp/supabase-fallback")`

초기화.

### `await db.insert(table, data)`

데이터 삽입.

### `await db.select(table, filters=None, limit=100)`

데이터 조회.

**filters 예시:**
```python
contests = await db.select("contests", {"status": "new"}, limit=5)
```

### `await db.update(table, filters, data)`

데이터 업데이트.

### `await db.delete(table, filters)`

데이터 삭제.

### `await db.sync_fallback()`

Fallback 데이터를 DB로 동기화.

```python
synced = await db.sync_fallback()
print(f"{synced}건 동기화됨")
```

## 환경 변수

```bash
export SUPABASE_URL=https://xxx.supabase.co
export SUPABASE_KEY=eyJ...
export SUPABASE_SERVICE_KEY=eyJ...
```

## 라이선스

MIT
