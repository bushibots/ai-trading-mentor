import json
import google.generativeai as genai
from typing import Dict, Any
from app.ai.provider_base import AIProviderBase
from app.core.config import get_gemini_keys
from google.api_core import exceptions

class GeminiProvider(AIProviderBase):
    def __init__(self):
        self.keys = get_gemini_keys()
        self.current_key_idx = 0
        if not self.keys:
            print("WARNING: GEMINI_API_KEYS is not set.")
        else:
            genai.configure(api_key=self.keys[self.current_key_idx])
            
        # Using gemini-2.5-flash-lite as requested
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
    def _rotate_key(self):
        """Rotates to the next available API key."""
        if not self.keys:
            return False
        self.current_key_idx = (self.current_key_idx + 1) % len(self.keys)
        genai.configure(api_key=self.keys[self.current_key_idx])
        # Safely re-initialize the model to ensure it picks up the new global API key
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        print(f"Rotated to API Key {self.current_key_idx + 1}/{len(self.keys)}")
        return True
        
    def _execute_prompt(self, prompt_parts: list) -> str:
        attempts = 0
        max_attempts = len(self.keys)
        
        while attempts < max_attempts:
            try:
                response = self.model.generate_content(prompt_parts)
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:].strip()
                    if text.endswith("```"):
                        text = text[:-3].strip()
                elif text.startswith("```"):
                    text = text[3:].strip()
                    if text.endswith("```"):
                        text = text[:-3].strip()
                
                # Further safety: find first { and last }
                start_idx = text.find('{')
                end_idx = text.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    text = text[start_idx:end_idx+1]
                    
                return text
            except exceptions.GoogleAPIError as e:
                print(f"Gemini API Error with key {self.current_key_idx + 1}: {e}")
                self._rotate_key()
                attempts += 1
            except Exception as e:
                raise ValueError(f"Unexpected error during AI generation: {str(e)}")
                
        raise ValueError("All configured Gemini API keys failed. Rate limits or invalid keys.")

    async def analyze_chart(self, image_path: str, timeframe: str, indicators: Dict[str, Any], previous_context: str = None, user_notes: str = None) -> str:
        """
        Orchestrates the Multi-Agent Pipeline: Extractor -> Analyst -> Judge
        """
        if not self.keys:
            raise ValueError("GEMINI_API_KEYS is not configured.")
            
        import PIL.Image
        try:
            img = PIL.Image.open(image_path)
        except Exception as e:
            raise ValueError(f"Failed to load image: {str(e)}")

        # 1. Extractor Agent (Vision)
        print("Running Agent 1: Extractor...")
        extractor_prompt = f"""
        You are the Extractor Agent. Your job is purely to read the chart screenshot and extract technical data.
        Timeframe: {timeframe}
        Output ONLY a JSON matching this schema:
        {{
            "support_levels": [<float>],
            "resistance_levels": [<float>],
            "trend_direction": "UP" | "DOWN" | "SIDEWAYS",
            "observed_patterns": ["<pattern>"],
            "volume_anomalies": "<string or null>",
            "key_observations": ["<string>"]
        }}
        """
        extracted_data_str = self._execute_prompt([extractor_prompt, img])

        # 2. Analyst Agent (Logic)
        print("Running Agent 2: Analyst...")
        context_prompt = ""
        if previous_context:
            context_prompt += f"HISTORY: You analyzed this previously. Previous Analysis: {previous_context}\nIf you still decide to WAIT, you MUST output a precise wait duration in 'wait_duration_recommendation'.\n"
        if user_notes:
            context_prompt += f"USER NOTES / CONTEXT: {user_notes}\nIMPORTANT: Incorporate this context from the user into your analysis!\n"
            
        analyst_prompt = f"""
        You are the Analyst Agent. Your job is to calculate a logical trading recommendation based on extracted data.
        Extracted Data: {extracted_data_str}
        Local Indicators: {json.dumps(indicators)}
        {context_prompt}
        
        Output ONLY a JSON matching this schema:
        {{
            "signal": "BUY" | "SELL" | "HOLD" | "WAIT" | "CONFLICT",
            "confidence": <float 0-100>,
            "stop_loss": <float or null>,
            "target": <float or null>,
            "time_horizon": "<string or null>",
            "wait_duration_recommendation": "<string or null>",
            "bull_factors": ["<string>"],
            "bear_factors": ["<string>"],
            "invalidation_conditions": ["<string>"],
            "logic_reasoning": ["<string>"]
        }}
        CRITICAL: If the signal is BUY or SELL, you MUST calculate and include a concrete numerical 'stop_loss' and 'target' (Take Profit) as floats based on the support/resistance levels. They MUST NOT be null.
        """
        analyst_recommendation_str = self._execute_prompt([analyst_prompt])

        # 3. Judge/Mentor Agent (Education)
        print("Running Agent 3: Judge/Mentor...")
        judge_prompt = f"""
        You are the Judge/Mentor Agent. You evaluate the Analyst's recommendation against the raw data, finalize the decision, and teach the user.
        Extracted Data: {extracted_data_str}
        Analyst Recommendation: {analyst_recommendation_str}
        User Notes / Context: {user_notes or 'None'}
        
        You have the final say. If the Analyst's logic is flawed or risk/reward is poor, override the signal to WAIT or CONFLICT.
        Your primary goal is to educate the user on WHY this decision was made and what concepts apply.
        
        Output ONLY a JSON matching this schema:
        {{
            "signal": "BUY" | "SELL" | "HOLD" | "WAIT" | "CONFLICT",
            "confidence": <float 0-100>,
            "reasons": ["<reason 1>"],
            "bull_factors": ["<factor>"],
            "bear_factors": ["<factor>"],
            "pattern_names": ["<pattern>"],
            "concept_names": ["<concept>"],
            "educational_explanations": [], 
            "wait_duration_recommendation": "<string or null>",
            "stop_loss": <float or null>,
            "target": <float or null>,
            "time_horizon": "<string or null>",
            "expiration_time": "<string or null>",
            "invalidation_conditions": ["<condition>"],
            "additional_comments": "<string or null>"
        }}
        CRITICAL: If the signal is BUY or SELL, you MUST ensure that 'stop_loss' and 'target' (Take Profit) are provided as concrete numerical float values. If the Analyst provided them, verify they are correct and pass them along. If they are missing or null, you must calculate and supply them. They must NOT be null for BUY or SELL signals.
        """
        final_response_str = self._execute_prompt([judge_prompt])
        
        return final_response_str
