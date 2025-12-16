from pydantic import BaseModel
from app.domain.models.media import MediaType
class IsItemInLibraryResponse(BaseModel):
    has_media: bool

class IsItemInLibraryRequest(BaseModel):
    userToken: str
    guid: str
    type: MediaType