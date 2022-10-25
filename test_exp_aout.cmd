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
echo "  --> Attach the TEST-BED board on the right of the DB-ZM1 DUT (Device Under Test) in the Z-BUS connector"
echo "  --> Attach the EXP-AOUT Device Under Test (DUT) on the right of the DB-ZM1 in the vertical Z-BUS connector of the TEST-BED"
echo "  --> Connect ANALOG OUTPUTS (voltage/current) screw terminal from TEST-BED to DUT. Please follow the labels on the screw terminal to make the right connections (V1 - V1, I1- I1 and so on)"
echo "  --> Attach the 12Vdc (P1 on DB-ZM1, P1-3/4 on TEST-BED) power supply to the DB-ZM1 and TEST-BED board"
echo "  --> Use USB-C cable to program the board and check messages in the prompt"
echo "----------------------------------------------------------------------------------"
echo "#######################################################"
echo "###  Press Reset Button to start the EXP-AOUT Test  ###"
echo "#######################################################"
"ztool\sys\python\python.exe" -I "ztool/dist/ztc/ztc.py" device open_raw %myvar%
