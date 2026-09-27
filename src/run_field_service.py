import uvicorn


if __name__ == "__main__":
    uvicorn.run("field_service_room.service:app", host="127.0.0.1", port=8000, reload=False)

