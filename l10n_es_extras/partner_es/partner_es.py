# -*- encoding: utf-8 -*-

from osv import osv, fields

def _CRC(cTexto):
    """Calculo el CRC de un número de 10 dígitos
    ajustados con ceros por la izquierda"""
    factor=(1,2,4,8,5,10,9,7,3,6)
    # Cálculo CRC
    nCRC=0
    for n in range(10):
        nCRC += int(cTexto[n])*factor[n]
    # Reducción del CRC a un dígito
    nValor=11 - nCRC%11
    if nValor==10: nValor=1
    elif nValor==11: nValor=0
    return nValor

def CalcCC(cBanco,cSucursal,cCuenta):
    """Cálculo del Código de Control Bancario"""
    cTexto="00%04d%04d" % (int(cBanco),int(cSucursal))
    DC1=_CRC(cTexto)
    cTexto="%010d" % long(cCuenta)
    DC2=_CRC(cTexto)
    return "%1d%1d" % (DC1,DC2)

class res_partner_bank(osv.osv):
    _inherit = 'res.partner.bank'
    _columns = {
        'acc_country_id': fields.many2one("res.country", 'País de la cuenta', help="""Si el país de la cuenta bancaria es España valida el número de la cuenta: Cuenta los caracteres que sean dígitos de la cuenta bancaria:
- Si los dígitos son 18 calcula los dos dígitos de control
- Si los dígitos son 20 calcula los dos dígitos de control e ignora los actuales
    Presenta el resultado con el formato "1234 5678 06 1234567890"
- Si el número de dígitos es diferente de 18 0 20 deja el valor inalterado"""),
        }
    def onchange_banco(self, cr, uid, ids, account, country_id):
        # No se por qué motivo, al añadir un nuevo banco, en ocasiones
        # la función onchange_banco se ejecuta con el valor account=False
        # dando el error: TypeError: 'bool' object is not iterable
        # El problema se resuelve con las tres siguientes líneas

        if type(account) <> str or type(country_id) <> int:
            #print "¿Por qué account es <type 'bool'>?"
            return {'value':{}}
        cr.execute("select code from res_country where id = " + str(country_id))
        if cr.fetchone()[0].upper() in ('ES', 'CT'):
            number = ""
            for i in account:
                if i.isdigit():
                    number += i
            if len(number) == 18:
                cuenta = number[8:18]
            elif len(number) == 20:
                cuenta = number[10:20]
            else:
                return {'value':{}}
            name = number[0:4]
            oficina = number[4:8]
            dc = CalcCC(name, oficina, cuenta)
            number = "%s %s %s %s" %(name, oficina, dc, cuenta)
            return {'value':{'acc_number': number}}
        return {'value':{}}
res_partner_bank()


def check_vat_es(cTexto):
    cTexto = cTexto.strip().upper()
    prefijo = ''
    if cTexto[0] == 'X':
        prefijo = 'X'
        if cTexto[-1].isalpha():
            cTexto = cTexto[1:].zfill(9)
        elif cTexto[-1].isdigit():
            cTexto = cTexto[1:].zfill(8) + 'A'
    if cTexto.isdigit():
        cTexto = cTexto + 'A'

    if cTexto.__len__()<>9:
        #raise osv.except_osv('Aviso', 'El CIF/NIF no tiene 9 caracteres')
        return False

    def check_nif_empresa():
        letras = 'ABCDEFGHKLMPQSX'
        if cTexto[0].upper() not in letras:
            #raise osv.except_osv('Aviso', 'La primera letra del CIF no es ninguna de estas letras: ABCDEFGHKLMPQSX')
            return False
        if cTexto[8].isalpha() and cTexto[0].upper() not in ('K','P','Q','S'):
            #raise osv.except_osv('Aviso', 'La primera letra del CIF no es ninguna de estas letras: KPQS')
            return False
        cadena = cTexto[1:8]
        suma = int(cadena[1])+int(cadena[3])+int(cadena[5])
        for i in range(0,4):
            suma += ((2*int(cadena[2*i]) % 10) + (2*int(cadena[2*i]) // 10))
        resultado = (10 - (suma % 10)) % 10
        if cTexto[0].upper() in ('K','P','Q','S'):
            if resultado == 0:
                resultado = 10
            return cTexto[8]==chr(64+resultado)
        return cTexto[8] == resultado.__str__()

    def check_cif_particular():
        claves = 'TRWAGMYFPDXBNJZSQVHLCKET'
        nif = int(cTexto[0:8])
        posicion = nif % 23
        #return claves[posicion]==cTexto[8].upper()
        return str(nif).zfill(8) + claves[posicion]

    if cTexto[0].isalpha() and cTexto[1:7].isdigit():
        valido = check_nif_empresa()
        #if not valido:
        #     raise osv.except_osv('Aviso', 'CIF no válido')
        return valido
    if cTexto[0:7].isdigit() and cTexto[8].isalpha():
        return prefijo + check_cif_particular()
    else:
        #raise osv.except_osv('Aviso', 'CIF/NIF no válido')
        return False

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'comercial': fields.char('Nombre Comercial', size=128, select=True), # Nombre Comercial del Partner
        'country_id': fields.many2one("res.country", 'País', help="""Si el país es España valida el número de CIF/NIF de la empresa. Si es un DNI sin letra ésta es añadida automáticamente"""),
        }
    def vat_check(self, cr, uid, ids, vat, country_id):
        if not country_id or not vat:
            return {'value':{}}
        cr.execute("select code from res_country where id = " + str(country_id))
        if cr.fetchone()[0].upper() in ('ES', 'CT'):
            newvat = check_vat_es(vat)
            if newvat:
                if type(newvat) == str:
                    # DNI modificado. Se ha añadido la letra al DNI
                    #raise osv.except_osv('Aviso', 'DNI modificado. Se ha añadido la letra al DNI')
                    return {'value':{'vat': newvat}}
                return {'value':{}}
            # CIF incorrecto. Corrija el CIF
            return {'value':{'vat': ''}}
        return {'value':{}}
res_partner()
