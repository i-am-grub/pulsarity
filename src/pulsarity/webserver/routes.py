"""
HTTP Rest API Routes
"""

import logging
from uuid import UUID

from starlette.requests import Request
from starlette.routing import Mount, Route
from starsessions.session import regenerate_session_id

from pulsarity.database.permission import SystemDefaultPerms
from pulsarity.database.pilot import Pilot
from pulsarity.database.user import User
from pulsarity.utils import background
from pulsarity.webserver import validation
from pulsarity.webserver.auth import PulsarityUser
from pulsarity.webserver.wrapper import endpoint

logger = logging.getLogger(__name__)


@endpoint(response_model=validation.BaseResponse)
async def check_auth(request: Request) -> validation.BaseResponse:
    """
    Check if a user is authenticated

    :return: The user's authentication status
    """
    auth_user: PulsarityUser = request.user
    return validation.BaseResponse(status=auth_user.is_authenticated)


@endpoint(
    request_model=validation.LoginRequest, response_model=validation.LoginResponse
)
async def login(
    request: Request, data: validation.LoginRequest
) -> validation.LoginResponse | None:
    """
    Pass the user credentials to log the user into the server

    :return: JSON containing the status of the request
    """
    user = await User.get_or_none(username=data.username)

    if user is not None and await user.verify_password(data.password):
        request.session.update({"auth_id": user.auth_id.hex})
        regenerate_session_id(request)

        logger.info("%s has been authenticated to the server", user.auth_id.hex)

        background.add_background_task(user.update_user_login_time)
        background.add_background_task(user.check_for_rehash, data.password)

        return validation.LoginResponse(
            status=True, password_reset_required=user.reset_required
        )

    return None


@endpoint(SystemDefaultPerms.AUTHENTICATED, response_model=validation.BaseResponse)
async def logout(request: Request) -> validation.BaseResponse:
    """
    Logout the currently connected client

    :return: JSON containing the status of the request
    """
    auth_user: PulsarityUser = request.user
    logger.info("Logging out user %s", auth_user.identity)

    request.session.clear()
    return validation.BaseResponse(status=True)


@endpoint(
    SystemDefaultPerms.AUTHENTICATED,
    request_model=validation.ResetPasswordRequest,
    response_model=validation.BaseResponse,
)
async def reset_password(
    request: Request, data: validation.ResetPasswordRequest
) -> validation.BaseResponse:
    """
    Resets the password for the client user

    :return: JSON containing the status of the request
    """
    auth_user: PulsarityUser = request.user
    uuid = UUID(hex=auth_user.identity)
    user = await User.get_by_uuid(uuid)

    if user is not None and await user.verify_password(data.old_password):
        await user.update_user_password(data.new_password)

        logger.info("Password reset for %s completed", auth_user.identity)

        background.add_background_task(user.update_password_required, False)

        return validation.BaseResponse(status=True)

    return validation.BaseResponse(status=False)


PilotModel = Pilot.generate_pydaantic_model()


@endpoint(
    SystemDefaultPerms.READ_PILOTS,
    response_model=PilotModel,
)
async def get_pilot(request: Request):
    """
    Get the pilot by id

    :return: Pilot data.
    """
    pilot_id: int = request.path_params["id"]
    pilot = await Pilot.get_by_id(pilot_id)

    if pilot is not None:
        return await PilotModel.from_tortoise_orm(pilot)


PilotModelList = Pilot.generate_pydaantic_queryset()


@endpoint(
    SystemDefaultPerms.READ_PILOTS,
    response_model=PilotModelList,
)
async def get_pilots():
    """
    A streaming route for getting all pilots currently stored in the
    database.

    :yield: A generator yielding pilots converted
    to a encoded JSON object.
    """
    return await PilotModelList.from_queryset(Pilot.all())


routes = [
    Route("/login", endpoint=login, methods=["POST"]),
    Route("/logout", endpoint=logout),
    Route("/auth-check", endpoint=check_auth),
    Route("/reset-password", endpoint=reset_password, methods=["POST"]),
    Mount(
        "/api",
        routes=[
            Route("/pilot/{id:int}", endpoint=get_pilot),
            Route("/pilot/all", endpoint=get_pilots),
        ],
        name="api",
    ),
]
