#ifndef FORWARD_GUARD_H
#define FORWARD_GUARD_H

#include <stdbool.h>
#include <stdint.h>

#define FORWARD_GUARD_MAX_LEASE_MS 200u
#define FORWARD_GUARD_MAX_MOVE_MS 300u

typedef struct {
    uint64_t session_id;
    uint64_t frame_id;
    uint64_t command_id;
    uint64_t observed_ms;
    uint64_t vision_received_ms;
    uint64_t drive_started_ms;
    uint32_t vision_remaining_ms;
    uint32_t drive_duration_ms;
} ForwardGuard;

/* Serialize calls and use a local monotonic millisecond clock. Reset once at boot. */
void forward_guard_reset(ForwardGuard *guard);

/* Begin a validated transport session with a higher positive receiver epoch. */
bool forward_guard_begin_session(ForwardGuard *guard, uint64_t session_id, uint64_t now_ms);

/* Lease budget has already accounted for capture age and worst-case transport delay. */
void forward_guard_receive_vision(ForwardGuard *guard, uint64_t session_id, uint64_t frame_id,
                                  uint64_t now_ms, bool qualified_clear, uint32_t remaining_ms);

/* permitted combines current valid ToF, heartbeat and physical stop status. */
bool forward_guard_start(ForwardGuard *guard, uint64_t session_id, uint64_t command_id,
                         uint64_t now_ms, uint32_t requested_ms, bool permitted);
bool forward_guard_poll(ForwardGuard *guard, uint64_t now_ms, bool permitted);

#endif
