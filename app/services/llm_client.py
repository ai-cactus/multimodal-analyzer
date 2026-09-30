"""
Vertex AI Model Garden Client for Compliant Models
Supports Claude via AnthropicVertex and Llama via OpenAI-compatible endpoints
"""
import warnings
# Suppress Vertex AI SDK deprecation warnings
warnings.filterwarnings("ignore", category=UserWarning, module="vertexai")

from typing import List, Dict, Any, Optional
from anthropic import AnthropicVertex
from openai import OpenAI
import requests
try:
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
except ImportError:
    from langchain.schema import HumanMessage, SystemMessage, AIMessage
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
import subprocess
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from app.config import get_settings
from app.utils.logger import get_logger
from app.services.cost_tracker import CostTracker
import json

settings = get_settings()
logger = get_logger(__name__)


class ModelGardenClient:
    """
    Client for compliant enterprise models via Vertex AI Model Garden
    Supports Claude (via Anthropic SDK) and Llama (via OpenAI-compatible API)
    """
    
    MODEL_CONFIGS = {
        # Primary model - Llama Scout (WORKING)
        "llama-scout": {
            "provider": "llama",
            "model_name": "meta/llama-4-scout-17b-16e-instruct-maas",
            "temperature": 0.1,
            "max_output_tokens": 8192,
        },
        # Secondary model - Gemini 2.0 Flash (Latest RAG-optimized)
        "gemini-flash": {
            "provider": "gemini",  
            "model_name": "gemini-2.0-flash-001",  # Latest Gemini 2.0 Flash
            "temperature": 0.1,
            "max_output_tokens": 8192,
        },
        # Fallback option - GPT OSS
        "gpt-oss": {
            "provider": "llama",  # Uses same OpenAI-compatible endpoint
            "model_name": "openai/gpt-oss-120b-maas",
            "region": "global",  # GPT-OSS uses global endpoint, not regional
            "temperature": 0.1,
            "max_output_tokens": 8192,
        },
        # Claude Opus - DISABLED (quota exhausted)
        # "claude-opus": {
        #     "provider": "anthropic",
        #     "model_name": "claude-opus-4-5@20251101",
        #     "temperature": 0.1,
        #     "max_output_tokens": 8192,
        # },
    }
    
    def __init__(self):
        vertexai.init(project=settings.gcp_project_id, location=settings.gemini_region)
        self.clients = {}
        self._verified = False
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Model Garden clients"""
        for model_key, config in self.MODEL_CONFIGS.items():
            try:
                if config["provider"] == "gemini":
                    # Gemini via direct Vertex AI REST API
                    self.clients[model_key] = {
                        "client": None,  # Uses direct HTTP requests
                        "provider": "gemini",
                        "config": config
                    }
                elif config["provider"] == "anthropic":
                    # Claude via AnthropicVertex SDK
                    client = AnthropicVertex(
                        region=settings.claude_region,
                        project_id=settings.gcp_project_id
                    )
                    self.clients[model_key] = {
                        "client": client,
                        "provider": "anthropic",
                        "config": config
                    }
                elif config["provider"] == "llama":
                    # Llama via OpenAI-compatible endpoint
                    # Use model-specific region if specified, otherwise default to llama_region
                    region = config.get("region", settings.llama_region)
                    
                    # Handle global region (uses different endpoint format)
                    if region == "global":
                        endpoint = "https://aiplatform.googleapis.com"
                    else:
                        endpoint = f"https://{region}-aiplatform.googleapis.com"
                    
                    base_url = f"{endpoint}/v1/projects/{settings.gcp_project_id}/locations/{region}/endpoints/openapi"
                    
                    client = OpenAI(
                        base_url=base_url,
                        api_key=self._get_gcloud_token(),
                        timeout=60.0  # Set default timeout
                    )
                    self.clients[model_key] = {
                        "client": client,
                        "provider": "llama",
                        "config": config
                    }
                
                logger.info(f"Registered {model_key} ({config['provider']})")
            except Exception as e:
                logger.warning(f"Could not register {model_key}: {e}")
    
    def _get_gcloud_token(self) -> str:
        """Get GCP access token for authentication using SDK credentials"""
        import google.auth
        import google.auth.transport.requests
        
        try:
            # This follows GOOGLE_APPLICATION_CREDENTIALS if set
            credentials, project = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            auth_request = google.auth.transport.requests.Request()
            credentials.refresh(auth_request)
            return credentials.token
        except Exception as e:
            logger.error(f"Failed to get GCP token via google-auth: {e}")
            # Fallback to subprocess for dev environments without google-auth configured
            try:
                import subprocess
                result = subprocess.run(
                    ["gcloud", "auth", "print-access-token"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            except:
                return ""
            return ""
    
    async def verify_models(self) -> List[str]:
        """
        Actively verify which models are responding.
        Returns list of verified model keys.
        """
        logger.info("Starting pre-flight model verification...")
        verified = []
        tasks = []
        keys = list(self.clients.keys())
        
        for key in keys:
            tasks.append(self._probe_model(key))
            
        results = await asyncio.gather(*tasks)
        
        for key, success in zip(keys, results):
            if success:
                logger.info(f"Model {key} verified successfully.")
                verified.append(key)
            else:
                logger.warning(f"Model {key} failed verification, removing from active set.")
                if key in self.clients:
                    del self.clients[key]
        
        self._verified = True
        return verified

    async def _probe_model(self, model_key: str) -> bool:
        """Attempt a minimal call to verify model availability"""
        try:
            client_info = self.clients[model_key]
            provider = client_info["provider"]
            
            if provider == "gemini":
                # Test Gemini
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self._call_gemini_sync(
                        client_info["config"]["model_name"],
                        "You are helpful.",
                        "Say hi",
                        10
                    )
                )
            elif provider == "anthropic":
                # Test Claude
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: client_info["client"].messages.create(
                        max_tokens=10,
                        messages=[{"role": "user", "content": "hi"}],
                        model=client_info["config"]["model_name"]
                    )
                )
            elif provider == "llama":
                # Test Llama
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: client_info["client"].chat.completions.create(
                        model=client_info["config"]["model_name"],
                        messages=[{"role": "user", "content": "hi"}],
                        max_tokens=10
                    )
                )
            
            return True
        except Exception as e:
            logger.debug(f"Probe failed for {model_key}: {e}")
            return False
    
    def _call_gemini_sync(self, model_name: str, system_prompt: str, user_prompt: str, max_tokens: int) -> tuple:
        """Synchronous Gemini API call via Vertex AI SDK
        
        Returns:
            tuple: (response_text, usage_dict) where usage_dict contains
                   prompt_token_count and candidates_token_count
        """
        try:
            model = GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt
            )
            
            response = model.generate_content(
                user_prompt,
                generation_config=GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.1
                )
            )
            
            # Extract token usage from response metadata
            usage = {"prompt_token_count": 0, "candidates_token_count": 0}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage["prompt_token_count"] = getattr(
                    response.usage_metadata, "prompt_token_count", 0
                ) or 0
                usage["candidates_token_count"] = getattr(
                    response.usage_metadata, "candidates_token_count", 0
                ) or 0
            
            return response.text, usage
        except Exception as e:
            logger.error(f"Error in Gemini Vertex SDK call: {e}")
            return "", {"prompt_token_count": 0, "candidates_token_count": 0}
    
    def _repair_json(self, json_str: str) -> str:
        """
        Attempt to repair common JSON syntax errors
        
        Handles issues like:
        - Missing commas between properties
        - Unquoted property names
        - Trailing commas
        - Single quotes instead of double quotes
        - Comments
        """
        import re
        
        # Remove comments
        json_str = re.sub(r'//.*?\n', '\n', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # Replace single quotes with double quotes (cautiously)
        # Only replace if they look like property delimiters
        json_str = re.sub(r"'([^']*)'(\s*:)", r'"\1"\2', json_str)
        json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)
        
        # Fix unquoted property names (common in llama-scout responses)
        # Match:word: (not already quoted)
        json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3', json_str)
        
        # Fix missing commas between adjacent string values and property names
        # Pattern: "value" "property":
        json_str = re.sub(r'"\s+("[\w_]+"\s*:)', r'", \1', json_str)
        
        # Fix missing commas when property is on next line after a value
        # Pattern: "value"\nword: or "value"\n"word":
        json_str = re.sub(r'"(\s*\n\s*)([a-zA-Z_"]+[\w_"]*\s*:)', r'",\1\2', json_str)
        
        # Fix missing commas after boolean/number values before next property
        # Pattern: true "property": or false "property": or 123 "property":
        json_str = re.sub(r'(true|false|null|\d+\.?\d*)\s+("[\w_]+"\s*:)', r'\1, \2', json_str)
        
        # Fix missing commas after closing braces/brackets before next property
        # Pattern: } "property": or ] "property":
        json_str = re.sub(r'([}\]])\s+("[\w_]+"\s*:)', r'\1, \2', json_str)
        
        # Remove trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Try to add missing commas between properties (multi-line)
        # Look for patterns like: }\n\s*" or }\n\s*{
        json_str = re.sub(r'([}\]"\d])\s*\n\s*(["{[])', r'\1,\2', json_str)
        
        # Fix missing commas after closing braces/brackets (with newline)
        json_str = re.sub(r'([}\]])\s*\n\s*"', r'\1,\n"', json_str)
        
        return json_str.strip()
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60)
    )
    async def call_llm(
        self,
        model_key: str,
        system_prompt: str,
        user_prompt: str,
        response_format: str = "json",
        cost_tracker: Optional[CostTracker] = None,
        phase: str = "analysis",
    ) -> Dict[str, Any]:
        """
        Call a specific LLM with retry logic and optional cost tracking.

        Args:
            model_key: Model identifier
            system_prompt: System prompt text
            user_prompt: User prompt text
            response_format: Expected format ("json" or "text")
            cost_tracker: Optional CostTracker to record token usage
            phase: Analysis phase for cost categorization
        """
        if model_key not in self.clients:
            raise ValueError(f"Model {model_key} not available")
        
        client_info = self.clients[model_key]
        provider = client_info["provider"]
        config = client_info["config"]
        
        input_tokens = 0
        output_tokens = 0
        
        try:
            loop = asyncio.get_event_loop()
            
            if provider == "gemini":
                # Gemini via Vertex AI SDK — returns (text, usage_dict)
                content, usage = await loop.run_in_executor(
                    None,
                    lambda: self._call_gemini_sync(
                        config["model_name"],
                        system_prompt,
                        user_prompt,
                        config["max_output_tokens"]
                    )
                )
                input_tokens = usage.get("prompt_token_count", 0)
                output_tokens = usage.get("candidates_token_count", 0)
                
            elif provider == "anthropic":
                # Claude API
                response = await loop.run_in_executor(
                    None,
                    lambda: client_info["client"].messages.create(
                        max_tokens=config["max_output_tokens"],
                        temperature=config["temperature"],
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_prompt}],
                        model=config["model_name"]
                    )
                )
                content = response.content[0].text
                # Anthropic SDK provides usage on the response object
                if hasattr(response, "usage") and response.usage:
                    input_tokens = getattr(response.usage, "input_tokens", 0) or 0
                    output_tokens = getattr(response.usage, "output_tokens", 0) or 0
                
            elif provider == "llama":
                # Llama via OpenAI-compatible API
                # Refresh token for each call
                client_info["client"].api_key = self._get_gcloud_token()
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                
                response = await loop.run_in_executor(
                    None,
                    lambda: client_info["client"].chat.completions.create(
                        model=config["model_name"],
                        messages=messages,
                        temperature=config["temperature"],
                        max_tokens=config["max_output_tokens"]
                    )
                )
                content = response.choices[0].message.content
                # OpenAI-compatible SDK provides usage on the response object
                if hasattr(response, "usage") and response.usage:
                    input_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
                    output_tokens = getattr(response.usage, "completion_tokens", 0) or 0
            
            # Record cost if tracker provided
            if cost_tracker and (input_tokens > 0 or output_tokens > 0):
                cost_tracker.record_llm_call(
                    model_key=model_key,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    phase=phase,
                )
            
            # Parse JSON if expected
            if response_format == "json":
                # Log raw response for debugging
                logger.debug(f"Raw response from {model_key}: {content[:300]}")
                
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.debug(f"Initial JSON parse failed: {e}")
                    # Try to extract JSON from markdown code blocks
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        json_str = content.split("```")[1].split("```")[0].strip()
                    else:
                        json_str = content
                    
                    # Try to repair malformed JSON
                    try:
                        repaired = self._repair_json(json_str)
                        logger.debug(f"Repaired JSON: {repaired[:300]}")
                        return json.loads(repaired)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Could not parse JSON from {model_key}: {str(e)}")
                        logger.warning(f"Original content: {content[:500]}")
                        logger.warning(f"After repair: {repaired[:500] if 'repaired' in locals() else 'N/A'}")
                        return {"raw_response": content}
            else:
                return {"response": content}
                
        except Exception as e:
            logger.error(f"Error calling {model_key}: {e}")
            raise
    
    async def call_multi_llm(
        self,
        models: List[str],
        system_prompt: str,
        user_prompt: str,
        response_format: str = "json",
        cost_tracker: Optional[CostTracker] = None,
        phase: str = "analysis",
    ) -> Dict[str, Dict[str, Any]]:
        """
        Call multiple LLMs in parallel with optional cost tracking.
        """
        # Ensure models are verified before parallel call
        if not self._verified:
            await self.verify_models()
            
        # Filter requested models by those currently active
        active_models = [m for m in models if m in self.clients]
        
        if not active_models:
            logger.error("No active models available for parallel call.")
            return {"error": "No verified models available"}

        tasks = {
            asyncio.create_task(
                self.call_llm(
                    model, system_prompt, user_prompt, response_format,
                    cost_tracker=cost_tracker, phase=phase,
                )
            ): model
            for model in active_models
        }
        
        # Execute parallel calls with an overall timeout
        done, pending = await asyncio.wait(
            tasks.keys(),
            timeout=120.0
        )
        
        if not done:
            logger.error("Parallel LLM execution timed out after 120 seconds with 0 results.")
            return {"error": "Multi-LLM execution timed out"}
            
        if pending:
            logger.warning(f"Parallel LLM execution partially timed out. {len(pending)} tasks remaining.")
            for task in pending:
                task.cancel()
        
        output = {}
        # Map finished tasks back to their models
        for task in done:
            model = tasks[task]
            try:
                result = task.result()
                output[model] = result
            except Exception as e:
                logger.error(f"Error from {model}: {e}")
                output[model] = {"error": str(e)}
        
        # Add error entries for timed-out models
        for task in pending:
            model = tasks[task]
            output[model] = {"error": "Request timed out"}
            
        return output
    
    def get_available_models(self) -> List[str]:
        """Return list of successfully verified models"""
        return list(self.clients.keys())
    
    def get_active_models(self) -> List[str]:
        """
        Return list of models to use based on configuration
        
        If USE_MULTI_MODEL=true: returns all available models
        If USE_MULTI_MODEL=false: returns only PRIMARY_MODEL if available
        """
        available = self.get_available_models()
        
        if settings.use_multi_model:
            # Use all available models
            return available
        else:
            # Use only primary model if available
            if settings.primary_model in available:
                return [settings.primary_model]
            elif available:
                # Fallback to first available if primary not found
                logger.warning(
                    f"Primary model '{settings.primary_model}' not available. "
                    f"Using {available[0]} instead."
                )
                return [available[0]]
            else:
                return []


# Singleton instance
_client_instance = None

def get_llm_client() -> ModelGardenClient:
    """Get singleton LLM client instance"""
    global _client_instance
    if _client_instance is None:
        _client_instance = ModelGardenClient()
    return _client_instance
