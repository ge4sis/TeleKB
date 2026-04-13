import os
from google import genai
from .config import Config

class Translator:
    def __init__(self):
        if Config.GEMINI_API_KEY:
            self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
            # Priority list of models to try. Fall back to older/other versions if quota exceeded.
            self.model_list = ["models/gemini-3.1-flash-lite-preview", "models/gemini-2.5-flash-lite", "models/gemma-4-31b-it"]
        else:
            self.client = None

    def translate_to_korean(self, text: str) -> str:
        if not text or not self.client:
            return ""
        
        import time
        max_retries_per_model = 2
        
        for model_name in self.model_list:
            for attempt in range(max_retries_per_model + 1):
                try:
                    prompt = f"Translate the following text to Korean. Output ONLY the translation without any explanation or quotes:\n\n{text}"
                    
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    
                    if response.text:
                        return response.text.strip()
                    return ""

                except Exception as e:
                    err_str = str(e).upper()
                    # Check for retriable errors: 429 (Quota), 503 (Service Unavailable), RESOURCE_EXHAUSTED
                    is_retriable = any(code in err_str for code in ["429", "503", "RESOURCE_EXHAUSTED", "SERVICE_UNAVAILABLE"])
                    
                    if is_retriable:
                        if attempt < max_retries_per_model:
                            sleep_time = 2 * (attempt + 1)
                            print(f"[{model_name}] Service issue ({'429' if '429' in err_str else '503'}). Retrying in {sleep_time}s...")
                            time.sleep(sleep_time)
                            continue
                        else:
                            print(f"[{model_name}] Limit/Error reached. Falling back to next model...")
                            break # Move to the next model in model_list
                    
                    print(f"Translation error with {model_name}: {e}")
                    # For other errors, we also try the next model just in case it's model-specific
                    break 
        
        return ""
