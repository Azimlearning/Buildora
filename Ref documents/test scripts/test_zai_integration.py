"""
Test Z.AI GLM API Integration

Quick test script to verify the Z.AI API key and endpoint are working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.core.glm_client import GLMClient


async def test_zai_connection():
    """Test basic Z.AI API connection"""
    print("=" * 60)
    print("Z.AI GLM API Integration Test")
    print("=" * 60)

    client = GLMClient()

    print(f"\n[OK] Configuration loaded:")
    print(f"  - API URL: {client.api_url}")
    print(f"  - Model: {client.model}")
    print(f"  - API Key: {client.api_key[:20]}...{client.api_key[-10:]}")

    print("\n[...] Testing API connection...")

    try:
        response = await client.chat_completion(
            prompt="Hello! Please respond with a simple greeting.",
            temperature=0.7,
            max_tokens=50
        )

        content = response["choices"][0]["message"]["content"]

        print("\n[SUCCESS] Z.AI API is working correctly!")
        print(f"\n[Response from {client.model}]")
        print(f"   {content}")

        return True

    except ValueError as e:
        print(f"\n[ERROR] AUTHENTICATION ERROR:")
        print(f"   {str(e)}")
        return False

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}:")
        print(f"   {str(e)}")
        return False

    finally:
        await client.close()
        print("\n" + "=" * 60)


async def test_json_extraction():
    """Test JSON extraction capability"""
    print("\n" + "=" * 60)
    print("Testing JSON Extraction")
    print("=" * 60)

    client = GLMClient()

    prompt = """
    Extract the following information as JSON:

    Project: Marina Bay Construction
    Start Date: 2024-01-15
    Budget: $2,500,000
    Status: In Progress

    Return JSON with fields: project_name, start_date, budget_usd, status
    """

    print("\n[...] Testing JSON extraction...")

    try:
        result = await client.extract_json(prompt)

        print("\n[SUCCESS] JSON Extraction successful!")
        print(f"\n[Extracted data]")
        for key, value in result.items():
            print(f"   {key}: {value}")

        return True

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}:")
        print(f"   {str(e)}")
        return False

    finally:
        await client.close()
        print("\n" + "=" * 60)


async def main():
    """Run all tests"""
    print("\n>> Starting Z.AI Integration Tests\n")

    # Test 1: Basic connection
    test1_passed = await test_zai_connection()

    if test1_passed:
        # Test 2: JSON extraction
        test2_passed = await test_json_extraction()

        if test1_passed and test2_passed:
            print("\n[SUCCESS] All tests passed! Z.AI integration is ready.")
            return 0

    print("\n[WARNING] Some tests failed. Please check the configuration.")
    return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
