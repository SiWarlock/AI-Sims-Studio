"""Shared frozen contracts for AI Sims Creator.

Pydantic v2 models are the single source of truth (§2.5, §4): emitted to JSON-Schema
and codegen'd to TS/Node for the desktop UI and the export worker. Every other area
imports from here; this package imports from no other area.
"""

from aisims_contracts.error import ErrorCategory, ErrorCode, ErrorEnvelope

__all__ = ["ErrorCategory", "ErrorCode", "ErrorEnvelope"]
