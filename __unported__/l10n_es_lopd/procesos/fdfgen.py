# -*- coding: ISO-8859-15 -*-

def mes2string(numero):
	if numero==1: return "ENERO"
	elif numero==2: return "FEBRERO"
	elif numero==3: return "MARZO"
	elif numero==4: return "ABRIL"
	elif numero==5: return "MAYO"
	elif numero==6: return "JUNIO"
	elif numero==7: return "JULIO"
	elif numero==8: return "AGOSTO"
	elif numero==9: return "SEPTIEMBRE"
	elif numero==10: return "OCTUBRE"
	elif numero==11: return "NOVIEMBRE"
	elif numero==12: return "DICIEMBRE"

def crear_fdf(datos):
		
	from datetime import datetime
	ahora=datetime.now()
	f_dia = ahora.strftime("%d")
	mes = int(ahora.strftime("%m"))
	f_mes = mes2string(mes)
	f_ano = ahora.strftime("%Y")

	fdf = "%FDF-1.2\n\n"
	fdf+= "1 0 obj\n<</FDF << /Fields 2 0 R>>>>\nendobj\n"
	fdf+= "2 0 obj\n[<< /T (Formulario[0]) /V () >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0]) /V () >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0]) /V () >>\n"
	
	codigo = datos['num_reg']
	#TODO: Modificar si cambia el soporte
	soporte = "FICHERO XML SIN FIRMA" #Soporte de la solicitud y modo de presentaci�n

	alta = modificacion = baja = ""
	# Forma de Cumplimentaci�n (forma_c)
	# XML: u - Alta, v - modificaci�n, w - supresi�n
	# XML Firmado: x - Alta, y - modificaci�n, z - supresi�n
	if datos['forma_c'] == 'u' or datos['forma_c']=='x': alta="X"
	elif datos['forma_c']=='v' or datos['forma_c']=='y': modificacion="X"
	elif datos['forma_c']=='w' or datos['forma_c']=='z': baja="X"

	#Datos del encabezado
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].EncabezadoDeclarante[0].Alta[0]) /V ("+alta+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].EncabezadoDeclarante[0].Baja[0]) /V ("+baja+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].EncabezadoDeclarante[0].Modificacion[0]) /V ("+modificacion+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].EncabezadoDeclarante[0].C_Inscripcion_Final[0]) /V ("+codigo+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].EncabezadoDeclarante[0].Soporte_presentacion[0]) /V ("+soporte+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_1[0].Num_envio[0]) /V ("+datos['id_upload']+") >>\n"

	#Datos del responsable
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_1[0].NIF_AP1[0]) /V ("+datos['cif_nif']+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_1[0].N_RazonAP1[0]) /V ("+datos['razon_s']+") >>\n"

	#Datos del declarante
	# *Denomina_postal = Apellido y nombre o Raz�n social
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_1[0].Nombre[0]) /V ("+datos['nombre']+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_1[0].Apellido1[0]) /V ("+datos['apellido1']+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_1[0].Apellido2[0]) /V ("+datos['apellido2']+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_1[0].NIF[0]) /V ("+datos['nif']+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_1[0].Texto_libre_cargo[0]) /V ("+datos['cargo']+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].Denomina_postal[0]) /V ("+datos['denomina_p']+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].Dir_postal[0]) /V ("+datos['dir_postal']+") >>\n"

	#formato fecha En 'localidad' a 'dia' de 'mes' de 'a�o' (mes en formato texto)
	#TODO: Ojo, localidad en la que se firma el impreso, se define igual a la localidad de notificaci�n
	f_localidad = datos['localidad']
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].FirmaLocalidad[0]) /V ("+f_localidad+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].FirmaDia[0]) /V ("+f_dia+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].FirmaMes[0]) /V ("+f_mes+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].FirmaAno[0]) /V ("+f_ano+") >>\n"
	
	# id_notific: Direcci�n electr�nica del servicio de notificaciones. Opcional. En los env�os realizados sin firma digital vendr� siempre vac�o. Si el env�o se hace con firma digital y se ha indicado en el elemento anterior (forma) un valor '2', s�lo se deber� cumplimentar cuando la suscripci�n al Servicio de Notificaciones Telem�ticas Seguras se haya realizado con un certificado de persona jur�dica. Se consignar�, en ese caso, la Direcci�n Electr�nica �nica (DEU) asignada por dicho Servicio. Cuando no se cumplimente, el servicio Web obtendr� la DEU a partir del los datos del NIF, nombre y apellidos de la persona f�sica correspondiente al certificado con el que se ha firmado. Hasta 70 caracteres.
	id_notific="" #TODO: Modificar en caso de incluir firma
	if datos['forma']=='1': forma = "XML SIN FIRMA DIGITAL" #TODO: Modificar en caso de incluir firma

	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].Forma[0]) /V ("+forma+") >>\n"
	#Direcci�n a efectos de notificaci�n
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].Localidad[0]) /V ("+datos['localidad']+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].Pais[0]) /V ("+str(datos['pais'])+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].Postal[0]) /V ("+datos['postal']+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].Provincia[0]) /V ("+datos['provincia']+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].Telefono[0]) /V ("+datos['telefono']+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].fax[0]) /V ("+datos['fax']+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].email[0]) /V ("+datos['email']+") >>\n"
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].id_notific[0]) /V ("+id_notific+") >>\n"

	#Ind_deberes = Conocimiento de los deberes del declarante
	fdf+= "<< /T (Formulario[0].PrivadoFinal[0].PaginaFinal3[0].Bloque0_2[0].Ind_deberes[0]) /V (1) >>\n"

	fdf+= "]\nendobj\ntrailer\n<</Root 1 0 R>>\n%%EOF"
	return fdf

