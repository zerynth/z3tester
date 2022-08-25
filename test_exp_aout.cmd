@echo off
"ztool\sys\python\python.exe" -I "ztool\dist\ztc\ztc.py" device discover --matchdb > tmpFile 
set /p myvar= < tmpFile 
del tmpFile 
echo %myvar%
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 erase_region 0x350000 0x1000 
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 "ztool/dist/devices/db_zm1/test/exp-aout/bootloader.bin" 0x10000 "ztool/dist/devices/db_zm1/test/exp-aout/zerynth.bin" 0x9000 "ztool/dist/devices/db_zm1/test/exp-aout/partition-table.bin" 0x910000 "ztool/dist/devices/db_zm1/test/exp-aout/otalog.bin" 0x210000 "ztool/dist/devices/db_zm1/test/exp-aout/firmware.bin" 
echo "----------------------------------"
echo "          TEST EXP-AOUT              "
echo "----------------------------------"
echo "Before starting the test:"
echo "  --> Put the ADDR Rotative Switch in position 1"
echo "  --> Attach the EXP-AOUT Device Under Test (DUT) on the right of the DB-ZM1 in the Z-BUS connector"
echo "  --> Use USB-C cable to program the board and check messages"
echo "----------------------------------------------------------------------------------"
echo "#######################################################"
echo "###  Press Reset Button to start the EXP-AOUT Test  ###"
echo "#######################################################"
"ztool\sys\python\python.exe" -I "ztool/dist/ztc/ztc.py" device open_raw %myvar%
