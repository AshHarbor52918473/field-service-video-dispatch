from typing import Literal

from pydantic import BaseModel, Field


DispatchStatus = Literal["assigned", "en_route", "on_site", "completed"]


class WorkOrderPhoto(BaseModel):
    photo_id: str = Field(min_length=1)
    label: str = Field(min_length=1)


class StartFieldSessionRequest(BaseModel):
    work_order_id: str = Field(min_length=1)
    dispatcher_id: str = Field(min_length=1)
    technician_id: str = Field(min_length=1)
    technician_name: str = Field(min_length=1)
    dispatch_status: DispatchStatus
    photos: list[WorkOrderPhoto] = Field(default_factory=list)


class ParticipantToken(BaseModel):
    client_id: str
    token: str


class FieldSessionResponse(BaseModel):
    channel: str
    dispatch_status: DispatchStatus
    follow_up_required: bool
    participants: list[ParticipantToken]

