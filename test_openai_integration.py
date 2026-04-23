import asyncio
from backend.core.glm_client import GLMClient
from backend.agents.agent_a.prompts import build_extraction_prompt

async def test_openai_extraction():
    print("Initializing GLMClient (which is now configured for OpenAI via .env)...")
    client = GLMClient()
    
    print(f"API URL: {client.api_url}")
    print(f"Model: {client.model}")
    
    sample_text = """
    PROJECT AGREEMENT
    Project Name: Building A Construction
    Contractor: ABC Construction Ltd
    Budget: RM 1,500,000
    Start Date: 15 January 2024
    End Date: 31 December 2024
    """

    print("\nSending extraction prompt...")
    try:
        prompt = build_extraction_prompt(sample_text)
        result = await client.extract_json(prompt)
        
        print("\n=== Extracted Fields ===")
        import json
        print(json.dumps(result, indent=2))
        print("\n✓ OpenAI API key works correctly with the GLMClient structure!")
        
    except Exception as e:
        print(f"\n[Error] during API call: {str(e)}")
        import traceback
        traceback.print_exc()
        
if __name__ == "__main__":
    asyncio.run(test_openai_extraction())
