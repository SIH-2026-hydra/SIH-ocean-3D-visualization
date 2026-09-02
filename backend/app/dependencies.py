from app.core.config import settings
from app.repositories import create_repository


repository = create_repository(settings)


def get_repository():
    """Return the application-wide configured repository instance."""
    return repository