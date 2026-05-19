"""bpy-bound skinning helpers (SPEC 013.2).

Public surface: pre-flight diagnose collection + bind application.
"""

from .bind_apply import apply_bind
from .diagnose_collect import collect_diagnoses_for_object

__all__ = ["apply_bind", "collect_diagnoses_for_object"]
