# RingNes
基于 python 的 NES 模拟器

#### 参考链接
[olcNES](https://github.com/OneLoneCoder/olcNES), 
[NES_DEV](https://www.nesdev.org/wiki/Nesdev_Wiki)，
etc

#### 项目想法
都说 python 开发效率高, 实践周抽空试试搞个nes模拟器，加深一下对计算机底层逻辑的理解。  
感觉调包就没意思了，挑战仅使用 python 内置模块。

#### 引入模块
enum : 试图模仿C/C++结构体  
tkinter : 创建图形界面

#### 程序入口
main.py : 理想入口
display : 画面调式中

#### 代码现状
大部分参考资料为英文 故代码注释直接CV的英文修改  
仅实现 cpu, ppu, bus, carteidge, mapper000 正在调试 ...

问题一: 模拟CPU时, PC会从 0x8ecd 跳到 0x18ecd, 怀疑是移位操作的溢出位没有舍去, 错误保留了高位的"1".  

问题二: 模拟PPU的 Pattern, Name, Palette 失败, 画面不能更新, 而且画面逐点逐行扫描效率太低, 开了16个线程去调总线时钟, 仍然刷新缓慢.  

要复习备考暂时弃坑, 对于用纯 python 实现高效的 int8/uint8, int16/uint16 数据结构 没有头绪
