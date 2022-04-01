@echo off
"ztool\sys\python\python.exe" -I "ztool\dist\ztc\ztc.py" device discover --matchdb > tmpFile 
set /p myvar= < tmpFile 
del tmpFile 
echo %myvar%
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 erase_region 0x350000 0x1000 
"ztool\sys\python_new\python.exe" -I "ztool/sys/esptool/esp32/esptool.py" --chip esp32 --port %myvar% --baud 460800 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x1000 "ztool/dist/devices/db_zm1/test/4zerobox-mobile/bootloader.bin" 0x10000 "ztool/dist/devices/db_zm1/test/4zerobox-mobile/zerynth.bin" 0x9000 "ztool/dist/devices/db_zm1/test/4zerobox-mobile/partition-table.bin" 0x910000 "ztool/dist/devices/db_zm1/test/4zerobox-mobile/otalog.bin" 0x210000 "ztool/dist/devices/db_zm1/test/4zerobox-mobile/firmware.bin" 
echo "-------------------------------------"
echo "         TEST 4ZeroBox Mobile        "
echo "-------------------------------------"
echo "Before starting the test:"
echo "  --> Insert SD Card in the 4ZeroBox Mobile onboard slot"
echo "  --> Attach the 'EXP-RELAY TOOL' board on the right of the 4ZeroBox Mobile DUT in the Z-BUS connector"
echo "  --> Attach the 'TEST PROTO-IO-DBZM1' board on the right of the EXP-RELAY TOOL in the Z-BUS connector"
echo "  --> Insert the Micro SIM card in the related slot"
echo "  --> Connect the GPS/GSM Antennas"
echo "  --> Connect pin header soldered inside the fixed screw connector of the DUT from EXP-RELAY TOOL"
echo "  --> Connect the 2 pin screw pluggable connector for powering setup 2 (ZM1-DB + TEST EXP-SER)"
echo "  --> Put the S1 Switch in position 111100 of the 4ZeroBox Mobile DUT"
echo "  --> Put the S2 Switch in position 101011 of the 4ZeroBox Mobile DUT"
echo "  --> Put the S3 Switch in position 111111 of the 4ZeroBox Mobile DUT"
echo "  --> Put the S4 Switch in position 111111 of the 4ZeroBox Mobile DUT"
echo "  --> Put the S5 Switch in position 111111 of the 4ZeroBox Mobile DUT"
echo "  --> Put the S1 Switch in position 010 of the TEST EXP-SER in Setup 2"
echo "  --> Put the S2 Switch in position 010 of the TEST EXP-SER in Setup 2"
echo "  --> Put the SW1 Switch in position 0 of the TEST EXP-SER in Setup 2"
echo "  --> Connect the JST 2 pin connector in the slot on 4ZeroBox Mobile to simulate a Li-Po Battery"
echo "  --> Power up the hardware setup with external 12 Vdc through available Power Wires (Red + / Black -)"
echo "  --> Use USB-C cable to program the board and check messages in the prompt"
echo "----------------------------------------------------------------------------------"
echo "##############################################################"
echo "###  Press Reset Button to start the 4ZeroBox Mobile Test  ###"
echo "##############################################################"
"ztool\sys\python\python.exe" -I "ztool/dist/ztc/ztc.py" device open_raw %myvar%