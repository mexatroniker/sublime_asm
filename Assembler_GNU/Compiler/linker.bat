echo off
cls

arm-none-eabi-ld.exe -T "C:\temp\WB55\link.ld" -o "C:\temp\WB55\tmp\project.elf" "C:\temp\WB55\tmp\config.o" "C:\temp\WB55\tmp\interrupt.o" "C:\temp\WB55\tmp\isr.o" "C:\temp\WB55\tmp\main.o" 
