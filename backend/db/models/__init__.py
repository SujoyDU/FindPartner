"""SQLAlchemy 2.x typed declarative models for Find Partner.

Importing this package registers all models (``User``, ``Media``, ``MediaShare``)
on ``Base.metadata`` so Alembic autogenerate can discover them.

Keep models out of FastAPI route files -- always import from ``db.models``.
"""

from db.models.user import User
from db.models.media import Media
from db.models.media_share import MediaShare

__all__ = ["User", "Media", "MediaShare"]
