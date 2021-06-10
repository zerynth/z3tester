@echo off
"ztool\sys\python\python.exe" -I "ztool\dist\ztc\ztc.py" device discover --matchdb > tmpFile 
set /p myvar= < tmpFile 
del tmpFile 
echo %myvar%
"ztool\sys\python\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 erase_region 0x350000 0x1000 
"ztool\sys\python\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 "ztool/dist/devices/db_zm1/test/exp-connect/bootloader.bin" 0x10000 "ztool/dist/devices/db_zm1/test/exp-connect/zerynth.bin" 0x9000 "ztool/dist/devices/db_zm1/test/exp-connect/partition-table.bin" 0x910000 "ztool/dist/devices/db_zm1/test/exp-connect/otalog.bin" 0x210000 "ztool/dist/devices/db_zm1/test/exp-connect/firmware.bin"
echo "-------------------------------------"
echo "          TEST EXP-CONNECT              "
echo "-------------------------------------"
echo "Before starting the test:"
echo "  --> Put the S1 Switch in position 010"
echo "  --> Put the SW1 Rotative Switch in position 0"
echo "  --> Insert the Micro SIM card in the related slot"
echo "  --> Attach the EXP-CONNECT Device Under Test (DUT) on the right of the DB-ZM1 in the Z-BUS connector"
echo "  --> Connect the GPS/GSM Antennas"
echo "  --> Power up the hardware setup with external 24 Vdc through DB-ZM1 screw terminals"
echo "  --> Use USB-C cable to program the board and check messages"
echo "----------------------------------------------------------------------------------"
echo "##########################################################"
echo "###  Press Reset Button to start the EXP-CONNECT Test  ###"
echo "##########################################################"
"ztool\sys\python\python.exe" -I "ztool/dist/ztc/ztc.py" device open_raw %myvar%