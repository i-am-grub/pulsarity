"""
HTTP Rest API Routes
"""

from uuid import UUID
from collections.abc import AsyncGenerator
import logging

from quart import ResponseReturnValue, render_template_string
from quart_auth import login_user, logout_user
from quart_schema import validate_request, validate_response

from ..extensions import RHBlueprint, RHUser, current_user, current_app
from .auth import permission_required
from ..database.user import SystemDefaults
from .validation import BaseResponse, LoginRequest, LoginResponse, ResetPasswordRequest

logger = logging.Logger(__name__)

routes = RHBlueprint("routes", __name__)


@routes.get("/")
async def index() -> ResponseReturnValue:
    """
    Serves the web application to the client

    :return str: The rendered web page
    """
    return await render_template_string("<body><h1>Hello World!</h1></body>")


@routes.post("/login")
@validate_request(LoginRequest)
@validate_response(LoginResponse)
async def login(data: LoginRequest) -> LoginResponse:
    """
    Pass the user credentials to log the user into the server

    :return dict: JSON containing the status of the request
    """
    database = await current_app.get_user_database()
    user = await database.users.get_by_username(None, data.username)

    if user is not None and await user.verify_password(data.password):
        auth_user = RHUser(user.auth_id.hex)
        login_user(auth_user)

        logger.info("%s has been logged into the server", auth_user.auth_id)

        current_app.add_background_task(
            database.users.update_user_login_time, None, user
        )

        current_app.add_background_task(
            database.users.check_for_rehash, None, user, data.password
        )

        return LoginResponse(status=True, password_reset_required=user.reset_required)

    return LoginResponse(status=False)


@routes.get("/logout")
@validate_response(BaseResponse)
async def logout() -> BaseResponse:
    """
    Logout the currently connected client

    :return dict: JSON containing the status of the request
    """
    logout_user()
    logger.info("Logged user (%s) out of the server", current_user.auth_id)
    return BaseResponse(status=True)


@routes.post("/reset-password")
@permission_required(SystemDefaults.RESET_PASSWORD)
@validate_request(ResetPasswordRequest)
@validate_response(BaseResponse)
async def reset_password(data: ResetPasswordRequest) -> BaseResponse:
    """
    Resets the password for the client user

    :return dict: JSON containing the status of the request
    """
    uuid = UUID(hex=current_user.auth_id)

    database = await current_app.get_user_database()
    user = await database.users.get_by_uuid(None, uuid)

    if user is not None and await user.verify_password(data.old_password):
        await database.users.update_user_password(None, user, data.new_password)

        logger.info("Password reset for %s completed", user.username)

        current_app.add_background_task(
            database.users.update_password_required, None, user, False
        )

        return BaseResponse(status=True)

    return BaseResponse(status=False)


@routes.get("/pilots")
@permission_required(SystemDefaults.READ_PILOTS)
async def get_pilots() -> AsyncGenerator[bytes, None]:
    """
    A streaming route for getting all pilots currently stored in the
    database.

    :yield AsyncGenerator[bytes, None]: A generator yielding pilots converted
    to a encoded JSON object.
    """
    database = await current_app.get_race_database()

    async def stream_pilots():
        async for pilot in database.pilots.get_all_as_stream(None):
            yield pilot.to_bytes()

    return stream_pilots()
