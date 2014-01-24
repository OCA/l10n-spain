# -*- coding: utf-8 -*-

import unicodedata, datetime
import logging

def mensaje_consola(tipo, mensaje):
	_logger = logging.getLogger('lopd')
	# La función recibe como parámetros el tipo de mensaje (1:INFO, 2:WARNING, 3:ERROR) y el mensaje que se mostrará
	if tipo==1: _logger.info(mensaje)		#tipomsg="\033[1;32mINFO"
	elif tipo==2: _logger.warning(mensaje)	#tipomsg="\033[1;33mWARNING"
	elif tipo==3: _logger.error(mensaje)	#tipomsg="\033[1;31mERROR"
	#ahora=datetime.datetime.now()
	#print '['+ahora.strftime("%Y-%m-%d %T,%f")[:23]+'][lopd] '+tipomsg+'\033[0;39m:'+mensaje
	return True

def _to_unicode(s):
	try:
		return s.decode('utf-8')
	except UnicodeError:
		try:
			return s.decode('latin')
		except UnicodeError:
			try:
				return s.encode('ascii')
			except UnicodeError:
				return s

def normalizar_cadena(cadena):
	# Devuelve la cadena normalizada sin acentos
	return ''.join((c for c in unicodedata.normalize('NFD', cadena) if unicodedata.category(c) != 'Mn'))

def capitalizar(cad):
	try: return normalizar_cadena(unicode(cad)).upper()
	except: return _to_unicode(cad.upper())

def minimizar(cad):
	try: return normalizar_cadena(unicode(cad)).lower()	
	except: return _to_unicode_(cad.lower())

def sin_espacios(cadena):
	if cadena:
		cadena = cadena.replace(' ','')
		cadena = cadena.replace('-','')
		return cadena
	else: return ""

