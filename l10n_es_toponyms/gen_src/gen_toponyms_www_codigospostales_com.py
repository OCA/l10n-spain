# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com) All Rights Reserved.
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com> 
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import sys
import os.path
import re

def capitalizeSpanishCity(originalName):
    #return re.sub(r"[A-Za-z]+('[A-Za-z]+)?",
                   #lambda mo: mo.group(0)[0].upper() + mo.group(0)[1:].lower(), 
                   #originalName)
    # Quitar mayúsculas de las letras no iniciales
    name = ' '.join([x.capitalize() for x in originalName.split()])
    # Buscar Ñ, Ü
    #TODO: No funciona esta sustitución
    name = re.sub(r"[A-Za-z]Ñ", lambda mo: mo.group(0)[0] + "ñ", name)
    name = re.sub(r"[A-Za-z]Ü", lambda mo: mo.group(0)[0] + "ü", name)
    return name

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "USO: $s <ruta_de_la_carpeta>" $sargv[0]
        sys.exit(1)
    if not os.path.isdir(sys.argv[1]):
        print "Carpeta de datos no válida."
        sys.exit(1)
    if not os.path.exists(os.path.join(sys.argv[1], "codciu.txt")):
        print "Archivo 'codciu.txt' no encontrado."
        sys.exit(1)
    fIndex = open(os.path.join(sys.argv[1], "codciu.txt"), 'r')
    # Preparar archivo en el que escribir
    output = open("municipios_cpostal.py", 'w')
    output.write("cod_postales = [\n")
    # Leer líneas con los archivos de CPs
    for line in fIndex:
        pos = 0
        while line[pos].isdigit() or line[pos].islower():
            pos += 1
        # Abrir archivo de códigos postales
        if os.path.exists(os.path.join(sys.argv[1], "%scodpos.txt" %line[:pos])):
            fCPs = open(os.path.join(sys.argv[1], "%scodpos.txt" %line[:pos]), 'r')
            if line[pos-1] == 'x':
                # Códigos postales de municipios
                for lineCP in fCPs:
                    cp, ciudad = lineCP.split(':')
                    output.writelines('    ["%s", "%s"],\n' %(cp, capitalizeSpanishCity(ciudad[:-1])))
            fCPs.close()
    output.write("]")
    # Cerrar archivos
    fIndex.close()
    output.close()
    print "Proceso terminado"
