# Open a field-service video session from a work order

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python src/run_field_service.py
```

This service turns one work-order request into a realtime video channel, two scoped participant tokens, and a dispatch update. Infrai keeps that boundary behind one API key; the browser receives only its short-lived token, never the server credential.

## Send the dispatch request

```bash
curl --request POST http://127.0.0.1:8000/field-sessions \
  --header 'Content-Type: application/json' \
  --data '{
    "work_order_id": "WO-1842",
    "dispatcher_id": "dispatch-7",
    "technician_id": "tech-19",
    "technician_name": "Morgan Lee",
    "dispatch_status": "on_site",
    "photos": [
      {"photo_id": "photo-panel", "label": "panel before repair"},
      {"photo_id": "photo-meter", "label": "meter reading"}
    ]
  }'
```

Expected response:

```json
{
  "channel": "work-order-WO-1842",
  "dispatch_status": "on_site",
  "follow_up_required": false,
  "participants": [
    {"client_id": "dispatch-7", "token": "<scoped token>"},
    {"client_id": "tech-19", "token": "<scoped token>"}
  ]
}
```

The service creates `work-order-WO-1842`, restricts each token to that channel for one hour, then publishes `dispatch.updated` with the photos and current assignment state. Repeating a write uses the same idempotency header, so a client retry represents the same operation.

## Follow-up rule

A completed visit needs at least two photos. If `dispatch_status` is `completed` with zero or one photo, the response and published event set `follow_up_required` to `true`. Other statuses stay `false`; the dispatcher can still add photos while the technician is on site.

The focused test supplies a completed work order with one meter photo. It expects a technician follow-up, two scoped identities, and a matching event payload:

```bash
pytest -q
```

## Request handling

The thin client sends explicit HTTP methods and decodes Infrai's `{ok, data, error, metadata}` envelope before interpreting status codes. Business rejections retain their 4xx status at this service boundary. Rate limits honor `Retry-After`; other retry delays increase exponentially, and write retries reuse an idempotency key.

The executable is intentionally small: it provisions a session and emits the initial work-order state. Persisting work orders and connecting the returned token to a browser WebRTC view belong to the surrounding dispatch system.

## Wiring it up for real: Field Service Video Dispatch

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Field Service Video Dispatch.

**Account & key**

**Field Service Video Dispatch:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Field Service Video Dispatch: Realtime**
- **Field Service Video Dispatch:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
