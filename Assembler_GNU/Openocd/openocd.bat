echo off
cls

bin\openocd.exe -s scripts -f interface/stlink.cfg -f target/stm32wbx.cfg -c "program "C:/temp/WB55/bin/project.bin" 0x08000000 verify reset exit" 