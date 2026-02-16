from fastapi import APIRouter, Request
from domain.dto.map_data import MapRequest, MapDataResponse
from interfaces.i_map_view import I_MapView

router = APIRouter(prefix="/map", tags=["Map"])

@router.post("/", response_model=MapDataResponse)
def get_map_view(request_body: MapRequest, request: Request):
    map_view_service: I_MapView = request.app.state.map_view_service
    map_data = map_view_service.get_map_view(request_body)

    return MapDataResponse(map=map_data)
