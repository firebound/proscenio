"""Individual pre-export check families.

Each module owns one check family and exposes a single ``validate_*`` entry
point that ``validation.export.validate_export`` orchestrates. Kept bpy-free
(duck-typed getattr access) so the headless writer and pytest exercise them
without registering the addon.
"""
