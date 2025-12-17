"""Factory for Plex user related use cases."""
from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.plex.repo.plexUserRepo import PlexUserRepo
from app.application.plex.queries.getPlexUsers import GetPlexUserQuery, GetPlexUserByIdQuery, GetPlexUserByNameQuery, GetPlexUserByPlexTokenQuery
from app.application.plex.useCases.createPlexUser import CreatePlexUserUseCase
from app.application.plex.useCases.updatePlexUser import UpdatePlexUserUseCase
from app.application.plex.useCases.deletePlexUser import DeletePlexUserUseCase
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

def createGetPlexUserQuery(session: AsyncSession = Depends(get_db)) -> GetPlexUserQuery:
    """Factory function to create GetPlexUserQuery with its dependencies."""
    repo = PlexUserRepo(session)
    return GetPlexUserQuery(repo)

def createGetPlexUserByIdQuery(session: AsyncSession = Depends(get_db)) -> GetPlexUserByIdQuery:
    """Factory function to create GetPlexUserByIdQuery with its dependencies."""
    repo = PlexUserRepo(session)
    return GetPlexUserByIdQuery(repo)

def createGetPlexUserByNameQuery(session: AsyncSession = Depends(get_db)) -> GetPlexUserByNameQuery:
    """Factory function to create GetPlexUserByNameQuery with its dependencies."""
    repo = PlexUserRepo(session)
    return GetPlexUserByNameQuery(repo)

def createGetPlexUserByPlexTokenQuery(session: AsyncSession = Depends(get_db)) -> GetPlexUserByPlexTokenQuery:
    """Factory function to create GetPlexUserByPlexTokenQuery with its dependencies."""
    repo = PlexUserRepo(session)
    return GetPlexUserByPlexTokenQuery(repo)

def createCreatePlexUserUseCase(session: AsyncSession = Depends(get_db)) -> CreatePlexUserUseCase:
    """Factory function to create CreatePlexUserUseCase with its dependencies."""
    repo = PlexUserRepo(session)
    return CreatePlexUserUseCase(repo)

def createUpdatePlexUserUseCase(session: AsyncSession = Depends(get_db)) -> UpdatePlexUserUseCase:
    """Factory function to create UpdatePlexUserUseCase with its dependencies."""
    repo = PlexUserRepo(session)
    return UpdatePlexUserUseCase(repo)

def createDeletePlexUserUseCase(session: AsyncSession = Depends(get_db)) -> DeletePlexUserUseCase:
    """Factory function to create DeletePlexUserUseCase with its dependencies."""
    repo = PlexUserRepo(session)
    return DeletePlexUserUseCase(repo)