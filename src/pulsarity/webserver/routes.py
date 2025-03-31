"""
HTTP Rest API Routes
"""

import os
from uuid import UUID
import logging

from quart import ResponseReturnValue, render_template, send_from_directory
from quart_auth import login_user, logout_user, login_required
from quart_schema import validate_request, validate_response, hide
from pydantic import BaseModel
from werkzeug.exceptions import NotFound

from ..extensions import RHBlueprint, RHUser, current_user, current_app
from .auth import permission_required
from ..database.user import User
from ..database.pilot import Pilot
from ..database.permission import SystemDefaultPerms
from .validation import BaseResponse, LoginRequest, LoginResponse, ResetPasswordRequest

logger = logging.getLogger(__name__)


def _get_webapp_filepath() -> str:
    """
    Navigate to location of frontend artifacts

    :return: The path of the frontent build folder
    """

    current_location = __file__
    for _ in range(3):
        current_location = os.path.split(current_location)[0]

    target_location = os.path.join(
        current_location, "frontend", "dist", "prophazard-frontend", "browser"
    )

    return target_location


_app_folder = _get_webapp_filepath()
files = RHBlueprint("files", __name__, template_folder=_app_folder)


@files.get("/")
@hide
async def index() -> ResponseReturnValue:
    """
    Serves the web application to the client

    :return str: The rendered web page
    """
    return await render_template("index.html")


@files.get("/<path:path>")
@hide
async def static_proxy(path) -> ResponseReturnValue:
    """
    Serves the static files for the web application
    to the client

    :param path: The requested path for a file
    :return: The requested file
    """
    return await send_from_directory(_app_folder, path)


auth = RHBlueprint(
    "auth",
    __name__,
    url_prefix="/auth",
)


@auth.post("/")
@validate_response(BaseResponse)
async def check_auth() -> BaseResponse:
    """
    Check if a user is authenticated

    :return: The user's authentication status
    """
    status = await current_user.is_authenticated
    return BaseResponse(status=status)


@auth.post("/login")
@validate_request(LoginRequest)
@validate_response(LoginResponse)
async def login(data: LoginRequest) -> LoginResponse:
    """
    Pass the user credentials to log the user into the server

    :return: JSON containing the status of the request
    """
    user = await User.get_or_none(username=data.username)

    if user is not None and await user.verify_password(data.password):
        auth_user = RHUser(user.auth_id.hex)
        login_user(auth_user, True)

        logger.info("%s has been logged into the server", auth_user.auth_id)

        current_app.add_background_task(User.update_user_login_time)

        current_app.add_background_task(User.check_for_rehash, data.password)

        return LoginResponse(status=True, password_reset_required=user.reset_required)

    return LoginResponse(status=False)


@auth.get("/logout")
@login_required
@validate_response(BaseResponse)
async def logout() -> BaseResponse:
    """
    Logout the currently connected client

    :return: JSON containing the status of the request
    """
    logout_user()
    logger.info("Logged user (%s) out of the server", current_user.auth_id)
    return BaseResponse(status=True)


@auth.post("/reset-password")
@login_required
@validate_request(ResetPasswordRequest)
@validate_response(BaseResponse)
async def reset_password(data: ResetPasswordRequest) -> BaseResponse:
    """
    Resets the password for the client user

    :return: JSON containing the status of the request
    """
    uuid = UUID(hex=current_user.auth_id)
    user = await User.get_by_uuid(uuid)

    if user is not None and await user.verify_password(data.old_password):
        await user.update_user_password(data.new_password)

        logger.info("Password reset for %s completed", user.username)

        current_app.add_background_task(user.update_password_required, False)

        return BaseResponse(status=True)

    return BaseResponse(status=False)


api = RHBlueprint(
    "api",
    __name__,
    url_prefix="/api",
)

PilotModel = Pilot.generate_pydaantic_model()


@api.get("/pilot/<int:pilot_id>")
@permission_required(SystemDefaultPerms.READ_PILOTS)
@validate_response(PilotModel)
async def get_pilot(pilot_id: int) -> BaseModel:
    """
    Get the pilot by id

    :return: Pilot data.
    """
    pilot = await Pilot.get_by_id(pilot_id)

    if pilot is None:
        raise NotFound()

    return await PilotModel.from_tortoise_orm(pilot)


PilotModelList = Pilot.generate_pydaantic_queryset()


@api.get("/pilot/all")
@permission_required(SystemDefaultPerms.READ_PILOTS)
@validate_response(PilotModelList)
async def get_pilots() -> BaseModel:
    """
    A streaming route for getting all pilots currently stored in the
    database.

    :yield: A generator yielding pilots converted
    to a encoded JSON object.
    """
    return await PilotModelList.from_queryset(Pilot.all())
