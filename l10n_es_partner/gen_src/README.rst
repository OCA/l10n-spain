Utilidad para generar el archivo de bancos a partir de la información del Banco de España
=========================================================================================

**NOTA**: Necesita la librería python 'csv'

1. Descargar el excel de las 'Entidades con establecimiento' de la web del
   Banco de España. Hay que tener cuidado que ponen el mismo archivo con
   extensión en mayúsculas o minúsculas y hay que ver cuál es el actualizado:

   http://www.bde.es/f/webbde/IFI/servicio/regis/ficheros/es/REGBANESP_CONESTAB_A.XLS
   http://www.bde.es/f/webbde/IFI/servicio/regis/ficheros/es/REGBANESP_CONESTAB_A.xls

2. Cambiar el formato del archivo descargado a 'csv' desde algún editor excel y guardarlo
   con el mismo nombre.
3. Mover el archivo descargado 'REGBANESP_CONESTAB_A.csv' a la carpeta gen_src
4. Ejecutar:

      `python gen_data_banks.py``
5. Se generará un archivo data_banks.csv en la carpeta wizard que sustituirá el
   anterior
