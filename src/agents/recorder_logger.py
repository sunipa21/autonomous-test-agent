"""
Logging configuration for the Recorder Agent
Provides structured logging with session tracking for debugging
"""
import logging
import sys
from datetime import datetime
from typing import Optional

# Create a dedicated logger for the recorder
recorder_logger = logging.getLogger("recorder_agent")
recorder_logger.setLevel(logging.DEBUG)

# Create console handler with detailed format
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

# Create formatter with timestamp, level, and message
formatter = logging.Formatter(
    '%(asctime)s - [RECORDER] - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)

# Add handler to logger
if not recorder_logger.handlers:
    recorder_logger.addHandler(console_handler)


class RecorderLogger:
    """
    Structured logger for recorder operations
    """
    
    @staticmethod
    def log_session_start(session_id: str, config: dict):
        """Log the start of a recording session"""
        recorder_logger.info("=" * 80)
        recorder_logger.info(f"🎬 RECORDING SESSION START: {session_id}")
        recorder_logger.info(f"   Suite: {config.get('suite_name', 'N/A')}")
        recorder_logger.info(f"   Test: {config.get('test_title', 'N/A')}")
        recorder_logger.info(f"   URL: {config.get('url', 'N/A')}")
        recorder_logger.info(f"   Headless: {config.get('headless', False)}")
        recorder_logger.info("=" * 80)
    
    @staticmethod
    def log_session_stop(session_id: str, code_length: int, steps_count: int):
        """Log the stop of a recording session"""
        recorder_logger.info("=" * 80)
        recorder_logger.info(f"🛑 RECORDING SESSION STOP: {session_id}")
        recorder_logger.info(f"   Code Length: {code_length} bytes")
        recorder_logger.info(f"   Steps Generated: {steps_count}")
        recorder_logger.info("=" * 80)
    
    @staticmethod
    def log_command(cmd: list):
        """Log the Playwright command being executed"""
        recorder_logger.debug(f"📝 Playwright Command: {' '.join(cmd)}")
    
    @staticmethod
    def log_process_info(pid: int, status: str):
        """Log process information"""
        recorder_logger.debug(f"⚙️  Process PID: {pid}, Status: {status}")
    
    @staticmethod
    def log_file_operation(operation: str, filepath: str, success: bool = True):
        """Log file operations"""
        status = "✅" if success else "❌"
        recorder_logger.debug(f"{status} {operation}: {filepath}")
    
    @staticmethod
    def log_llm_conversion(code_length: int, steps_generated: int):
        """Log LLM conversion results"""
        recorder_logger.info(f"🤖 LLM Conversion: {code_length} bytes → {steps_generated} steps")
    
    @staticmethod
    def log_error(context: str, error: Exception):
        """Log errors with context"""
        recorder_logger.error(f"❌ ERROR in {context}: {type(error).__name__}: {str(error)}")
    
    @staticmethod
    def log_warning(message: str):
        """Log warnings"""
        recorder_logger.warning(f"⚠️  {message}")
    
    @staticmethod
    def log_test_save(suite_name: str, test_id: str, test_title: str):
        """Log test case save operation"""
        recorder_logger.info(f"💾 Saving Test Case:")
        recorder_logger.info(f"   Suite: {suite_name}")
        recorder_logger.info(f"   ID: {test_id}")
        recorder_logger.info(f"   Title: {test_title}")
