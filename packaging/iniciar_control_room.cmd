@echo off
rem Sobe a Control Room guardando os dados ao lado do instalador (pasta "data").
setlocal
set "RPA_PASTA_DADOS=%~dp0data"
"%~dp0control_room.exe" %*
endlocal
