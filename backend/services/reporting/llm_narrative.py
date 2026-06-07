import os
import json
import logging
from openai import AsyncOpenAI
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Configure OpenRouter using the OpenAI SDK
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if OPENROUTER_API_KEY:
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
else:
    client = None
    logger.warning("OPENROUTER_API_KEY not found. AI Reports will use mock generation.")

async def generate_case_narrative(case_data: Dict[str, Any]) -> str:
    """
    Takes structured graph/case data (patterns, shared entities, total risk)
    and uses an LLM via OpenRouter to generate a professional cybercrime dossier.
    """
    if not client:
        return _mock_narrative(case_data)
        
    system_prompt = """
    You are an expert Cybercrime Intelligence Analyst working for the Pune Police Cybercrime Cell.
    Your job is to take raw transaction data, identified structural patterns (like smurfing, OTP fraud), and shared entity overlaps (like reused phone numbers across cases), and synthesize them into a highly professional, cohesive Case Dossier.
    
    Structure the report with:
    1. Executive Summary
    2. Modus Operandi (MO) Analysis
    3. Key Indicators & Shared Entities
    4. Recommended Action Plan
    
    Use a formal, objective, investigative tone. Do not use markdown styling like asterisks since this text will be injected into a formatted PDF/HTML template. Use clear paragraphs and simple bullet points (using hyphens).
    """
    
    user_prompt = f"Generate a cybercrime case dossier based on the following intelligence data:\n\n{json.dumps(case_data, indent=2)}"
    
    try:
        # Using a solid open-weight model or auto-router if preferred.
        # We'll default to a generic model identifier or anthropic/claude-3-haiku for speed
        # If openrouter auto is preferred: "openrouter/auto"
        response = await client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct:free", # Free tier model for dev
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            extra_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "FraudLens by Pune Police Cybercrime Cell",
            }
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM Generation failed: {e}")
        return _mock_narrative(case_data)

async def stream_case_narrative(case_data: Dict[str, Any]):
    """
    Yields chunks of the generated case dossier directly from the LLM stream.
    """
    if not client:
        # Yield mock text chunks to simulate streaming
        mock_text = _mock_narrative(case_data)
        for chunk in mock_text.split(' '):
            import asyncio
            await asyncio.sleep(0.05)
            yield chunk + ' '
        return

    system_prompt = """
    You are an expert Cybercrime Intelligence Analyst working for the Pune Police Cybercrime Cell.
    Your job is to take raw transaction data, identified structural patterns (like smurfing, OTP fraud), and shared entity overlaps (like reused phone numbers across cases), and synthesize them into a highly professional, cohesive Case Dossier.
    
    Structure the report with:
    1. Executive Summary
    2. Modus Operandi (MO) Analysis
    3. Key Indicators & Shared Entities
    4. Recommended Action Plan
    
    Use a formal, objective, investigative tone. Do not use markdown styling like asterisks since this text will be injected into a formatted PDF/HTML template. Use clear paragraphs and simple bullet points (using hyphens).
    """
    
    user_prompt = f"Generate a cybercrime case dossier based on the following intelligence data:\n\n{json.dumps(case_data, indent=2)}"
    
    try:
        stream = await client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            extra_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "FraudLens by Pune Police Cybercrime Cell",
            },
            stream=True
        )
        
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    except Exception as e:
        logger.error(f"LLM Streaming failed: {e}")
        yield f"Error generating narrative stream: {str(e)}"

def _mock_narrative(case_data: dict) -> str:
    return """Executive Summary
The analyzed transaction cluster exhibits strong indicators of a coordinated cyber fraud operation, specifically mirroring a classic Investment Scam playbook. Over 15 unique victim accounts were drained within a tight 48-hour window.

Modus Operandi (MO) Analysis
The perpetrators utilized a "Round Robin" routing technique, rapidly shifting small-value transfers (averaging ₹45,000 to evade immediate ₹50,000 threshold alerts) across a secondary mule network before consolidating the funds into two primary beneficiary accounts linked to cryptocurrency exchanges. 

Key Indicators & Shared Entities
- Reused UPI VPA: The VPA 'returns.invest@ybl' appeared in 12 distinct fraudulent transfers.
- Shared IP Subnets: 4 of the mule accounts were accessed from the identical proxy server block.

Recommended Action Plan
1. Freeze the two terminal beneficiary accounts immediately.
2. Submit Section 91 CrPC notices to the involved payment gateways for KYC logs tied to the reused UPI VPA.
3. Escalate the linked phone numbers to the Telecom Nodal Officer for immediate suspension."""
