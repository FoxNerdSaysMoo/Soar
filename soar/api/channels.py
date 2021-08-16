from sanic import response, Blueprint
import asyncio
import datetime
import hashlib

from .middleware import Middleware
from .snowflakes import channel_snowflake


class Channels:
    app = None

    @staticmethod
    def setup(_app):
        app = _app
        middleware = Middleware(app)

        bp = Blueprint("channelsapi", url_prefix="/api/channels")
        bp.middleware(middleware.check_auth, "request")

        bp.add_route(Channels.create, "/create")
        app.blueprint(bp)

    @staticmethod
    async def create(self, request):
        data = request.json

        if data["scope"] in ["dm", "private"]:
            if "members" not in data:
                return response.json({"error": "members not provided"})

        date = datetime.datetime.now()

        channel = {
            "name": data["name"],
            "scope": data["scope"],
            "public": data["public"],
            "members": [] if data.get("members") is None else data["members"],
            "creator": request.ctx.auth,
            "attrs": {},
            "created-at": date,
            "message-tag": channel_snowflake(data["name"], request.ctx.auth, date),
            "parent": None,
            "roles": {}
        }

        await Channels.app.ctx.db["channels"].insert_one({**channel})

        return response.json(channel)
