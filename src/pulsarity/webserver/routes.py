"""
HTTP Rest API Routes
"""

import logging
from uuid import UUID

from starlette.routing import Mount, Route
from starsessions.session import regenerate_session_id

from pulsarity import ctx
from pulsarity.database.heat import Heat, HeatAdapter, HeatListAdapter
from pulsarity.database.permission import SystemDefaultPerms
from pulsarity.database.pilot import Pilot, PilotAdapter, PilotListAdapter
from pulsarity.database.raceclass import (
    RaceClass,
    RaceClassAdapter,
    RaceClassListAdapter,
)
from pulsarity.database.raceevent import RaceEvent, RaceEventAdapter
from pulsarity.database.round import Round, RoundAdapter, RoundListAdapter
from pulsarity.database.user import User
from pulsarity.utils import background
from pulsarity.webserver.validation import (
    BaseResponse,
    LoginRequest,
    LoginResponse,
    ResetPasswordRequest,
)
from pulsarity.webserver.wrapper import endpoint

logger = logging.getLogger(__name__)


@endpoint(response_model=BaseResponse)
async def check_auth() -> BaseResponse:
    """
    Check if a user is authenticated

    :return: The user's authentication status
    """
    auth_user = ctx.user_ctx.get()
    return BaseResponse(status=auth_user.is_authenticated)


@endpoint(request_model=LoginRequest, response_model=LoginResponse)
async def login(data: LoginRequest) -> LoginResponse | None:
    """
    Pass the user credentials to log the user into the server

    :return: JSON containing the status of the request
    """
    user = await User.get_or_none(username=data.username)

    if user is not None and await user.verify_password(data.password):
        request = ctx.request_ctx.get()
        request.session.update({"auth_id": user.auth_id.hex})
        regenerate_session_id(request)

        logger.info("%s has been authenticated to the server", user.auth_id.hex)

        background.add_background_task(user.update_user_login_time)
        background.add_background_task(user.check_for_rehash, data.password)

        return LoginResponse(status=True, password_reset_required=user.reset_required)

    return None


@endpoint(SystemDefaultPerms.AUTHENTICATED, response_model=BaseResponse)
async def logout() -> BaseResponse:
    """
    Logout the currently connected client

    :return: JSON containing the status of the request
    """
    auth_user = ctx.user_ctx.get()
    logger.info("Logging out user %s", auth_user.identity)

    ctx.request_ctx.get().session.clear()
    return BaseResponse(status=True)


@endpoint(
    SystemDefaultPerms.AUTHENTICATED,
    request_model=ResetPasswordRequest,
    response_model=BaseResponse,
)
async def reset_password(data: ResetPasswordRequest) -> BaseResponse:
    """
    Resets the password for the client user

    :return: JSON containing the status of the request
    """
    auth_user = ctx.user_ctx.get()
    uuid = UUID(hex=auth_user.identity)
    user = await User.get_by_uuid(uuid)

    if user is not None and await user.verify_password(data.old_password):
        await user.update_user_password(data.new_password)

        logger.info("Password reset for %s completed", auth_user.identity)

        background.add_background_task(user.update_password_required, False)

        return BaseResponse(status=True)

    return BaseResponse(status=False)


@endpoint(SystemDefaultPerms.READ_PILOTS, response_adapter=PilotAdapter)
async def get_pilot() -> Pilot | None:
    """
    Get the pilot by id

    :return: Pilot data.
    """
    pilot_id: int = ctx.request_ctx.get().path_params["id"]
    return await Pilot.get_by_id(pilot_id)


@endpoint(SystemDefaultPerms.READ_PILOTS, response_adapter=PilotListAdapter)
async def get_pilots() -> list[Pilot]:
    """
    A route for getting all pilots currently stored in the
    database.

    :return: A JSON model of all pilots
    """
    return await Pilot.all()


@endpoint(SystemDefaultPerms.READ_EVENTS, response_adapter=RaceEventAdapter)
async def get_event() -> RaceEvent | None:
    """
    Get the event by id

    :return: Event data.
    """
    event_id: int = ctx.request_ctx.get().path_params["id"]
    return await RaceEvent.get_by_id(event_id)


@endpoint(SystemDefaultPerms.READ_EVENTS, response_adapter=RaceEventAdapter)
async def get_events() -> list[RaceEvent]:
    """
    A route for getting all events currently stored in the
    database.

    :return: A JSON model of all events
    """
    return await RaceEvent.all()


@endpoint(SystemDefaultPerms.READ_RACECLASS, response_adapter=RaceClassAdapter)
async def get_racelass() -> RaceClass | None:
    """
    Get the raceclass by id

    :return: Race Class data.
    """
    raceclass_id: int = ctx.request_ctx.get().path_params["id"]
    return await RaceClass.get_by_id(raceclass_id)


@endpoint(SystemDefaultPerms.READ_RACECLASS, response_adapter=RaceClassListAdapter)
async def get_raceclasses_for_event() -> list[RaceClass]:
    """
    A route for getting all raceclasses currently stored in the
    database.

    :return: A JSON model of all raceclasses
    """
    event_id: int = ctx.request_ctx.get().path_params["id"]
    return await RaceClass.filter(event_id=event_id)


@endpoint(SystemDefaultPerms.READ_ROUND, response_adapter=RoundAdapter)
async def get_round() -> Round | None:
    """
    Get the round by id
    """
    round_id: int = ctx.request_ctx.get().path_params["id"]
    return await Round.get_by_id(round_id)


@endpoint(SystemDefaultPerms.READ_ROUND, response_adapter=RoundListAdapter)
async def get_rounds_for_raceclass() -> list[Round]:
    """
    Gets all rounds for a specific racelass
    """
    raceclass_id: int = ctx.request_ctx.get().path_params["id"]
    return await Round.filter(raceclass_id=raceclass_id)


@endpoint(SystemDefaultPerms.READ_HEAT, response_adapter=HeatAdapter)
async def get_heat() -> Heat | None:
    """
    Get the heat by id
    """
    heat_id: int = ctx.request_ctx.get().path_params["id"]
    return await Heat.get_by_id(heat_id)


@endpoint(SystemDefaultPerms.READ_HEAT, response_adapter=HeatListAdapter)
async def get_heats_for_round() -> list[Heat]:
    """
    Gets all heats for a specific round
    """
    round_id: int = ctx.request_ctx.get().path_params["id"]
    return await Heat.filter(round_id=round_id)


routes = [
    Route("/login", endpoint=login, methods=["POST"]),
    Route("/logout", endpoint=logout),
    Route("/auth-check", endpoint=check_auth),
    Route("/reset-password", endpoint=reset_password, methods=["POST"]),
    Mount(
        "/api",
        routes=[
            Route("/pilots", endpoint=get_pilots),
            Route("/pilots/{id:int}", endpoint=get_pilot),
            Route("/events/", endpoint=get_event),
            Route("/events/{id:int}", endpoint=get_event),
            Route("/events/{id:int}/raceclasses", endpoint=get_raceclasses_for_event),
            Route("/raceclasses/{id:int}", endpoint=get_racelass),
            Route("/raceclasses/{id:int}/rounds", endpoint=get_rounds_for_raceclass),
            Route("/rounds/{id:int}", endpoint=get_round),
            Route("/rounds/{id:int}/heats", endpoint=get_heats_for_round),
            Route("/heats/{id:int}", endpoint=get_heat),
        ],
        name="api",
    ),
]
