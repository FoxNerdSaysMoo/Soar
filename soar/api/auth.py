from sanic import response, Blueprint
from sanic_limiter import Limiter, get_remote_address
import asyncio
import hashlib
import time
from .middleware import Middleware


class Auth:
    app = None

    @staticmethod
    def setup(_app):
        app = _app
        middleware = Middleware(app)

        bp = Blueprint(name="authapi", url_prefix="/api/auth")

        bp.middleware(middleware.check_auth, 'request')

        bp.add_route(Auth.register, '/register')
        bp.add_route(Auth.login, '/login')

        app.blueprint(bp)

    @staticmethod
    async def register(request):
        users = Auth.app.ctx.db["users"]
        data = request.json

        count = await users.count_documents({"username": data["un"]})

        if count > 0:
            return response.json({"error": "Username taken"})

        await users.insert_one({
            "username": data["un"],
            "password": hashlib.sha256(data["pw"].encode("utf-8")).hexdigest(),
            "created-at": time.time(),
            "friends": [],
            "friend-reqs": []  # Inbound
        })

        request.ctx.auth = data["un"]

        return response.json({"un": data["un"]})

    @staticmethod
    async def login(request):
        data = request.json
        users = Auth.app.ctx["users"]

        await asyncio.sleep(0.1)

        dig = hashlib.sha256(data["pw"].encode("utf-8")).hexdigest()
        if dig != (await users.find_one({"username": data["un"]}))["password"]:
            return response.json({"error": "incorrect password"})

        request.ctx.auth = data["un"]

        return response.json({"un": data["un"]})
