@echo off
"ztool\sys\python\python.exe" -I "ztool\dist\ztc\ztc.py" device discover --matchdb > tmpFile 
set /p myvar= < tmpFile 
del tmpFile 
echo %myvar%
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 erase_region 0x350000 0x1000 
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 "ztool/dist/devices/db_zm1/test/db-zm1/bootloader.bin" 0x10000 "ztool/dist/devices/db_zm1/test/db-zm1/zerynth.bin" 0x9000 "ztool/dist/devices/db_zm1/test/db-zm1/partition-table.bin" 0x910000 "ztool/dist/devices/db_zm1/test/db-zm1/otalog.bin" 0x210000 "ztool/dist/devices/db_zm1/test/db-zm1/firmware.bin" 
echo "-------------------------------------"
echo "            TEST DB-ZM1              "
echo "-------------------------------------"
echo "Before starting the test:"
echo "  --> Insert SD Card in the related onboard slot"
echo "  --> Connect Ethernet cable from onboard connector to standard Modem/Router"
echo "  --> Attach the TEST-BED board on the right of the DB-ZM1 in the Z-BUS connector"
echo "  --> Attach the 12Vdc (P1 on DB-ZM1, P1-3/4 on TEST-BED) power supply to the DB-ZM1 and TEST-BED board"
echo "  --> Use USB-C cable to program the board and check messages"
echo "  --> PLEASE check the ethernet connector leds if they works during eth connection"
echo "----------------------------------------------------------------------------------"
echo "#####################################################"
echo "###  Press Reset Button to start the DB-ZM1 Test  ###"
echo "#####################################################"
"ztool\sys\python\python.exe" -I "ztool/dist/ztc/ztc.py" device open_raw %myvar%
