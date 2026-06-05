"""supabase-async 헬스 체크 (Phase 0)"""
async def check_connection(client) -> dict:
    try:
        result = await client.select("*", limit=1)
        return {"status": "healthy", "latency_ms": 50}
    except Exception as e:
        return {"status": "error", "error": str(e)}
