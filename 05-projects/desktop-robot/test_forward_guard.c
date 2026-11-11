#include "forward_guard.h"

#include <stdio.h>
#include <stdlib.h>

static unsigned failures;

#define CHECK(condition)                                                        \
    do {                                                                        \
        if (!(condition)) {                                                     \
            fprintf(stderr, "%s:%d: %s\n", __func__, __LINE__, #condition);      \
            ++failures;                                                         \
        }                                                                       \
    } while (0)

static ForwardGuard new_session(void)
{
    ForwardGuard guard;
    forward_guard_reset(&guard);
    CHECK(forward_guard_begin_session(&guard, 41, 1000));
    return guard;
}

static void denied_command_cannot_resume_or_be_replayed(void)
{
    ForwardGuard guard = new_session();
    CHECK(!forward_guard_start(&guard, 41, 1, 1010, 100, true));
    forward_guard_receive_vision(&guard, 41, 1, 1011, true, 100);
    CHECK(!forward_guard_poll(&guard, 1011, true));
    CHECK(!forward_guard_start(&guard, 41, 1, 1012, 100, true));
    CHECK(forward_guard_start(&guard, 41, 2, 1012, 100, true));
    CHECK(forward_guard_poll(&guard, 1013, true));
}

static void duplicate_vision_and_healthy_heartbeat_cannot_extend_lease(void)
{
    ForwardGuard guard = new_session();
    forward_guard_receive_vision(&guard, 41, 2, 1010, true, 80);
    CHECK(forward_guard_start(&guard, 41, 1, 1020, 300, true));
    forward_guard_receive_vision(&guard, 41, 2, 1088, true, 200);
    forward_guard_receive_vision(&guard, 41, 1, 1089, true, 200);
    CHECK(forward_guard_poll(&guard, 1089, true));
    CHECK(!forward_guard_poll(&guard, 1090, true));
    forward_guard_receive_vision(&guard, 41, 3, 1091, true, 200);
    CHECK(!forward_guard_poll(&guard, 1091, true));
}

static void clear_arriving_after_expiry_does_not_continue_old_motion(void)
{
    ForwardGuard guard = new_session();
    forward_guard_receive_vision(&guard, 41, 1, 1010, true, 30);
    CHECK(forward_guard_start(&guard, 41, 1, 1011, 300, true));
    forward_guard_receive_vision(&guard, 41, 2, 1040, true, 150);
    CHECK(!forward_guard_poll(&guard, 1040, true));
    CHECK(forward_guard_start(&guard, 41, 2, 1041, 100, true));
}

static void vision_deny_and_local_gate_drop_cancel_motion(void)
{
    ForwardGuard guard = new_session();
    forward_guard_receive_vision(&guard, 41, 1, 1010, true, 100);
    CHECK(forward_guard_start(&guard, 41, 1, 1011, 100, true));
    forward_guard_receive_vision(&guard, 41, 2, 1012, false, 100);
    CHECK(!forward_guard_poll(&guard, 1012, true));
    forward_guard_receive_vision(&guard, 41, 3, 1013, true, 100);
    CHECK(forward_guard_start(&guard, 41, 2, 1014, 100, true));
    CHECK(!forward_guard_poll(&guard, 1015, false));
    CHECK(!forward_guard_poll(&guard, 1016, true));
    CHECK(!forward_guard_start(&guard, 41, 3, 1016, 100, false));
    CHECK(!forward_guard_start(&guard, 41, 3, 1016, 100, true));
}

static void old_session_messages_cannot_rearm_after_reconnect(void)
{
    ForwardGuard guard = new_session();
    forward_guard_receive_vision(&guard, 41, 1, 1010, true, 100);
    CHECK(forward_guard_start(&guard, 41, 1, 1011, 100, true));
    CHECK(forward_guard_begin_session(&guard, 42, 1012));
    CHECK(!forward_guard_begin_session(&guard, 41, 1012));
    CHECK(!forward_guard_begin_session(&guard, 42, 1012));
    forward_guard_receive_vision(&guard, 41, 99, 1013, true, 100);
    CHECK(!forward_guard_poll(&guard, 1013, true));
    CHECK(!forward_guard_start(&guard, 42, 1, 1013, 100, true));
    forward_guard_receive_vision(&guard, 42, 1, 1014, true, 100);
    CHECK(!forward_guard_start(&guard, 41, 100, 1014, 100, true));
    CHECK(forward_guard_start(&guard, 42, 2, 1014, 100, true));
}

static void command_duration_is_capped_and_active_command_is_never_extended(void)
{
    ForwardGuard guard = new_session();
    forward_guard_receive_vision(&guard, 41, 1, 1010, true, 200);
    CHECK(forward_guard_start(&guard, 41, 1, 1020, UINT32_MAX, true));
    forward_guard_receive_vision(&guard, 41, 2, 1200, true, 200);
    CHECK(!forward_guard_start(&guard, 41, 2, 1201, 300, true));
    CHECK(forward_guard_poll(&guard, 1319, true));
    CHECK(!forward_guard_poll(&guard, 1320, true));
    CHECK(!forward_guard_start(&guard, 41, 2, 1320, 100, true));
    CHECK(forward_guard_start(&guard, 41, 3, 1320, 100, true));
}

static void out_of_range_lease_revokes_and_zero_duration_is_denied(void)
{
    ForwardGuard guard = new_session();
    forward_guard_receive_vision(&guard, 41, 1, 1010, true, 100);
    CHECK(!forward_guard_start(&guard, 41, 1, 1011, 0, true));
    CHECK(!forward_guard_start(&guard, 41, 1, 1011, 100, true));
    CHECK(forward_guard_start(&guard, 41, 2, 1011, 100, true));
    forward_guard_receive_vision(&guard, 41, 2, 1012, true, 201);
    CHECK(!forward_guard_poll(&guard, 1012, true));
    forward_guard_receive_vision(&guard, 41, 3, 1013, true, 100);
    CHECK(forward_guard_start(&guard, 41, 3, 1014, 100, true));
    forward_guard_receive_vision(&guard, 41, 4, 1015, true, 0);
    CHECK(!forward_guard_poll(&guard, 1015, true));
}

static void clock_regression_and_wrap_fail_closed(void)
{
    ForwardGuard guard;
    forward_guard_reset(&guard);
    CHECK(!forward_guard_begin_session(&guard, 0, 0));
    CHECK(forward_guard_begin_session(&guard, 1, UINT64_MAX - 5));
    forward_guard_receive_vision(&guard, 1, 1, UINT64_MAX - 4, true, 200);
    CHECK(forward_guard_start(&guard, 1, 1, UINT64_MAX - 3, 300, true));
    CHECK(forward_guard_poll(&guard, UINT64_MAX, true));
    CHECK(!forward_guard_poll(&guard, 0, true));
    CHECK(!forward_guard_poll(&guard, UINT64_MAX, true));
    CHECK(!forward_guard_start(&guard, 1, 2, UINT64_MAX, 10, true));
}

int main(void)
{
    denied_command_cannot_resume_or_be_replayed();
    duplicate_vision_and_healthy_heartbeat_cannot_extend_lease();
    clear_arriving_after_expiry_does_not_continue_old_motion();
    vision_deny_and_local_gate_drop_cancel_motion();
    old_session_messages_cannot_rearm_after_reconnect();
    command_duration_is_capped_and_active_command_is_never_extended();
    out_of_range_lease_revokes_and_zero_duration_is_denied();
    clock_regression_and_wrap_fail_closed();
    if (failures != 0) {
        fprintf(stderr, "%u forward guard checks failed\n", failures);
        return EXIT_FAILURE;
    }
    puts("8 forward guard scenarios passed");
    return EXIT_SUCCESS;
}
