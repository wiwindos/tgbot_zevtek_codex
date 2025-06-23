from aiohttp import web


async def ping(request: web.Request) -> web.Response:
    return web.Response(text="pong")


async def start() -> web.AppRunner:
    app = web.Application()
    app.add_routes([web.get("/ping", ping)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    return runner
