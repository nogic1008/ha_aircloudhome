# AirCloud Home API Reference

This document describes the AirCloud Home cloud API endpoints used by this integration.

**Base URL:** `https://api-kuma.aircloudhome.com`

> **Tested hardware:** API behaviour documented here was verified against a **Hitachi RAS-X40L2**. Other **room air conditioners (RAC)** connected via AirCloud Home should be compatible. Packaged air conditioners (PAC) use a separate API and are out of scope for this integration.

## Authentication

### Sign In

Authenticates a user and returns JWT access and refresh tokens.

- **URL:** `POST /iam/auth/sign-in`
- **Headers:**
  - `Content-Type: application/json`

**Request body:**

```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response — 200 OK:**

```json
{
  "token": "<access_token>",
  "refreshToken": "<refresh_token>",
  "newUser": false,
  "errorState": "NONE",
  "access_token_expires_in": 1209600000,
  "refresh_token_expires_in": 7776000000
}
```

| Field | Description |
| ----- | ----------- |
| `token` | JWT access token (valid for ~14 days: `access_token_expires_in` ms) |
| `refreshToken` | JWT refresh token (valid for ~90 days: `refresh_token_expires_in` ms) |
| `newUser` | Intended to indicate a new user, but observed to return `true` for existing users as well — exact semantics unclear |
| `errorState` | `"NONE"` on success |

**Response — 401 Unauthorized:** Invalid email or password.

---

### Token Refresh

Obtains a new access token using a valid refresh token.

- **URL:** `POST /iam/auth/refresh`
- **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer <refresh_token>`
  - `isRefreshToken: true`
- **Body:** none

**Response — 200 OK:**

```json
{
  "token": "<new_access_token>",
  "refreshToken": "<new_refresh_token>",
  "errorState": "NONE",
  "access_token_expires_in": 1209600000
}
```

---

## Device Information

Device data is structured in **family groups**. A single account may belong to multiple family groups, each containing one or more AC units (IDUs). Fetch the family group list first, then query each group for its devices.

### List Family Groups

Returns all family groups the authenticated user belongs to.

- **URL:** `GET /iam/family-account/v2/groups`
- **Headers:**
  - `Authorization: Bearer <access_token>`

**Response — 200 OK:**

```json
{
  "message": "",
  "result": [
    {
      "familyId": 100001,
      "familyName": "My Home",
      "createdBy": "user@example.com",
      "role": {
        "id": 1,
        "name": "OWNER",
        "level": 1
      },
      "pictureData": null
    }
  ]
}
```

| Field | Description |
| ----- | ----------- |
| `familyId` | Unique identifier for the family group — used in subsequent API calls |
| `role.name` | User's role in the group (`OWNER`, etc.) |

---

### List IDUs in Family Group

Returns all AC units (indoor units / IDUs) registered to a family group.

- **URL:** `GET /rac/ownership/groups/{familyId}/idu-list`
- **Headers:**
  - `Authorization: Bearer <access_token>`

**Response — 200 OK:**

```json
[
  {
    "userId": "000000",
    "serialNumber": "XXXX-XXXX-XXXX",
    "model": "HITACHI",
    "id": 10001,
    "vendorThingId": "JCH-xxxxxxxx",
    "name": "Living Room",
    "roomTemperature": 21.5,
    "mode": "HEATING",
    "iduTemperature": 21.0,
    "humidity": 50,
    "power": "ON",
    "relativeTemperature": 0.0,
    "fanSpeed": "AUTO",
    "fanSwing": "AUTO",
    "updatedAt": 1700000000000,
    "lastOnlineUpdatedAt": 1700000000000,
    "racTypeId": 6,
    "iduFrostWash": false,
    "specialOperation": false,
    "criticalError": false,
    "zoneId": "Asia/Tokyo",
    "scheduleType": "SCHEDULE_DISABLED",
    "online": true
  }
]
```

**Key fields:**

| Field | Values | Description |
| ----- | ------ | ----------- |
| `id` | integer | Device ID — used as `racId` in control commands |
| `vendorThingId` | string | Vendor-assigned device identifier (contains partial MAC address) |
| `model` | string | Manufacturer name (e.g. `"HITACHI"`) |
| `serialNumber` | string | Unit serial number (observed to be `"XXXX-XXXX-XXXX"` in real data — may not be uniquely set per device) |
| `name` | string | User-defined room name (may contain non-ASCII) |
| `online` | boolean | Whether the device is currently reachable |
| `power` | `"ON"` \| `"OFF"` | Current power state |
| `mode` | see below | Current operating mode |
| `fanSpeed` | see below | Current fan speed |
| `fanSwing` | see below | Current swing direction |
| `iduTemperature` | float | Target temperature (°C, 0.5° increments) |
| `roomTemperature` | float | Current room temperature (°C) |
| `humidity` | integer | Target humidity setting (40–60%) |

**`mode` values:**

| API value | Meaning |
| --------- | ------- |
| `HEATING` | Heat |
| `COOLING` | Cool |
| `FAN` | Fan only |
| `DRY` | Dry |
| `DRY_COOL` | Cool-dry (涼快) |
| `AUTO` | Auto |
| `UNKNOWN` | Unknown / other |

**`fanSpeed` values:** `AUTO`, `LV1`, `LV2`, `LV3`, `LV4`, `LV5`

**`fanSwing` values:**

| API value | Meaning |
| --------- | ------- |
| `AUTO` | Auto swing |
| `OFF` | Swing off |
| `VERTICAL` | Vertical sweep |
| `HORIZONTAL` | Horizontal sweep |
| `ALL` | All directions |

---

## Device Control

### Send Control Command

Updates the operating state of an AC unit. All five required fields must be included; omitting any required field returns `400 Bad Request`. For fields you are not changing, pass the current device value.

- **URL:** `PUT /rac/basic-idu-control/general-control-command/{racId}?familyId={familyId}`
- **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer <access_token>`

**Request body:**

```json
{
  "power": "ON",
  "mode": "HEATING",
  "fanSpeed": "AUTO",
  "fanSwing": "OFF",
  "iduTemperature": 21.5,
  "humidity": 50
}
```

**Required fields:**

| Field | Values | Description |
| ----- | ------ | ----------- |
| `power` | `"ON"` \| `"OFF"` | Power state |
| `mode` | `HEATING` \| `COOLING` \| `FAN` \| `DRY` \| `DRY_COOL` \| `AUTO` \| `UNKNOWN` | Operating mode |
| `fanSpeed` | `AUTO` \| `LV1` \| `LV2` \| `LV3` \| `LV4` \| `LV5` | Fan speed |
| `fanSwing` | `AUTO` \| `OFF` \| `VERTICAL` \| `HORIZONTAL` \| `ALL` | Swing direction |
| `iduTemperature` | float (16–32, step 0.5) | Target temperature (°C) |

**Optional fields:**

| Field | Values | Description |
| ----- | ------ | ----------- |
| `humidity` | integer (40–60, step 5) | Target humidity (%) |

**Response — 200 OK:**

```json
{
  "commandId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "thingId": "th.xxxxxxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

The response confirms the command was accepted; actual device state change is asynchronous. Poll the IDU list to confirm the updated state.
