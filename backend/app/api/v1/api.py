from fastapi import APIRouter

from .endpoints import devices, clusters, netbox, cables

api_router = APIRouter()

api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(clusters.router, prefix="/clusters", tags=["clusters"])
api_router.include_router(netbox.router, prefix="/netbox", tags=["netbox"])
api_router.include_router(cables.router, prefix="/cables", tags=["cables"])
