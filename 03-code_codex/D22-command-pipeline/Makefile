CFLAGS = -std=c11 -Wall -Wextra -Werror -pedantic
QUEUE = ../D21-queue-device
PARSER = ../shared-command
SOURCES = test-submit.c submit-command.c $(QUEUE)/D19-ring-queue.c $(PARSER)/d12-command-kind.c
HEADERS = submit-command.h $(QUEUE)/D19-ring-queue.h $(QUEUE)/D20-device-state.h $(PARSER)/d12-command-kind.h

submit-check.exe: $(SOURCES) $(HEADERS)
	gcc $(CFLAGS) $(SOURCES) -o $@

PIPELINE_SOURCES = test-pipeline.c submit-command.c $(QUEUE)/consume-all.c $(QUEUE)/D20-device-step.c $(QUEUE)/D19-ring-queue.c $(PARSER)/d12-command-kind.c

pipeline-check.exe: $(PIPELINE_SOURCES) $(HEADERS) $(QUEUE)/queue-device-all.h
	gcc $(CFLAGS) -I$(QUEUE) $(PIPELINE_SOURCES) -o $@
