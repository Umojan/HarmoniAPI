"""Import all models for Alembic autogeneration.

WARNING: This module should ONLY be imported inside Alembic env.py
for migration autogeneration purposes.

Import pattern in env.py:
    import src.db.all_models
"""

# Import all models here as they are created
from src.modules.admin.models import Admin  # noqa: F401
