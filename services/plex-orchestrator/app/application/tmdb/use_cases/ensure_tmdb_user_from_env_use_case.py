"""Create or update a TMDB user from environment variables when configured."""
import logging

from app.application.tmdb.use_cases.create_tmdb_user_use_case import CreateTmdbUserUseCase
from app.core.config import settings
from app.domain.models.tmdb_user import TmdbUser
from app.domain.ports.repositories.tmdb.tmdb_user_repository_port import TmdbUserRepoPort

logger = logging.getLogger(__name__)


class EnsureTmdbUserFromEnvUseCase:
    def __init__(
        self,
        repo: TmdbUserRepoPort,
        create_tmdb_user_use_case: CreateTmdbUserUseCase,
    ):
        self._repo = repo
        self._create_tmdb_user = create_tmdb_user_use_case

    async def execute(self) -> TmdbUser | None:
        access_token = (settings.tmdb_access_token or "").strip()
        if not access_token:
            return None

        name = (settings.tmdb_user_name or "default").strip() or "default"
        existing = await self._repo.get_user_by_name(name)
        if existing:
            if existing.access_token == access_token and existing.active:
                logger.debug("TMDB user '%s' already configured from env", name)
                return existing
            updated = existing.model_copy(
                update={
                    "access_token": access_token,
                    "account_id": settings.tmdb_account_id or existing.account_id,
                    "active": True,
                }
            )
            saved = await self._repo.update_user(updated)
            logger.info("Updated TMDB user '%s' from env", name)
            return saved

        user = TmdbUser(
            name=name,
            access_token=access_token,
            account_id=settings.tmdb_account_id,
            active=True,
        )
        created = await self._create_tmdb_user.execute(user)
        logger.info("Registered TMDB user '%s' from env", name)
        return created
