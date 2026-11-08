#ifndef D12_LINE_READER_H
#define D12_LINE_READER_H
#define LINE_READY 1
#define LINE_END 0
#define LINE_TOO_LONG 2
#define LINE_IO_ERROR (-1)
#define LINE_BAD_BUFFER (-2)
/* Teacher adapter reusing the existing D9 read_text/check_tail module.
 * Text input only, without embedded NUL. dest must span capacity writable bytes.
 * On LINE_READY dest is a terminated string without its newline.
 * Only LINE_READY permits the caller to parse dest.
 */
int read_complete_line(char *dest, int capacity);
#endif
