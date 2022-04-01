@echo off
"ztool\sys\python\python.exe" -I "ztool\dist\ztc\ztc.py" device discover --matchdb > tmpFile 
set /p myvar= < tmpFile 
del tmpFile 
echo %myvar%
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 erase_region 0x350000 0x1000 
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 "ztool/dist/devices/db_zm1/test/exp-ain/bootloader.bin" 0x10000 "ztool/dist/devices/db_zm1/test/exp-ain/zerynth.bin" 0x9000 "ztool/dist/devices/db_zm1/test/exp-ain/partition-table.bin" 0x910000 "ztool/dist/devices/db_zm1/test/exp-ain/otalog.bin" 0x210000 "ztool/dist/devices/db_zm1/test/exp-ain/firmware.bin" 
echo "----------------------------------"
echo "          TEST EXP-AIN              "
echo "----------------------------------"
echo "Before starting the test:"
echo "  --> Put the S1,S2,S3,S4 Switch in position 111111"
echo "  --> Put the ADDR Rotative Switch in position 1"
echo "  --> Put the INT Rotative Switch in position 0"
echo "  --> Attach the EXP-AIN Device Under Test (DUT) on the right of the DB-ZM1 in the Z-BUS connector"
echo "  --> Attach the 'EXP-RELAY TOOL' + 'TEST PROTO-IO-DBZM1' on the DUT in the Z-BUS connector"
echo "  --> Connect screw terminal from 'EXP-RELAY TOOL' to DUT"
echo "  --> Use USB-C cable to program the board and check messages"
echo "----------------------------------------------------------------------------------"
echo "######################################################"
echo "###  Press Reset Button to start the EXP-AIN Test  ###"
echo "######################################################"
"ztool\sys\python\python.exe" -I "ztool/dist/ztc/ztc.py" device open_raw %myvar%