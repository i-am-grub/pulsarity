"""
HTTP Rest API Routes
"""

import logging
from uuid import UUID

from starlette.responses import Response
from starlette.routing import Mount, Route
from starsessions.session import regenerate_session_id

from pulsarity import ctx
from pulsarity.database.heat import HEAT_ADAPTER, HEAT_LIST_ADAPTER, Heat
from pulsarity.database.permission import SystemDefaultPerms
from pulsarity.database.pilot import PILOT_ADAPTER, PILOT_LIST_ADAPTER, Pilot
from pulsarity.database.raceclass import (
    RACECLASS_ADAPTER,
    RACECLASS_LIST_ADAPTER,
    RaceClass,
)
from pulsarity.database.raceevent import (
    RACE_EVENT_ADAPTER,
    RACE_EVENT_LIST_ADAPTER,
    RaceEvent,
)
from pulsarity.database.round import ROUND_ADAPTER, ROUND_LIST_ADAPTER, Round
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


@endpoint(requires_auth=False, response_model=BaseResponse)
async def check_auth() -> BaseResponse:
    """
    Check if a user is authenticated

    :return: The user's authentication status
    """
    auth_user = ctx.user_ctx.get()
    return BaseResponse(status=auth_user.is_authenticated)


@endpoint(requires_auth=False, request_model=LoginRequest, response_model=LoginResponse)
async def login(data: LoginRequest) -> LoginResponse | Response:
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

    return Response(status_code=400)


@endpoint()
async def logout() -> Response:
    """
    Logout the currently connected client

    :return: JSON containing the status of the request
    """
    auth_user = ctx.user_ctx.get()
    logger.info("Logging out user %s", auth_user.identity)
    ctx.request_ctx.get().session.clear()
    return Response(status_code=200)


@endpoint(request_model=ResetPasswordRequest)
async def reset_password(data: ResetPasswordRequest) -> Response:
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

        return Response(status_code=200)

    return Response(status_code=400)


@endpoint(SystemDefaultPerms.READ_PILOTS, response_adapter=PILOT_ADAPTER)
async def get_pilot() -> Pilot | None:
    """
    Get the pilot by id

    :return: Pilot data.
    """
    pilot_id: int = ctx.request_ctx.get().path_params["id"]
    return await Pilot.get_by_id_with_attributes(pilot_id)


@endpoint(SystemDefaultPerms.READ_PILOTS, response_adapter=PILOT_LIST_ADAPTER)
async def get_pilots() -> list[Pilot]:
    """
    A route for getting all pilots currently stored in the
    database.

    :return: A JSON model of all pilots
    """
    return await Pilot.all().prefetch_related("attributes")


@endpoint(SystemDefaultPerms.READ_EVENTS, response_adapter=RACE_EVENT_ADAPTER)
async def get_event() -> RaceEvent | None:
    """
    Get the event by id

    :return: Event data.
    """
    event_id: int = ctx.request_ctx.get().path_params["id"]
    return await RaceEvent.get_by_id_with_attributes(event_id)


@endpoint(SystemDefaultPerms.READ_EVENTS, response_adapter=RACE_EVENT_LIST_ADAPTER)
async def get_events() -> list[RaceEvent]:
    """
    A route for getting all events currently stored in the
    database.

    :return: A JSON model of all events
    """
    return await RaceEvent.all().prefetch_related("attributes")


@endpoint(SystemDefaultPerms.READ_RACECLASS, response_adapter=RACECLASS_ADAPTER)
async def get_racelass() -> RaceClass | None:
    """
    Get the raceclass by id

    :return: Race Class data.
    """
    raceclass_id: int = ctx.request_ctx.get().path_params["id"]
    return await RaceClass.get_by_id_with_attributes(raceclass_id)


@endpoint(SystemDefaultPerms.READ_RACECLASS, response_adapter=RACECLASS_LIST_ADAPTER)
async def get_raceclasses_for_event() -> list[RaceClass]:
    """
    A route for getting all raceclasses currently stored in the
    database.

    :return: A JSON model of all raceclasses
    """
    event_id: int = ctx.request_ctx.get().path_params["id"]
    return await RaceClass.filter(event_id=event_id).prefetch_related("attributes")


@endpoint(SystemDefaultPerms.READ_ROUND, response_adapter=ROUND_ADAPTER)
async def get_round() -> Round | None:
    """
    Get the round by id
    """
    round_id: int = ctx.request_ctx.get().path_params["id"]
    return await Round.get_by_id_with_attributes(round_id)


@endpoint(SystemDefaultPerms.READ_ROUND, response_adapter=ROUND_LIST_ADAPTER)
async def get_rounds_for_raceclass() -> list[Round]:
    """
    Gets all rounds for a specific racelass
    """
    raceclass_id: int = ctx.request_ctx.get().path_params["id"]
    return await Round.filter(raceclass_id=raceclass_id).prefetch_related("attributes")


@endpoint(SystemDefaultPerms.READ_HEAT, response_adapter=HEAT_ADAPTER)
async def get_heat() -> Heat | None:
    """
    Get the heat by id
    """
    heat_id: int = ctx.request_ctx.get().path_params["id"]
    return await Heat.get_by_id_with_attributes(heat_id)


@endpoint(SystemDefaultPerms.READ_HEAT, response_adapter=HEAT_LIST_ADAPTER)
async def get_heats_for_round() -> list[Heat]:
    """
    Gets all heats for a specific round
    """
    round_id: int = ctx.request_ctx.get().path_params["id"]
    return await Heat.filter(round_id=round_id).prefetch_related("attributes")


routes = [
    Route("/login", endpoint=login, methods=["POST"]),
    Route("/logout", endpoint=logout),
    Route("/auth-check", endpoint=check_auth),
    Route("/reset-password", endpoint=reset_password, methods=["POST"]),
    Mount(
        "/api",
        routes=[
            Route("/pilots/{id:int}", endpoint=get_pilot),
            Route("/pilots", endpoint=get_pilots),
            Route("/events/{id:int}", endpoint=get_event),
            Route("/events", endpoint=get_events),
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
