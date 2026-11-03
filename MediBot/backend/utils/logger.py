# backend/utils/logger.py
import logging
import json
import os
from pathlib import Path
from typing import Any, Callable, Union

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

noisy_loggers = [
    "LiteLLM",
    "litellm",
    "qdrant_client",
    "httpx",
    "httpcore",
    "langchain",
    "urllib3",
    "fastapi",
    "uvicorn",
    "uvicorn.access",
    "typesafe_sdk",
    "httpcore2.connection",
    "httpcore2.http11",
]

for logger_name in noisy_loggers:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

class ExtensionLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _eval_msg(self, msg: Union[str, Callable[[], str]]) -> str:
        if callable(msg):
            return msg()
        return msg

    # Matches Java: extMethodEntry(methodName, params, msgSupplier)
    def extMethodEntry(self, method_name: str, params: Any = None, msg: Union[str, Callable[[], str]] = "Entry"):
        self.logger.info(f"[{method_name}] >>> {self._eval_msg(msg)}")

    # Matches Java: extMethodExit(methodName, retVal, msgSupplier)
    def extMethodExit(self, method_name: str, ret_val: Any = None, msg: Union[str, Callable[[], str]] = "Exit"):
        self.logger.info(f"[{method_name}] <<< {self._eval_msg(msg)}")

    # Matches Java: extDebugAsJson(methodName, msgSupplier, payload)
    # Made payload optional (=None) to prevent crashes if you forget to pass it
    def extDebugAsJson(self, method_name: str, msg: Union[str, Callable[[], str]], payload: Any = None):
        try:
            payload_dict = payload
            if hasattr(payload, "model_dump"):
                payload_dict = payload.model_dump()
            elif hasattr(payload, "body"):
                # Use global json, removed the local import that caused the crash!
                payload_dict = json.loads(payload.body.decode('utf-8'))

            json_str = json.dumps(payload_dict, default=str, indent=2)
            self.logger.debug(f"[{method_name}] {self._eval_msg(msg)} \n{json_str}")
        except Exception as e:
            self.logger.debug(f"[{method_name}] {self._eval_msg(msg)} \n{payload} (JSON serialization failed: {e})")

    # Matches Java: extError(methodName, msgSupplier, throwable, errorMsg)
    def extError(self, method_name: str, msg: Union[str, Callable[[], str]], exception: Exception, error_msg: str = ""):
        self.logger.error(f"[{method_name}] {self._eval_msg(msg)} | Error: {error_msg}", exc_info=exception)

    def extDebugTextBlock(self, method_name: str, msg: Union[str, Callable[[], str]], text_block: str):
        """Bypasses JSON serialization to print a raw, multi-line string beautifully."""
        self.logger.debug(f"[{method_name}] {self._eval_msg(msg)} \n{text_block}")

class ExtensionLoggerFactory:
    @staticmethod
    def getLogger(name: str) -> 'ExtensionLogger':
        return ExtensionLogger(name)