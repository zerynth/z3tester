@echo off
"ztool\sys\python\python.exe" -I "ztool\dist\ztc\ztc.py" device discover --matchdb > tmpFile 
set /p myvar= < tmpFile 
del tmpFile 
echo %myvar%
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 erase_region 0x350000 0x1000 
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 "ztool/dist/devices/db_zm1/test/exp-io/bootloader.bin" 0x10000 "ztool/dist/devices/db_zm1/test/exp-io/zerynth.bin" 0x9000 "ztool/dist/devices/db_zm1/test/exp-io/partition-table.bin" 0x910000 "ztool/dist/devices/db_zm1/test/exp-io/otalog.bin" 0x210000 "ztool/dist/devices/db_zm1/test/exp-io/firmware.bin"
echo "-------------------------------------"
echo "            TEST EXP-IO              "
echo "-------------------------------------"
echo "Before starting the test:"
echo "  --> Put the S1 Switch in position 000000"
echo "  --> Put the SW1 Rotative Switch in position 1"
echo "  --> Put the SW2 Rotative Switch in position 0"
echo "  --> Attach the TEST-BED board on the right of the DB-ZM1 in the Z-BUS connector"
echo "  --> Attach the EXP-IO Device Under Test (DUT) on the right of the DB-ZM1 in the vertical Z-BUS connector of the TEST-BED"
echo "  --> Connect DIGITAL INPUTS screw terminal from TEST-BED to DUT"
echo "  --> Connect ANALOG INPUTS screw terminal from TEST-BED to DUT"
echo "  --> Connect DIGITAL OUTPUTS screw terminal from TEST-BED to DUT"
echo "  --> Attach the 12Vdc (P1 on DB-ZM1, P1-3/4 on TEST-BED) power supply to the DB-ZM1 and TEST-BED board"
echo "  --> Use USB-C cable to program the board and check messages in the prompt"
echo "----------------------------------------------------------------------------------"
echo "#####################################################"
echo "###  Press Reset Button to start the EXP-IO Test  ###"
echo "#####################################################"
"ztool\sys\python\python.exe" -I "ztool/dist/ztc/ztc.py" device open_raw %myvar%
