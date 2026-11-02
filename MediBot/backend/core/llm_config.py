from litellm import completion
from backend.config.configs import SYNTHESIS_MODEL

def generate_completion(prompt: str, model: str = SYNTHESIS_MODEL, temperature: float = 0.2, response_format=None) -> str:
    """
    A unified LiteLLM wrapper for all text generation in the app.
    """
    try:
        kwargs = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }

        # Add JSON mode if requested (useful for the Intent Router)
        if response_format:
            kwargs["response_format"] = response_format

        response = completion(**kwargs)
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[ERROR] LiteLLM Generation failed on model {model}: {e}")
        return "I'm sorry, I am currently unable to generate a response."