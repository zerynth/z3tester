@echo off
"ztool\sys\python\python.exe" -I "ztool\dist\ztc\ztc.py" device discover --matchdb > tmpFile 
set /p myvar= < tmpFile 
del tmpFile 
echo %myvar%
"ztool\sys\python\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 erase_region 0x350000 0x1000 
"ztool\sys\python\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 "ztool/dist/devices/db_zm1/test/exp-io/bootloader.bin" 0x10000 "ztool/dist/devices/db_zm1/test/exp-io/zerynth.bin" 0x9000 "ztool/dist/devices/db_zm1/test/exp-io/partition-table.bin" 0x310000 "ztool/dist/devices/db_zm1/test/db-zm1/otalog.bin" 0x320000 "ztool/dist/devices/db_zm1/test/db-zm1/firmware.bin"
echo "-------------------------------------"
echo "            TEST EXP-IO              "
echo "-------------------------------------"
echo "Before starting the test:"
echo "  --> Put the S1 Switch in position 111111"
echo "  --> Put the SW1 Rotative Switch in position 1"
echo "  --> Put the SW2 Rotative Switch in position 0"
echo "  --> Attach the EXP-IO Device Under Test (DUT) on the right of the DB-ZM1 in the Z-BUS connector"
echo "  --> Attach the 'TEST EXP-PROTO, IO, DB-ZM1' board on the right of the DUT in the Z-BUS connector"
echo "  --> Connect screw terminal from 'TEST EXP-PROTO, IO, DB-ZM1' to DUT"
echo "  --> Power up the hardware setup with external 24 Vdc through DB-ZM1 screw terminals"
echo "  --> Use USB-C cable to program the board and check messages"
echo "----------------------------------------------------------------------------------"
echo "#####################################################"
echo "###  Press Reset Button to start the EXP-IO Test  ###"
echo "#####################################################"
"ztool\sys\python\python.exe" -I "ztool/dist/ztc/ztc.py" device open_raw %myvar%
