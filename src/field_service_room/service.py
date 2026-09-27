from fastapi import FastAPI, HTTPException

from .dispatch_service import start_field_session
from .infrai_realtime import InfraiError, InfraiRealtimeClient
from .work_order_models import FieldSessionResponse, StartFieldSessionRequest

app = FastAPI(title="Field service video dispatch")


@app.post("/field-sessions", response_model=FieldSessionResponse)
def create_field_session(request: StartFieldSessionRequest) -> FieldSessionResponse:
    client = InfraiRealtimeClient()
    try:
        return start_field_session(request, client)
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=exc.detail) from exc
    finally:
        client.close()

