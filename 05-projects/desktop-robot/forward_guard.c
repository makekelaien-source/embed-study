#include "forward_guard.h"

void forward_guard_reset(ForwardGuard *guard)
{
    *guard = (ForwardGuard){0};
}

static bool advance_clock(ForwardGuard *guard, uint64_t now_ms)
{
    if (now_ms < guard->observed_ms) {
        guard->vision_remaining_ms = 0;
        guard->drive_duration_ms = 0;
        return false;
    }

    guard->observed_ms = now_ms;
    if (now_ms - guard->vision_received_ms >= guard->vision_remaining_ms) {
        guard->vision_remaining_ms = 0;
    }
    if (guard->vision_remaining_ms == 0 || now_ms - guard->drive_started_ms >= guard->drive_duration_ms) {
        guard->drive_duration_ms = 0;
    }
    return true;
}

bool forward_guard_begin_session(ForwardGuard *guard, uint64_t session_id, uint64_t now_ms)
{
    if (!advance_clock(guard, now_ms) || session_id <= guard->session_id) {
        return false;
    }
    *guard = (ForwardGuard){.session_id = session_id, .observed_ms = now_ms};
    return true;
}

void forward_guard_receive_vision(ForwardGuard *guard, uint64_t session_id, uint64_t frame_id,
                                  uint64_t now_ms, bool qualified_clear, uint32_t remaining_ms)
{
    if (!advance_clock(guard, now_ms) || session_id == 0 || session_id != guard->session_id ||
        frame_id <= guard->frame_id) {
        return;
    }
    guard->frame_id = frame_id;
    if (!qualified_clear || remaining_ms == 0 || remaining_ms > FORWARD_GUARD_MAX_LEASE_MS) {
        guard->vision_remaining_ms = 0;
        guard->drive_duration_ms = 0;
        return;
    }
    guard->vision_received_ms = now_ms;
    guard->vision_remaining_ms = remaining_ms;
}

bool forward_guard_start(ForwardGuard *guard, uint64_t session_id, uint64_t command_id,
                         uint64_t now_ms, uint32_t requested_ms, bool permitted)
{
    bool driving = forward_guard_poll(guard, now_ms, permitted);
    if (session_id == 0 || session_id != guard->session_id || command_id <= guard->command_id) {
        return false;
    }

    guard->command_id = command_id;
    if (driving || !permitted || requested_ms == 0 || guard->vision_remaining_ms == 0) {
        return false;
    }
    guard->drive_started_ms = now_ms;
    guard->drive_duration_ms = requested_ms > FORWARD_GUARD_MAX_MOVE_MS ? FORWARD_GUARD_MAX_MOVE_MS : requested_ms;
    return true;
}

bool forward_guard_poll(ForwardGuard *guard, uint64_t now_ms, bool permitted)
{
    if (!advance_clock(guard, now_ms) || !permitted) {
        guard->drive_duration_ms = 0;
    }
    return guard->drive_duration_ms != 0;
}
