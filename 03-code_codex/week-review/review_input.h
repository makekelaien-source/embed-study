#ifndef REVIEW_INPUT_H
#define REVIEW_INPUT_H

/* read_text return values. */
#define READ_TEXT_BAD_CAPACITY (-1)
#define READ_TEXT_NO_DATA 0
#define READ_TEXT_COMPLETE 1
#define READ_TEXT_NEEDS_TAIL 2
int read_text(char *dest, int capacity);

/* check_tail return values. Call after READ_TEXT_NEEDS_TAIL. */
#define CHECK_TAIL_NO_CHAR 0       /* The first read got EOF. */
#define CHECK_TAIL_NEWLINE 1       /* The first read took the newline. */
#define CHECK_TAIL_EXTRA_TEXT 2    /* Extra text was drained to newline or EOF. */
int check_tail(void);
/* read_command: -1 bad capacity, 0 no data, 1 complete line,
 * 2 overlong line drained, 3 text read but line ending unconfirmed. */
int read_command(char *dest, int capacity);

#endif
