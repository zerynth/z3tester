@echo off
"ztool\sys\python\python.exe" -I "ztool\dist\ztc\ztc.py" device discover --matchdb > tmpFile 
set /p myvar= < tmpFile 
del tmpFile 
echo %myvar%
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 erase_region 0x350000 0x1000 
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 "ztool/dist/devices/db_zm1/test/exp-ser/bootloader.bin" 0x10000 "ztool/dist/devices/db_zm1/test/exp-ser/zerynth.bin" 0x9000 "ztool/dist/devices/db_zm1/test/exp-ser/partition-table.bin" 0x910000 "ztool/dist/devices/db_zm1/test/exp-ser/otalog.bin" 0x210000 "ztool/dist/devices/db_zm1/test/exp-ser/firmware.bin"
echo "-------------------------------------"
echo "              TEST EXP-SER           "
echo "-------------------------------------"
echo "Before starting the test:"
echo "  --> Put the S1 Switch in position 110 of the EXP-SER DUT"
echo "  --> Put the S2 Switch in position 111 of the EXP-SER DUT"
echo "  --> Put the SW1 Rotative Switch in position 0 of the EXP-SER DUT"
echo "  --> Put the S1 Switch in position 010 of the 'TEST EXP-SER'"
echo "  --> Put the S2 Switch in position 010 of the 'TEST EXP-SER'"
echo "  --> Put the SW1 Rotative Switch in position 3 of the 'TEST EXP-SER'"
echo "  --> Attach the TEST-BED board on the right of the DB-ZM1 DUT (Device Under Test) in the Z-BUS connector and connect TEST DB-ZM1+EXP-SER to the TEST-BED"
echo "  --> Attach the EXP-SER Device Under Test (DUT) on the right of the DB-ZM1 in the vertical Z-BUS connector of the TEST-BED"
echo "  --> Connect only the bottom screw terminal (CAN and RS485) from 'TEST EXP-SER' to DUT"
echo "  --> DO NOT CONNECT THE TOP SCREW TERMINAL (RS232) UNTIL THE TEST ASKS FOR IT"
echo " --> Attach the 12Vdc (P1 on 4ZeroBox V10, P1 on DB-ZM1, P1-3/4 on TEST-BED) power supply to the 4ZeroBox V10, DB-ZM1+EXP-SER and TEST-BED board"
echo "  --> Use USB-C cable to program the board and check messages"
echo "----------------------------------------------------------------------------------"
echo "######################################################"
echo "###  Press Reset Button to start the EXP-SER Test  ###"
echo "######################################################"
"ztool\sys\python\python.exe" -I "ztool/dist/ztc/ztc.py" device open_raw %myvar%
