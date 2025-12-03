"""
Security Module

This module provides enterprise-grade security features including:
- Audit logging for LLM interactions
- Credential leak detection
- Compliance report generation

Example usage:
    from src.security.audit_logger import AuditLogger
    
    audit = AuditLogger()
    audit.register_credentials(username, password)
    audit.log_llm_request(prompt="...")
    report = audit.generate_compliance_report()
"""

from .audit_logger import AuditLogger

__all__ = ['AuditLogger']
