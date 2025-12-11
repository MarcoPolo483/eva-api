"""Script to install and start Redis for local development.

For Windows, Redis can be run using:
1. Docker (recommended)
2. WSL2 with Redis installed
3. Windows Redis port (memurai.com)

This script uses Docker for cross-platform compatibility.
"""

import subprocess
import sys
import time


def check_docker():
    """Check if Docker is installed and running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def start_redis_docker():
    """Start Redis using Docker."""
    print("🚀 Starting Redis in Docker...")
    
    # Stop any existing Redis container
    subprocess.run(
        ["docker", "stop", "eva-redis"],
        capture_output=True
    )
    subprocess.run(
        ["docker", "rm", "eva-redis"],
        capture_output=True
    )
    
    # Start Redis container
    cmd = [
        "docker", "run",
        "--name", "eva-redis",
        "-d",
        "-p", "6379:6379",
        "redis:7-alpine",
        "redis-server",
        "--appendonly", "yes"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Redis container started successfully")
        print("   Container: eva-redis")
        print("   Host: localhost")
        print("   Port: 6379")
        print("\nWaiting for Redis to be ready...")
        time.sleep(2)
        
        # Test connection
        test_cmd = ["docker", "exec", "eva-redis", "redis-cli", "ping"]
        test_result = subprocess.run(test_cmd, capture_output=True, text=True)
        
        if test_result.returncode == 0 and "PONG" in test_result.stdout:
            print("✅ Redis is ready!")
            return True
        else:
            print("⚠️ Redis started but connection test failed")
            return False
    else:
        print(f"❌ Failed to start Redis: {result.stderr}")
        return False


def check_redis_connection():
    """Check if Redis is accessible."""
    try:
        import redis.asyncio as redis
        import asyncio
        
        async def test():
            client = redis.Redis(host="localhost", port=6379, decode_responses=True)
            try:
                await client.ping()
                return True
            except Exception as e:
                print(f"Redis connection test failed: {e}")
                return False
            finally:
                await client.aclose()
        
        return asyncio.run(test())
    except ImportError:
        print("⚠️ redis-py not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "redis==5.0.1"])
        return check_redis_connection()


def main():
    """Main installation workflow."""
    print("=" * 60)
    print("EVA API - Redis Setup")
    print("=" * 60)
    print()
    
    # Check Docker
    if not check_docker():
        print("❌ Docker is not installed or not running")
        print("\nPlease install Docker Desktop:")
        print("   https://www.docker.com/products/docker-desktop")
        print("\nAlternatively, install Redis manually:")
        print("   Windows: https://github.com/tporadowski/redis/releases")
        print("   WSL2: sudo apt-get install redis-server")
        return 1
    
    print("✅ Docker is available")
    print()
    
    # Start Redis
    if not start_redis_docker():
        return 1
    
    print()
    
    # Test connection
    print("🔍 Testing Redis connection from Python...")
    if check_redis_connection():
        print("✅ Redis connection successful!")
        print()
        print("=" * 60)
        print("Redis is ready for use!")
        print("=" * 60)
        print()
        print("To stop Redis:")
        print("   docker stop eva-redis")
        print()
        print("To start Redis again:")
        print("   docker start eva-redis")
        print()
        print("To view Redis logs:")
        print("   docker logs eva-redis")
        return 0
    else:
        print("❌ Redis connection failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
