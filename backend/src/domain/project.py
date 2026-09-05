"""Project membership roles."""

from enum import StrEnum


class ProjectRole(StrEnum):
    """Roles available to a project member."""

    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"
