from field_service_room.dispatch_service import start_field_session
from field_service_room.work_order_models import StartFieldSessionRequest, WorkOrderPhoto


class RecordingRealtime:
    def __init__(self) -> None:
        self.published: dict = {}

    def create_channel(self, channel: str, request_key: str) -> dict:
        return {"channel": channel}

    def issue_token(self, client_id: str, channel: str) -> dict:
        return {"token": f"scoped-{client_id}"}

    def publish(self, channel: str, event: str, data: dict, account_id: str, request_key: str) -> dict:
        self.published = {"channel": channel, "event": event, "data": data}
        return {"published": True}


def test_completed_order_with_one_photo_requests_technician_follow_up() -> None:
    realtime = RecordingRealtime()
    request = StartFieldSessionRequest(
        work_order_id="WO-1842",
        dispatcher_id="dispatch-7",
        technician_id="tech-19",
        technician_name="Morgan Lee",
        dispatch_status="completed",
        photos=[WorkOrderPhoto(photo_id="photo-meter", label="meter after repair")],
    )

    result = start_field_session(request, realtime)

    assert result.channel == "work-order-WO-1842"
    assert result.follow_up_required is True
    assert {participant.client_id for participant in result.participants} == {"dispatch-7", "tech-19"}
    assert realtime.published["event"] == "dispatch.updated"
    assert realtime.published["data"]["follow_up_required"] is True

