"""
Quick test script to verify mock mode performance fixes.
Run this before load testing to confirm API responds quickly.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from eva_api.config import Settings
from eva_api.services.cosmos_service import CosmosDBService


async def test_mock_mode():
    """Test that mock mode returns instantly without Azure timeouts."""

    print("\n" + "="*70)
    print("🧪 Testing Mock Mode Performance")
    print("="*70 + "\n")

    # Test with mock mode enabled
    settings_mock = Settings(mock_mode=True, azure_timeout=5)
    cosmos_mock = CosmosDBService(settings_mock)

    print("✅ Mock mode enabled: True")
    print(f"✅ Azure timeout: {settings_mock.azure_timeout}s\n")

    # Test create_space (should be instant)
    print("Testing create_space...")
    start = time.time()
    space = await cosmos_mock.create_space(
        name="Test Space",
        description="Performance test"
    )
    elapsed = time.time() - start

    print(f"  ⏱️  Time: {elapsed*1000:.2f}ms")
    print(f"  📦 Space ID: {space['id']}")

    if elapsed < 0.1:  # Should be under 100ms
        print("  ✅ PASS - Instant response\n")
    else:
        print(f"  ❌ FAIL - Took {elapsed:.2f}s (expected <0.1s)\n")
        return False

    # Test get_space
    print("Testing get_space...")
    start = time.time()
    retrieved = await cosmos_mock.get_space(space['id'])
    elapsed = time.time() - start

    print(f"  ⏱️  Time: {elapsed*1000:.2f}ms")
    print(f"  📦 Retrieved: {retrieved['name']}")

    if elapsed < 0.1:
        print("  ✅ PASS - Instant response\n")
    else:
        print(f"  ❌ FAIL - Took {elapsed:.2f}s (expected <0.1s)\n")
        return False

    # Test list_spaces
    print("Testing list_spaces...")
    start = time.time()
    spaces, cursor, has_more = await cosmos_mock.list_spaces(limit=10)
    elapsed = time.time() - start

    print(f"  ⏱️  Time: {elapsed*1000:.2f}ms")
    print(f"  📦 Returned: {len(spaces)} spaces")

    if elapsed < 0.1:
        print("  ✅ PASS - Instant response\n")
    else:
        print(f"  ❌ FAIL - Took {elapsed:.2f}s (expected <0.1s)\n")
        return False

    # Benchmark 100 operations
    print("Benchmarking 100 create_space operations...")
    start = time.time()
    tasks = []
    for i in range(100):
        tasks.append(cosmos_mock.create_space(
            name=f"Benchmark Space {i}",
            description="Load test"
        ))

    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    ops_per_sec = 100 / elapsed

    print(f"  ⏱️  Total time: {elapsed:.2f}s")
    print(f"  🚀 Throughput: {ops_per_sec:.1f} ops/sec")
    print(f"  📊 Avg latency: {elapsed*1000/100:.2f}ms\n")

    if ops_per_sec > 500:  # Should handle 500+ ops/sec in mock mode
        print("  ✅ PASS - High throughput achieved\n")
    else:
        print(f"  ⚠️  WARNING - Throughput {ops_per_sec:.1f} ops/sec (expected >500)\n")

    print("="*70)
    print("✅ All mock mode tests passed!")
    print("="*70)
    print("\n💡 Ready for load testing with EVA_MOCK_MODE=true\n")

    return True


if __name__ == "__main__":
    result = asyncio.run(test_mock_mode())
    sys.exit(0 if result else 1)
