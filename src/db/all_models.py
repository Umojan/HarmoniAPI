"""Import all models for Alembic autogeneration.

WARNING: This module should ONLY be imported inside Alembic env.py
for migration autogeneration purposes.

Import pattern in env.py:
    import src.db.all_models
"""

# Import all models here as they are created
from src.modules.admin.models import Admin  # noqa: F401
from src.modules.auth.models import EmailVerification  # noqa: F401
from src.modules.files.models import TariffFile  # noqa: F401
from src.modules.payment.models import Payment  # noqa: F401
from src.modules.tariffs.models import Tariff  # noqa: F401
from src.modules.users.models import User  # noqa: F401

__all__ = [
    "Admin",
    "EmailVerification",
    "Payment",
    "Tariff",
    "TariffFile",
    "User",
]
