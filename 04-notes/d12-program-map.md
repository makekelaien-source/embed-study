# D12现有程序梳理与两项局部验证

## 本次范围

不加函数、不重写核心。只梳理输入消费、输出缓冲与两个整数状态，随后做两项短验证。一题一等，不用全部展开调用链。

## 主入口只使用两个工具

1. read_complete_line(text,capacity)：真正读取并消费stdin，写入text，返回读取状态a。只有LINE_READY允许本题解析text。其他状态不使用text当新行。
2. bounded_command_kind(text,capacity)：检查已在内存的缓冲并分类，不读stdin，不修改输入，返回业务类别b。

读取状态a：1=READY，0=END，2=TOO_LONG，-1=IO_ERROR，-2=BAD_BUFFER。
命令类别b：-4=无有效结束字符串，-1=缺斜杠，-3=标签错误，-2=命令为空，0=未知非空，1=RUN，2=STOP。
两者各属于自己的函数，数字相同不代表含义相同。main返回0/1又是进程退出状态，不是把分类类别自动当退出。

## 两份输出

read_complete_line的int返回值进入a；读取的字符通过dest参数写入main的text数组。dest复制了text首元素地址，二者指向同一数组；并非在函数内复制了一整份独立数组。

## 每轮顺序

读一次→看a→仅READY才分类得到b并打印→下一轮。TOO_LONG已清理本行，打印后下一轮；END退出；错误打印后退出。
continue回到while条件，再进入循环体顶部读取；return结束整个main。打印不消费stdin，也不自动清空text。

## 第一个短验证（待作答）

输入CMD/JUMP并换行。看当前main，预测第一轮a、b以及是否因为b为0退出。此处只按已有契约应用，不要求展开内部全部代码。

## 第二个短验证（第一题后再呈现）

16正文超长行后接CMD/STOP并关闭输入，预测读取状态/分类是否执行/输出，验证一个输入拥有者与不同状态命名空间。先不展示答案。

## 实际实现附录

下方逐文件摘自当前保存稿，供回看，不是要求一次背下全部函数。原始源不改。分类用例已有严格验证回执；这次短验证的学生预测尚未验。


### 03-code_codex/d12-command-console.c

SHA-256: 6444b7e3f0813020b44da5b2a9d22bb0203f8c4779af616704aca8be0bf90ced

```c
#include <stdio.h>
#include "d12-line-reader.h"
#include "d12-bounded-command.h"

int main(void){
    char text[16];
    int capacity = sizeof text ;
    while (1)
    {
        int a = read_complete_line(text, capacity);
        if (a == LINE_READY)
        {
            int b = bounded_command_kind(text,capacity);
            printf ("%d\n",b);
            continue;
        }else if (a == LINE_END)
        {
            return 0;
        }else if (a == LINE_TOO_LONG)
        {
            puts("TOO_LONG");
            continue;
        }else if (a == LINE_IO_ERROR)
        {
            puts ("READ_ERROR");
            return 1;
        }else if (a == LINE_BAD_BUFFER)
        {
            puts ("BUFFER_ERROR");
            return 1;
        }    
    }
    return 0;
}
```


### 03-code_codex/d12-line-reader.h

SHA-256: 138b7f5707c5a9a8ebc225a070e6aa91bf03c5d2c04485350e840e0d035d3b94

```c
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
```


### 03-code_codex/d12-line-reader.c

SHA-256: f97cb394c41fa019633830698b725cad37cd86fe864d448cf12d85fe7ede28d3

```c
/* Teacher integration adapter; student does not rewrite input parsing. */
#include <stdio.h>
#include <stddef.h>
#include "week-review/review_input.h"
#include "d12-line-reader.h"
int read_complete_line(char *dest, int capacity)
{
    if (dest == NULL || capacity < 2) return LINE_BAD_BUFFER;
    int status=read_text(dest,capacity);
    if (ferror(stdin)) return LINE_IO_ERROR;
    if (status == READ_TEXT_NO_DATA) return LINE_END;
    if (status == READ_TEXT_BAD_CAPACITY) return LINE_BAD_BUFFER;
    if (status == READ_TEXT_COMPLETE) return LINE_READY;
    int tail=check_tail();
    if (ferror(stdin)) return LINE_IO_ERROR;
    if (tail == CHECK_TAIL_EXTRA_TEXT) return LINE_TOO_LONG;
    return LINE_READY;
}
```


### 03-code_codex/week-review/review_input.h

SHA-256: 684ea21f3c1e09cacaef94206f27db817044f8250ccb6e42defc26015a1bb3ab

```c
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
```


### 03-code_codex/week-review/review_input.c

SHA-256: 55f668c53d606ef7b63810a075b9e9faee480fac8477d2e6703ae994dcf3e736

