@echo off
"ztool\sys\python\python.exe" -I "ztool\dist\ztc\ztc.py" device discover --matchdb > tmpFile 
set /p myvar= < tmpFile 
del tmpFile 
echo %myvar%
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 erase_region 0x350000 0x1000 
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 "ztool/dist/devices/db_zm1/test/4zerobox-mobile-lite/bootloader.bin" 0x10000 "ztool/dist/devices/db_zm1/test/4zerobox-mobile-lite/zerynth.bin" 0x9000 "ztool/dist/devices/db_zm1/test/4zerobox-mobile-lite/partition-table.bin" 0x910000 "ztool/dist/devices/db_zm1/test/4zerobox-mobile-lite/otalog.bin" 0x210000 "ztool/dist/devices/db_zm1/test/4zerobox-mobile-lite/firmware.bin" 
echo "-----------------------------------------"
echo "         TEST Lite 4ZeroBox Mobile       "
echo "-----------------------------------------"
echo "Before starting the test:"
echo "  --> Insert SD Card in the 4ZeroBox Mobile onboard slot"
echo "  --> Insert the Micro SIM card in the related slot"
echo "  --> Put the S1 Switch in position 111100 of the 4ZeroBox Mobile DUT"
echo "  --> Put the S2 Switch in position 101011 of the 4ZeroBox Mobile DUT"
echo "  --> Put the S3 Switch in position 111111 of the 4ZeroBox Mobile DUT"
echo "  --> Put the S4 Switch in position 111111 of the 4ZeroBox Mobile DUT"
echo "  --> Put the S5 Switch in position 111111 of the 4ZeroBox Mobile DUT"
echo "  --> Power up the hardware setup with external 12 Vdc through available Power Wires (Red + / Black -)"
echo "  --> Use USB-C cable to program the board and check messages in the prompt"
echo "----------------------------------------------------------------------------------"
echo "###################################################################"
echo "###  Press Reset Button to start the 4ZeroBox Mobile Lite Test  ###"
echo "###################################################################"
"ztool\sys\python\python.exe" -I "ztool/dist/ztc/ztc.py" device open_raw %myvar%