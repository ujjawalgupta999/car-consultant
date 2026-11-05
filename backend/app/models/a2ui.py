from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field

class A2UIComponent(BaseModel):
    id: str
    component: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    children: List[str] = Field(default_factory=list)

class CreateSurfaceMessage(BaseModel):
    type: str = "createSurface"
    surfaceId: str
    catalogId: str = "automotive-standard-v1"
    title: Optional[str] = None
    position: str = "inline"

class UpdateComponentsMessage(BaseModel):
    type: str = "updateComponents"
    surfaceId: str
    components: List[A2UIComponent]

class UpdateDataModelMessage(BaseModel):
    type: str = "updateDataModel"
    surfaceId: str
    path: str
    value: Any

class DeleteSurfaceMessage(BaseModel):
    type: str = "deleteSurface"
    surfaceId: str

class A2UIActionPayload(BaseModel):
    session_id: str
    surface_id: str
    action_id: str
    data: Dict[str, Any] = Field(default_factory=dict)

