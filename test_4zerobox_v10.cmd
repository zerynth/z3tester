@echo off
"ztool\sys\python\python.exe" -I "ztool\dist\ztc\ztc.py" device discover --matchdb > tmpFile 
set /p myvar= < tmpFile 
del tmpFile 
echo %myvar%
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 erase_region 0x350000 0x1000 
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 "ztool/dist/devices/db_zm1/test/v10/bootloader.bin" 0x10000 "ztool/dist/devices/db_zm1/test/v10/zerynth.bin" 0x9000 "ztool/dist/devices/db_zm1/test/v10/partition-table.bin" 0x910000 "ztool/dist/devices/db_zm1/test/v10/otalog.bin" 0x210000 "ztool/dist/devices/db_zm1/test/v10/firmware.bin" 0x920000 "ztool/dist/devices/db_zm1/test/v10/lfs.bin"
echo "------------------------------------------"
echo "            TEST 4ZeroBoxV10              "
echo "------------------------------------------"
echo "Before starting the test:"
echo " --> Attach the TEST-BED board on the right of the 4ZeroBox V10 in the Z-BUS connector"
echo " --> Connect ALL screw terminals from TEST-BED to DUT following the tables above"
echo " --> Attach the 12Vdc (P1 on 4ZeroBox V10, P1 on DB-ZM1, P1-3/4 on TEST-BED) power supply to the 4ZeroBox V10, DB-ZM1+EXP-SER and TEST-BED board"
echo " --> Attach ETH Cable to LAN1 of the 4ZeroBox V10"
echo " --> Insert SD Card to the slot on the 4ZeroBox V10"
echo " --> Use USB-C cable to program the board and check messages in the prompt"
echo "----------------------------------------------------------------------------------"
echo "#####################################################"
echo "###  Press Reset Button to start the 4ZeroBoxV10  ###"
echo "#####################################################"
"ztool\sys\python\python.exe" -I "ztool/dist/ztc/ztc.py" device open_raw %myvar%
