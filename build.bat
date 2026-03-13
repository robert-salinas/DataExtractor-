@echo off 
echo Construyendo RS DataExtractor... 

:: Instalar dependencias necesarias para el build
pip install pyinstaller

:: Ejecutar PyInstaller con configuraciones optimizadas
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "RSDataExtractor" ^
  --add-data "config.yaml;." ^
  --add-data "src/desktop/logic;logic" ^
  --hidden-import playwright ^
  --hidden-import playwright.async_api ^
  --hidden-import customtkinter ^
  --hidden-import PIL.ImageResampling ^
  main.py 

echo. 
echo Build completado: dist/RSDataExtractor.exe 
pause 
