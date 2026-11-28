#ifndef D22_SUBMIT_COMMAND_H
#define D22_SUBMIT_COMMAND_H

#include "../shared-command/d12-command-kind.h"
#include "../D21-queue-device/D19-ring-queue.h"
#include "../D21-queue-device/D20-device-state.h"

enum SubmitResult { SUBMIT_OK, SUBMIT_INVALID, SUBMIT_FULL };
enum SubmitResult submit_command(struct IntQueue *q, const char *text);

#endif
