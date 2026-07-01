from aiohttp import web

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("LabZero")


async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app






# Channel dev : LabZero (https://t.me/LabZero0)
# Developer : Dev Suayki (https://t.me/Suayki)