```c
#include <stdio.h>
#include "review_input.h"

/* Teacher copy of your D9 read_text and check_tail. */
int read_text(char *dest, int capacity){
    if (capacity < 2)
    {
        return -1 ; /*容量小于2*/
    }
    if (fgets(dest,capacity,stdin) == NULL)
    {
        return 0 ; /*什么都没有返回0*/
    }
    for (int i = 0; i < capacity; i++)
    {
        if (dest[i] == '\n')
        {
            dest[i] = '\0';
            return 1 ; /*取到换行，令换行=0结束*/
        }
        else if (dest[i] == '\0')
    {
        return 2 ;  /*取到结束*/
    }
    
    }
    return 2 ;  
}

int check_tail(void){
    int a = fgetc(stdin);
    if (a == '\n')
    {
        return 1 ;  /*代表取到回车换行，再次进行read_text取新的*/
    }else if (a == EOF)
    {
        return 0 ; /*读取到错误*/
    }else {
        while (a != '\n' && a != EOF)
        {
            a = fgetc(stdin); /*读正常文本，一直读到出现前两种情况*/
        }
        
    }return 2 ;
}
```


### 03-code_codex/d12-bounded-command.c

SHA-256: f44c3bc9a8f584fae5f24a7a4467a31f04cbfecd2898fc8525106e5b9dd4d3ce

```c
#include <stddef.h>
#include "shared-text/d11-token-prefix.h"
#include "d12-strict-command.h"

int bounded_command_kind(const char *text, int capacity){
    if (text == NULL || capacity < 0 || capacity == token_prefix_length(text,capacity,'\0'))
    {
        return -4 ;
    }else return strict_command_kind(text,capacity);   
}
```


### 03-code_codex/d12-strict-command.c

SHA-256: d65fabe3648f5373e4c923cb4d77c80bfba01aaf175574383eef177f079ea10f

```c
#include <string.h>
#include "d12-tagged-command.h" /*a为NULL 返回-1 a==0 返回-2 RUN 1 STOP2*/

int strict_command_kind(const char *text, int capacity){
    if (text == NULL)
    {
        return -1;
    }else{
        int ch = tagged_command_kind(text,capacity);

        if (ch == -1){
            return -1 ; /*-1 没有分隔符*/
        }else {
            if (strncmp(text,"CMD/",4) != 0)
            {
                return -3 ; /*-3 缺标签*/
            }else {
                return ch;
            }
            
    }}
}
```


### 03-code_codex/d12-tagged-command.c

SHA-256: d7c56975c64d6eb1c7caaa9a68b370a4ade3712bb4230b9397704bd797614e0b

```c
#include <stdio.h>
#include "shared-text/d11-after-delimiter.h" /*capacity = 0 delimiter = '\0' text[a]= 0 返回NULL*/
#include "d12-command-kind.h"                /*其他时候返回分隔符后面的字符地址*/
                                             /*NULL 返回-1 RUN 1 STOP2 其他0*/
int tagged_command_kind(const char *text, int capacity){
    const char *a = after_delimiter(text,capacity,'/');
    if (a == NULL)
    {
        return -1 ;
    }else if (a[0] != '\0')
    {
        return command_kind(a);  
    }else return -2;     
}


/* 已有接口：
const char *after_delimiter(const char *text, int capacity, char delimiter);
int command_kind(const char *command);
*/
```


### 03-code_codex/d12-command-kind.c

SHA-256: 7c42c19ca220c9dd1831f01f3e3ee3b25027b96cfbe68f14b5086fccb619c780

```c
#include <string.h>

int command_kind(const char *command){
    if (command == NULL)
    {
        return -1;
    }
    else if (strcmp(command,"STOP") == 0){
        return 2;
    }
    else if (strcmp(command,"RUN") == 0)
    {
        return 1;
    }else return 0;
}
```


### 03-code_codex/shared-text/d11-after-delimiter.c

SHA-256: 5f47f451675242cad87d6e6eefa3b06957ef8f610ac65579180c4c8fab6c6ea7

```c
#include <stdio.h>
#include "d11-after-delimiter.h"
#include "d11-token-prefix.h"

const char *after_delimiter(const char *text, int capacity, char delimiter){
    int a = token_prefix_length(text,capacity,delimiter); /*在delimiter\结束符之前的文本量*/
    if (capacity == 0 || delimiter == '\0' || text [a] == '\0'){
        return NULL;}
    else{ 
    return text + a + 1 ;}
}
```


### 03-code_codex/shared-text/d11-token-prefix.c

SHA-256: 9241aeba3587243eb28d71d8c7b51f4906a7a1f69d1e25e65d2b89403f2653f3

```c
#include "d11-token-prefix.h"
#include "d11-after-delimiter.h"
#include <stddef.h>
#include <stdio.h>

int token_prefix_length(const char *text, int capacity, char delimiter){
    {
    int a = 0;
    for (int i = 0; i < capacity; i++)
    {
        if (text == NULL || text [i] == delimiter || text[i] == '\0')
        {
            return a;
        }else a ++;
    }
    return a ;
    }
}
```
