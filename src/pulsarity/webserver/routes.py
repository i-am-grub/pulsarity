"""
HTTP Rest API Routes
"""

import logging

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from ..database.pilot import Pilot
from .auth import PulsarityUser
from .validation import BaseResponse

logger = logging.getLogger(__name__)


async def check_auth(request: Request):
    """
    Check if a user is authenticated

    :return: The user's authentication status
    """
    user: PulsarityUser = request.user
    return BaseResponse(status=user.is_authenticated)


# async def login(request: Request) -> LoginResponse | None:
#     """
#     Pass the user credentials to log the user into the server

#     :return: JSON containing the status of the request
#     """
#     if request.method != "POST":
#         return None

#     data = await request.json()
#     user = await User.get_or_none(username=data["username"])

#     if user is not None and await user.verify_password(data.password):
#         auth_user = AppUser(user.auth_id.hex)
#         login_user(auth_user, True)

#         logger.info("%s has been logged into the server", auth_user.auth_id)

#         current_app.add_background_task(User.update_user_login_time)

#         current_app.add_background_task(User.check_for_rehash, data.password)

#         return LoginResponse(status=True, password_reset_required=user.reset_required)

#     return None


# async def logout(request: Request):
#     """
#     Logout the currently connected client

#     :return: JSON containing the status of the request
#     """
#     logout_user()
#     logger.info("Logged user (%s) out of the server", current_user.auth_id)
#     return BaseResponse(status=True)


# async def reset_password(request: Request):
#     """
#     Resets the password for the client user

#     :return: JSON containing the status of the request
#     """
#     uuid = UUID(hex=current_user.auth_id)
#     user = await User.get_by_uuid(uuid)

#     if user is not None and await user.verify_password(data.old_password):
#         await user.update_user_password(data.new_password)

#         logger.info("Password reset for %s completed", user.username)

#         current_app.add_background_task(user.update_password_required, False)

#         return BaseResponse(status=True)

#     return BaseResponse(status=False)


PilotModel = Pilot.generate_pydaantic_model()


async def get_pilot(request: Request):
    """
    Get the pilot by id

    :return: Pilot data.
    """
    pilot_id: int = request.path_params["id"]
    pilot = await Pilot.get_by_id(pilot_id)

    if pilot is not None:
        model = await PilotModel.from_tortoise_orm(pilot)
        return JSONResponse(model)


PilotModelList = Pilot.generate_pydaantic_queryset()


async def get_pilots(_request: Request):
    """
    A streaming route for getting all pilots currently stored in the
    database.

    :yield: A generator yielding pilots converted
    to a encoded JSON object.
    """
    model = await PilotModelList.from_queryset(Pilot.all())
    return JSONResponse(model)


routes = [
    Route("/", endpoint=check_auth),
    # Mount(
    #     "/auth",
    #     routes=[
    #         Route("/login", endpoint=login),
    #         Route("/logout", endpoint=logout),
    #         Route("/reset-password", endpoint=reset_password),
    #     ],
    # ),
    Mount(
        "/api",
        routes=[
            Route("/pilot/{id:int}", endpoint=get_pilot),
            Route("/pilot/all", endpoint=get_pilots),
        ],
    ),
]
