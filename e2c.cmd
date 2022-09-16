@echo off
"ztool\sys\python\python.exe" -I "ztool\dist\ztc\ztc.py" device discover --matchdb > tmpFile
set /p myvar= < tmpFile
del tmpFile
echo %myvar%
"ztool\sys\python\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 erase_region 0x350000 0x1000
"ztool\sys\python\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 "ztool/dist/devices/db_zm1/test/e2c/bootloader.bin" 0x10000 "ztool/dist/devices/db_zm1/test/e2c/zerynth.bin" 0x9000 "ztool/dist/devices/db_zm1/test/e2c/partition-table.bin" 0x910000 "ztool/dist/devices/db_zm1/test/e2c/otalog.bin" 0x210000 "ztool/dist/devices/db_zm1/test/e2c/firmware.bin"
echo "-------------------------------------"
echo "         TEST E2C        "
echo "-------------------------------------"
echo "Before starting the test:"
echo "  --> Use USB-C cable to program the board and check messages in the prompt"
echo "----------------------------------------------------------------------------------"
echo "##############################################################"
echo "###  Press Reset Button to start the E2C Test  ###"
echo "##############################################################"
"ztool\sys\python\python.exe" -I "ztool/dist/ztc/ztc.py" device open_raw %myvar%

