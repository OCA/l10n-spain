Utilidad para generar el archivo de bancos a partir de la información del Banco de España
=========================================================================================

**NOTA**: Necesita la librería python 'xlrd'

1. Descargar el excel de las 'Entidades con establecimiento' de la web del
   Banco de España. Hay que tener cuidado que ponen el mismo archivo con
   extensión en mayúsculas o minúsculas y hay que ver cuál es el actualizado:

   http://www.bde.es/f/webbde/IFI/servicio/regis/ficheros/es/REGBANESP_CONESTAB_A.XLS
   http://www.bde.es/f/webbde/IFI/servicio/regis/ficheros/es/REGBANESP_CONESTAB_A.xls

2. Mover el archivo descargado 'REGBANESP_CONESTAB_A.XLS' a la carpeta gen_src
3. Ejecutar:

        python gen_data_banks.py
4. Se generará un archivo data_banks.xml en la carpeta wizard que sustituirá el
   anterior
