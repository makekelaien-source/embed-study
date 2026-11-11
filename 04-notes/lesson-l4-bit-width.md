# L4 位宽与位操作：位宽首讲

2026-11-11同日继续，原计划static后接位宽/位操作。前置仅整数和按位权求和；不假定已掌握位运算。

bit取0或1；位宽是表示一个值所用二进制位数。按位权从右往左1/2/4/8/16/32/64/128，13对应8+4+1，即00001101。无符号N位范围0至2^N-1；4位0至15，8位0至255。本机CHAR_BIT=8，UCHAR_MAX=255，经教师严格C11程序实测。unsigned char是整数类型，可保存数值，不限文本字符；同一个类型char的默认有无符号属性不可假定。sizeof计字节不直接计位，signed范围后续单独讲，不将无符号公式推广到signed。二进制位图是表示方式，标准C11不使用0b前缀演示源码；示例unsigned char flags=13，位图仅讲解。

教师环境核验：

```c
#include <stdio.h>
#include <limits.h>
int main(void) {
    printf("CHAR_BIT=%d UCHAR_MAX=%u\n", CHAR_BIT, (unsigned int)UCHAR_MAX);
    unsigned char flags = 13;
    printf("flags=%u\n", (unsigned int)flags);
    return 0;
}
```

教师编译0诊断、退出0，CHAR_BIT=8 UCHAR_MAX=255，flags=13。示例中的limits.h/CHAR_BIT/UCHAR_MAX及强制转换仅作教师环境检测，不作学生必写新语法。

首讲预测：00010010为多少？待答。之后才教按位与/或及掩码，逐一给规则和例子。

## 按位与首讲

学生独立答00010010为16+2=18正确。按位与a & b逐位计算：仅1&1为1，其余为0，输出整数，不修改两个操作数。掩码为用于筛选特定位的数值；flags13(00001101)&4(00000100)=4，&2=0。位号从右0起，4筛选第2位。括号(flag & mask) != 0检测被选中位至少一个为1；本例单比特掩码检测一位。区别一元&取地址、二元&按位与；&&为逻辑与，不可替代。按位与不短路，两个操作数均求值；本讲示例仅无副作用整数。教师unsigned int示例严格编译0诊断退出0，输出4 0。预测flags18对mask16和mask4，学生待答。

## 按位或首讲

二元a|b逐位只要任一为1结果为1，00为0；不短路。flags18位图00010010，mask4位图00000100，结果00010110即22。flags=flags|4设第2位，保留其他位；重复设同一位仍22，不等同加4。flags|4仅计算，须赋值写回。flags|=4在普通变量场景等价于flags=flags|4，是复合赋值写法；||为逻辑或不替代。教师两次设置输出22/22严格编译验证通过。预测flags18先|16再|4，待学生回答。

## 清位：按位取反配合按位与

unsigned int mask=4，~mask逐位取反，目标第2位变0，其余位全1；flags & ~mask保留其他位、强制第2位0，flags &= ~mask写回。位图只展示低8位，不能误称unsigned int的~4只有8位或数值251。~不是逻辑非!；不是原地修改变量。flags22清第2位为18，再清仍18，不等同减4。教师示例：

```c
#include <stdio.h>
int main(void) {
 unsigned int flags=22;
 unsigned int mask=4;
 flags=flags & ~mask;
 printf("%u\n",flags);
 flags &= ~mask;
 printf("%u\n",flags);
 return 0;
}
```

严格编译0诊断、运行退出0、输出18/18。预测flags18清mask4，待答。

## 按位异或首讲

^逐位不同为1、相同为0，掩码1位翻转，0位保持；flags^=mask等价普通变量flags=flags^mask。不是乘方，不等同逻辑运算，不自动控制硬件。7^2=5，再^2=7，教师严格C11含-Werror编译0诊断退出0验证。预测flags5、mask4连翻两次，待答。

## 移位首讲

<<左移、>>右移；本单元仅unsigned int操作数。a<<n向左移动n位、低位补0、超出类型位宽的高位丢弃；无丢弃时对应乘2^n。a>>n向右移动n位、低位丢弃、高位补0，对应无符号整数除2^n舍去余数。表达式本身不修改a，赋值才写回。位移次数必须非负且小于提升后左操作数位宽，本机unsigned int32位，允许0至31；其他平台不能假定均32。后续题限制位号0至2。整数常量1u表示unsigned int的1，用1u<<bit生成选中第bit位的掩码，位号从0起。5<<1=10，5>>1=2，1u<<3=8，原value仍5，教师严格C11编译运行验证。

```c
#include <stdio.h>
#include <limits.h>
int main(void) {
 unsigned int value=5;
 unsigned int left=value<<1;
 unsigned int right=value>>1;
 unsigned int mask=1u<<3;
 printf("value=%u left=%u right=%u mask=%u bits=%zu\n",value,left,right,mask,sizeof(unsigned int)*CHAR_BIT);
 return 0;
}
```

教师实测value=5 left=10 right=2 mask=8 bits=32。短预测1u<<4及18u>>1，学生待答。
