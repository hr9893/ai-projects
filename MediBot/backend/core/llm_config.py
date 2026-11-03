from litellm import completion
from backend.config.configs import SYNTHESIS_MODEL
from backend.utils.logger import ExtensionLoggerFactory

LOGGER = ExtensionLoggerFactory.getLogger("llm_config")

def generate_completion(prompt: str, model: str = SYNTHESIS_MODEL, temperature: float = 0.2, response_format=None) -> str:
    """
    A unified LiteLLM wrapper for all text generation in the app.
    """
    function_name = "generate_completion"
    LOGGER.extMethodExit(function_name, lambda: "Entry")
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
        LOGGER.extDebugAsJson(function_name, lambda: "Final LLM Response ->", response.choices[0].message.content.strip())
        LOGGER.extMethodExit(function_name, lambda: "Exit")

        return response.choices[0].message.content.strip()

    except Exception as e:
        LOGGER.extError(function_name, lambda: f"LiteLLM Generation failed on model {model}: {e}")
        return "I'm sorry, I am currently unable to generate a response."