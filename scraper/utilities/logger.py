from datetime import datetime
from typing import Any, Callable, Protocol
from dataclasses import dataclass

class Logger(Protocol):
    def success(self, format_str: str, *args: Any) -> None:
        ...

    def info(self, format_str: str, *args: Any) -> None:
        ...

    def error(self, format_str: str, *args: Any) -> None:
        ...

    def debug(self, format_str: str, *args: Any) -> None:
        ...

def get_time() -> str:
    """Returns the current time formatted as HH:MM:SS.mmm."""
    return datetime.now().strftime("%H:%M:%S.%f")[:-4]

COLORS = {
    "error": "\x1B[91m",
    "success": "\x1B[92m",
    "info": "\x1B[96m",
    "debug": "\x1B[95m",
    "reset": "\u001b[0m"
}

@dataclass
class LoggerCallback:
    level: str
    prefix: str
    message: str
    timestamp: str

class CallbackLogger:
    def __init__(self, prefix: str, is_debug: bool, callback: Callable[[LoggerCallback], None]) -> None:
        self.prefix = prefix
        self.is_debug = is_debug
        self.cb = callback

    def _log(self, level: str, format_str: str, *args: Any) -> None:
        message = format_str % args if args else format_str
        self.cb(LoggerCallback(
            prefix=self.prefix,
            level=level,
            message=message,
            timestamp=get_time()
        ))

    def debug(self, format_str: str, *args: Any) -> None:
        if self.is_debug:
            self._log("debug", format_str, *args)

    def error(self, format_str: str, *args: Any) -> None:
        self._log("error", format_str, *args)

    def info(self, format_str: str, *args: Any) -> None:
        self._log("info", format_str, *args)

    def success(self, format_str: str, *args: Any) -> None:
        self._log("success", format_str, *args)

class ConsoleLogger:
    def __init__(self, prefix: str, is_debug: bool) -> None:
        self.prefix = prefix
        self.is_debug = is_debug

    def _log(self, level: str, format_str: str, *args: Any) -> None:
        color = COLORS[level]
        message = format_str % args if args else format_str
        print(f"[{get_time()}] {color}[{self.prefix}]{COLORS['reset']} {message}")

    def debug(self, format_str: str, *args: Any) -> None:
        if self.is_debug:
            self._log("debug", format_str, *args)

    def error(self, format_str: str, *args: Any) -> None:
        self._log("error", format_str, *args)

    def info(self, format_str: str, *args: Any) -> None:
        self._log("info", format_str, *args)

    def success(self, format_str: str, *args: Any) -> None:
        self._log("success", format_str, *args)

def new_console_logger(prefix: str, debug: bool) -> Logger:
    """Creates a new ConsoleLogger instance."""
    return ConsoleLogger(prefix, debug)

def new_callback_logger(prefix: str, debug: bool, callback: Callable[[LoggerCallback], None]) -> Logger:
    """Creates a new CallbackLogger instance."""
    return CallbackLogger(prefix, debug, callback)

def new_callback_and_console_logger(prefix: str, debug: bool, callback: Callable[[LoggerCallback], None]) -> Logger:
    """Creates a logger that logs to both console and a callback."""
    console_logger = new_console_logger(prefix, debug)

    def combined_callback(log_callback: LoggerCallback) -> None:
        if log_callback.level == "debug":
            console_logger.debug(log_callback.message)
        elif log_callback.level == "info":
            console_logger.info(log_callback.message)
        elif log_callback.level == "error":
            console_logger.error(log_callback.message)
        elif log_callback.level == "success":
            console_logger.success(log_callback.message)

        callback(log_callback)

    return new_callback_logger(prefix, debug, combined_callback)
