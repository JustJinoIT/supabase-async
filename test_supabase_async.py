"""
Supabase Async 테스트
"""

import asyncio
from pathlib import Path
import tempfile
from supabase_async import SupabaseAsync


async def test_init():
    """초기화 테스트."""
    db = SupabaseAsync(
        url="https://test.supabase.co",
        api_key="test_key",
        service_key="test_service_key",
        fallback_dir=tempfile.gettempdir()
    )

    assert db.url == "https://test.supabase.co"
    assert db.api_key == "test_key"
    assert db.service_key == "test_service_key"
    assert db.fallback_dir.exists()
    print("✅ test_init passed")


async def test_fallback_dir():
    """Fallback 디렉토리 생성 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = SupabaseAsync(
            url="https://test.supabase.co",
            api_key="test_key",
            fallback_dir=f"{tmpdir}/fallback"
        )

        assert Path(f"{tmpdir}/fallback").exists()
    print("✅ test_fallback_dir passed")


async def test_fallback_save():
    """Fallback 저장 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = SupabaseAsync(
            url="https://test.supabase.co",
            api_key="test_key",
            fallback_dir=tmpdir
        )

        # Fallback 저장 (DB 연결 실패 시뮬레이션)
        db._fallback_save("contests", {"id": "123", "title": "Test"})

        # 파일 확인
        fallback_file = Path(tmpdir) / "contests.jsonl"
        assert fallback_file.exists()

        # 내용 확인
        with open(fallback_file) as f:
            line = f.readline()
            assert "123" in line
            assert "Test" in line

    print("✅ test_fallback_save passed")


async def test_headers_setup():
    """HTTP 헤더 설정 테스트."""
    db = SupabaseAsync(
        url="https://test.supabase.co",
        api_key="test_key",
        service_key="test_service_key"
    )

    assert "apikey" in db._headers
    assert "Authorization" in db._headers
    assert "Content-Type" in db._headers
    assert db._headers["apikey"] == "test_service_key"
    print("✅ test_headers_setup passed")


async def test_sync_fallback_empty():
    """빈 Fallback 동기화 테스트."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = SupabaseAsync(
            url="https://test.supabase.co",
            api_key="test_key",
            fallback_dir=tmpdir
        )

        # 빈 fallback 동기화
        count = await db.sync_fallback()
        assert count == 0
    print("✅ test_sync_fallback_empty passed")


async def main():
    print("🧪 Supabase Async 테스트 시작\n")

    await test_init()
    await test_fallback_dir()
    await test_fallback_save()
    await test_headers_setup()
    await test_sync_fallback_empty()

    print("\n✅ 모든 테스트 통과!")


if __name__ == "__main__":
    asyncio.run(main())
