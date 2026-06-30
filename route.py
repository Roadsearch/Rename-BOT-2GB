"""
route.py
Serveur aiohttp — maintient le Web Service Render actif.
Répond aux health checks sur GET /
"""
import logging
from datetime import datetime
from aiohttp import web

logger = logging.getLogger(__name__)
routes = web.RouteTableDef()


@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response({
        "status": "online",
        "bot": "LabZero Rename Bot",
        "time": datetime.utcnow().isoformat(),
    })


@routes.get("/health")
async def health_check(request):
    """Endpoint dédié pour UptimeRobot / services de ping externes."""
    return web.Response(text="OK", status=200)


async def web_server():
    web_app = web.Application(client_max_size=30_000_000)
    web_app.add_routes(routes)
    logger.info("[Route] Serveur aiohttp prêt")
    return web_app

# Développeur : LabZero — https://t.me/LabZero0
# Programmeur : Dev Suayki — https://t.me/Suayki
