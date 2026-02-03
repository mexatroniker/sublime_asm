echo off
cls

arm-none-eabi-as.exe -o "C:\temp\WB55\tmp\config.o" "C:\temp\WB55\tmp\config.asm"

arm-none-eabi-as.exe -o "C:\temp\WB55\tmp\interrupt.o" "C:\temp\WB55\tmp\interrupt.asm"

arm-none-eabi-as.exe -o "C:\temp\WB55\tmp\isr.o" "C:\temp\WB55\tmp\isr.asm"

arm-none-eabi-as.exe -o "C:\temp\WB55\tmp\main.o" "C:\temp\WB55\tmp\main.asm"

