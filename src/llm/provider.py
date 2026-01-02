
import os
import abc
import json
import httpx
from loguru import logger
from typing import Dict, Any, Optional

class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        pass

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_key:
             return "Error: No Gemini API Key provided."
             
        headers = {"Content-Type": "application/json"}
        
        # Construct payload
        # Gemini 1.5 structure
        contents = [{"parts": [{"text": prompt}]}]
        if system_instruction:
             # System instructions for Gemini often go nicely in the first user turn or specific field if beta supports it,
             # but standard generateContent is safest with just prompt. I will prepend sys instruction.
             contents[0]["parts"][0]["text"] = f"System Instruction: {system_instruction}\n\nUser Query: {prompt}"

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 800
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(self.url, json=payload, headers=headers, timeout=30.0)
                if resp.status_code != 200:
                    logger.error(f"Gemini API Error {resp.status_code}: {resp.text}")
                    return f"Error: Gemini API returned {resp.status_code}"
                
                data = resp.json()
                # Parse response
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                     logger.error(f"Gemini unexpected response format: {data}")
                     return "Error: Could not parse Gemini response."
                     
            except Exception as e:
                logger.error(f"Gemini Request Failed: {e}")
                return f"Error: {e}"

class HuggingFaceProvider(LLMProvider):
    def __init__(self, api_token: str, model_name: str = "meta-llama/Meta-Llama-3-8B-Instruct"):
        self.api_token = api_token
        self.model_name = model_name
        self.url = f"https://api-inference.huggingface.co/models/{model_name}"

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_token:
            return "Error: No HuggingFace Token provided."

        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        # Hugging Face Inference API format (standard text-generation)
        # For Llama 3/Instruct models, we should format the prompt with special tokens if possible, 
        # or just rely on the API to handle basic text.
        # Simple formatting:
        full_prompt = f"<|system|>\n{system_instruction}\n<|user|>\n{prompt}\n<|assistant|>\n"
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.7,
                "return_full_text": False
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(self.url, json=payload, headers=headers, timeout=30.0)
                
                if resp.status_code == 503:
                     # Model loading
                     return "Error: Model is loading, please try again in 30s."
                
                if resp.status_code != 200:
                    logger.error(f"HF API Error {resp.status_code}: {resp.text}")
                    return f"Error: HF API returned {resp.status_code}"

                data = resp.json()
                # HF returns list of dicts: [{'generated_text': '...'}]
                if isinstance(data, list) and len(data) > 0:
                    return data[0].get("generated_text", "").strip()
                elif isinstance(data, dict) and "error" in data:
                    return f"Error: {data['error']}"
                else:
                    return str(data)
                    
            except Exception as e:
                logger.error(f"HF Request Failed: {e}")
                return f"Error: {e}"

class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = "moonshotai/kimi-k2-instruct-0905"):
        self.api_key = api_key
        self.model_name = model_name
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_key:
            return "Error: No Groq API Key provided."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(self.url, json=payload, headers=headers, timeout=30.0)
                
                if resp.status_code != 200:
                    logger.error(f"Groq API Error {resp.status_code}: {resp.text}")
                    return f"Error: Groq API returned {resp.status_code} - {resp.text}"

                data = resp.json()
                return data["choices"][0]["message"]["content"]
                    
            except Exception as e:
                logger.error(f"Groq Request Failed: {e}")
                return f"Error: {e}"

class GitHubModelProvider(LLMProvider):
    def __init__(self, api_token: str, model_name: str = "gpt-4o"):
        self.api_token = api_token
        self.model_name = model_name
        self.url = "https://models.inference.ai.azure.com/chat/completions"

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_token:
            return "Error: No GitHub Token provided."

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(self.url, json=payload, headers=headers, timeout=30.0)
                
                if resp.status_code != 200:
                    logger.error(f"GitHub API Error {resp.status_code}: {resp.text}")
                    return f"Error: GitHub API returned {resp.status_code} - {resp.text}"

                data = resp.json()
                return data["choices"][0]["message"]["content"]
                    
            except Exception as e:
                logger.error(f"GitHub Request Failed: {e}")
                return f"Error: {e}"
