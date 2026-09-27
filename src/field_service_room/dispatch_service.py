from abc import abstractmethod
from typing import Protocol

from .work_order_models import FieldSessionResponse, ParticipantToken, StartFieldSessionRequest


class RealtimePort(Protocol):
    @abstractmethod
    def create_channel(self, channel: str, request_key: str) -> dict:
        raise AssertionError("protocol method")

    @abstractmethod
    def issue_token(self, client_id: str, channel: str) -> dict:
        raise AssertionError("protocol method")

    @abstractmethod
    def publish(self, channel: str, event: str, data: dict, account_id: str, request_key: str) -> dict:
        raise AssertionError("protocol method")


def start_field_session(request: StartFieldSessionRequest, realtime: RealtimePort) -> FieldSessionResponse:
    channel = f"work-order-{request.work_order_id}"
    follow_up_required = request.dispatch_status == "completed" and len(request.photos) < 2
    realtime.create_channel(channel, f"{request.work_order_id}:channel")

    participants = []
    for role, client_id in (("dispatcher", request.dispatcher_id), ("technician", request.technician_id)):
        issued = realtime.issue_token(client_id, channel)
        participants.append(ParticipantToken(client_id=client_id, token=issued["token"]))

    realtime.publish(
        channel,
        "dispatch.updated",
        {
            "work_order_id": request.work_order_id,
            "dispatch_status": request.dispatch_status,
            "technician_name": request.technician_name,
            "photos": [photo.model_dump() for photo in request.photos],
            "follow_up_required": follow_up_required,
        },
        request.dispatcher_id,
        f"{request.work_order_id}:dispatch:{request.dispatch_status}",
    )
    return FieldSessionResponse(
        channel=channel,
        dispatch_status=request.dispatch_status,
        follow_up_required=follow_up_required,
        participants=participants,
    )
