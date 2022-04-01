@echo off
"ztool\sys\python\python.exe" -I "ztool\dist\ztc\ztc.py" device discover --matchdb > tmpFile 
set /p myvar= < tmpFile 
del tmpFile 
echo %myvar%
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 erase_region 0x350000 0x1000 
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 "ztool/dist/devices/db_zm1/test/4zerobox-v9/bootloader.bin" 0x10000 "ztool/dist/devices/db_zm1/test/4zerobox-v9/zerynth.bin" 0x9000 "ztool/dist/devices/db_zm1/test/4zerobox-v9/partition-table.bin" 0x910000 "ztool/dist/devices/db_zm1/test/4zerobox-v9/otalog.bin" 0x210000 "ztool/dist/devices/db_zm1/test/4zerobox-v9/firmware.bin" 
echo "-----------------------------------"
echo "         TEST 4ZeroBox v9.9        "
echo "-----------------------------------"
echo "Before starting the test:"
echo "  --> Insert SD Card in the 4ZeroBox v9.9 onboard slot"
echo "  --> Connect the 2 pin screw pluggable connector for powering setup 2 (ZM1-DB + TEST EXP-SER)"
echo "  --> Put the SW1 Switch in position 000000111100 of the 4ZeroBox DUT"
echo "  --> Put the SW2 Switch in position 010101010010 of the 4ZeroBox DUT"
echo "  --> Connect Ethernet cable from onboard connector to standard Modem/Router"
echo "  --> Attach the green pluggable connector following the naming written in the connectors"
echo "  --> Put the S1 Switch in position 010 of the TEST EXP-SER in Setup 2"
echo "  --> Put the S2 Switch in position 010 of the TEST EXP-SER in Setup 2"
echo "  --> Put the SW1 Switch in position 0 of the TEST EXP-SER in Setup 2"
echo "  --> Power up the hardware setup with external 24 Vdc through available Power Wires (Red + / Black -)"
echo "  --> Use USB-B cable to program the board and check messages in the prompt"
echo "----------------------------------------------------------------------------------"
echo "############################################################"
echo "###  Press Reset Button to start the 4ZeroBox v9.9 Test  ###"
echo "############################################################"

"ztool\sys\python\python.exe" -I "ztool/dist/ztc/ztc.py" device open_raw %myvar%