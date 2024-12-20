"""
HTTP Rest API Routes
"""

from uuid import UUID

from quart import render_template_string, request
from quart_auth import login_user, logout_user

from ..database.user import User
from ..extensions import RHBlueprint, RHUser, current_user, current_app
from ..auth._authorizer import permission_required
from ..auth._permissions import UserPermission

routes = RHBlueprint("routes", __name__)


@routes.get("/")
async def index():
    return await render_template_string("<body><h1>Hello World!</h1></body>")


@routes.post("/login")
async def login():
    data: dict[str, str] = await request.get_json()

    if "username" in data and "password" in data:
        database = await current_app.get_user_database()
        user = await database.users.get_by_username(None, data["username"])

        if user is not None and await user.verify_password(data["password"]):
            login_user(RHUser(user.auth_id.hex))

            current_app.add_background_task(
                database.users.update_user_login_time(None, user)
            )

            current_app.add_background_task(
                database.users.check_for_rehash(None, user, data["password"])
            )

            return {"success": True}

    return {"success": False}


@routes.get("/logout")
async def logout():
    logout_user()
    return {"success": True}


@routes.post("/reset-password")
@permission_required(UserPermission.RESET_PASSWORD)
async def reset_password():
    data: dict[str, str] = await request.get_json()

    if all(["password" in data, "new_password" in data]):

        uuid = UUID(hex=current_user.auth_id)

        database = await current_app.get_user_database()
        user = await database.users.get_by_uuid(None, uuid)

        if user is not None and await user.verify_password(data["password"]):
            await database.users.update_user_password(None, user, data["new_password"])
            return {"success": True}

    return {"success": False}


@routes.get("/pilots")
@permission_required(UserPermission.READ_PILOTS)
async def get_pilots():
    database = await current_app.get_user_database()
    return {"status": True}
