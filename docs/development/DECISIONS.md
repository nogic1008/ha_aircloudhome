# Architectural and Design Decisions

This document records significant architectural and design decisions made during the development of this integration.

## Format

Each decision is documented with:

- **Date:** When the decision was made
- **Context:** Why this decision was necessary
- **Decision:** What was decided
- **Rationale:** Why this approach was chosen
- **Consequences:** Expected impacts and trade-offs

---

## Decision Log

### Use DataUpdateCoordinator for All Data Fetching

**Date:** 2025-11-29 (Template initialization)

**Context:** The integration needs to fetch data from an external API and share it with multiple entities. Home Assistant provides several patterns for this.

**Decision:** Use `DataUpdateCoordinator` from `homeassistant.helpers.update_coordinator` as the central data management component.

**Rationale:**

- Provides built-in support for update intervals and error handling
- Automatic retry with exponential backoff
- Shared data access prevents duplicate API calls
- Standard pattern recommended by Home Assistant
- Entities automatically become unavailable when coordinator fails

**Consequences:**

- All entities must inherit from `CoordinatorEntity`
- Single update interval applies to all entities
- Data is fetched even if no entities are enabled
- Coordinator manages entity lifecycle and availability

---

### Separate API Client from Coordinator

**Date:** 2025-11-29 (Template initialization)

**Context:** The coordinator needs to fetch data, but business logic should be separated from data transport.

**Decision:** Implement API communication in separate `api/client.py` module, coordinator only orchestrates updates.

**Rationale:**

- Separation of concerns: transport vs. orchestration
- Easier to test API client in isolation
- Simpler to swap API implementation if needed
- Clearer error handling boundaries

**Consequences:**

- Additional abstraction layer
- Coordinator depends on API client
- API client raises custom exceptions for error translation

---

### Platform-Specific Directories

**Date:** 2025-11-29 (Template initialization)

**Context:** Integration supports multiple platforms (sensor, binary_sensor, switch, etc.).

**Decision:** Each platform gets its own directory with individual entity files.

**Rationale:**

- Clear organization as integration grows
- Easier to find specific entity implementations
- Supports multiple entities per platform cleanly
- Follows Home Assistant Core pattern

**Consequences:**

- More files/directories than single-file approach
- Platform `__init__.py` must import and register entities
- Slightly more initial setup overhead

---

### EntityDescription for Static Metadata

**Date:** 2025-11-29 (Template initialization)

**Context:** Entities have static metadata (name, icon, device class) that doesn't change.

**Decision:** Use `EntityDescription` dataclasses to define static entity metadata.

**Rationale:**

- Declarative and easy to read
- Type-safe with dataclasses
- Recommended Home Assistant pattern
- Separates static configuration from dynamic behavior

**Consequences:**

- Each entity type needs an EntityDescription
- Dynamic entities need custom handling
- Static and dynamic properties clearly separated

---

### Support Both AirCloud Home Regions via a Stored Region

**Date:** 2026-11-04

**Context:** AirCloud Home has a Japan cloud (`api-kuma`, Shirokuma-kun app) and a Europe / global cloud (`api-global-prod`, airCloud Go app). Accounts exist in only one of them. The two APIs share the same endpoints but differ in required headers and some payload fields.

**Decision:** Store the region in the config entry (`region`, chosen in the setup and reconfigure forms) and pass it to the API client, which picks the base URL. Absorb payload differences in the API layer (`normalize_device_list`) so the coordinator and entities stay region-agnostic.

**Rationale:**

- Explicit choice is predictable. Auto-detection would need failed sign-in attempts against the wrong cloud.
- Defaulting to Japan keeps existing entries working without a config entry migration.
- Normalizing in one place keeps region checks out of entity code.

**Consequences:**

- Users must pick the right region; the form explains which app maps to which region.
- New region-specific quirks belong in `api/client.py`, not in entities.

---

## Future Considerations

### State Restoration

**Status:** Not yet implemented

Consider implementing state restoration for switches and configurable settings to maintain state across Home Assistant restarts when the external device is unavailable.

### Multi-Device Support

**Status:** Not yet implemented

Current architecture assumes single device per config entry. If multi-device support is needed, coordinator data structure will need redesign to map device ID → data.

### Polling vs. Push

**Status:** Uses polling

Currently implements polling-based updates. If the API supports webhooks or WebSocket, consider implementing push-based updates for real-time responsiveness.

---

## Decision Review

These decisions should be reviewed periodically (suggested: quarterly or when major features are added) to ensure they still serve the integration's needs.
