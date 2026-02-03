echo off
cls

arm-none-eabi-objcopy.exe -O binary "C:\temp\WB55\tmp\project.elf" "C:\temp\WB55\bin\project.bin" 
arm-none-eabi-objcopy.exe -O ihex "C:\temp\WB55\tmp\project.elf" "C:\temp\WB55\bin\project.hex" 
