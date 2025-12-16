"""Factory for Plex user related use cases."""
from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.plex.repo.plexUserRepo import PlexUserRepo
from app.application.plex.queries.getPlexUsers import GetPlexUserQuery, GetPlexUserByIdQuery, GetPlexUserByNameQuery, GetPlexUserByPlexTokenQuery
from app.application.plex.useCases.createPlexUser import CreatePlexUserUseCase
from app.application.plex.useCases.updatePlexUser import UpdatePlexUserUseCase
from app.application.plex.useCases.deletePlexUser import DeletePlexUserUseCase
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

def getGetPlexUsersQuery(session: AsyncSession = Depends(get_db)) -> GetPlexUserQuery:
    repo = PlexUserRepo(session)
    return GetPlexUserQuery(repo)

def getGetPlexUserByIdQuery(session: AsyncSession = Depends(get_db)) -> GetPlexUserByIdQuery:
    repo = PlexUserRepo(session)
    return GetPlexUserByIdQuery(repo)

def getGetPlexUserByNameQuery(session: AsyncSession = Depends(get_db)) -> GetPlexUserByNameQuery:
    repo = PlexUserRepo(session)
    return GetPlexUserByNameQuery(repo)

def getGetPlexUserByPlexTokenQuery(session: AsyncSession = Depends(get_db)) -> GetPlexUserByPlexTokenQuery:
    repo = PlexUserRepo(session)
    return GetPlexUserByPlexTokenQuery(repo)

def getCreatePlexUserUseCase(session: AsyncSession = Depends(get_db)) -> CreatePlexUserUseCase:
    repo = PlexUserRepo(session)
    return CreatePlexUserUseCase(repo)

def getUpdatePlexUserUseCase(session: AsyncSession = Depends(get_db)) -> UpdatePlexUserUseCase:
    repo = PlexUserRepo(session)
    return UpdatePlexUserUseCase(repo)

def getDeletePlexUserUseCase(session: AsyncSession = Depends(get_db)) -> DeletePlexUserUseCase:
    repo = PlexUserRepo(session)
    return DeletePlexUserUseCase(repo)