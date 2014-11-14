# -*- coding: utf-8 -*-

"""
This class generate code 128 (http://en.wikipedia.org/wiki/Code_128) bar code,
it requires PIL (python imaging library) installed.


This program is based on EanBarCode.py found on
http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/426069 submitted by Remi Inconnu.

This code was written by Jostein Leira and is published under the
Creative Commons 3.0 BY SA (aka CC 3.0 BY SA). This license can be found at
http://creativecommons.org/licenses/by-sa/3.0/

Este código ha sido editado por Compuservice Network Consulting para la integración en el
módulo LOPD para OpenERP.

Code 128 is variable lenght and a 103 module checksum is added automatically.


Create bar code sample :
   from Code128 import Code128
   bar = Code128()
   bar.crear_imagen("9782212110708",50,"gif")

"""


class Code128:

    CharSetA = {
        ' ': 0, '!': 1, '"': 2, '#': 3, '$': 4, '%': 5, '&': 6, "'": 7,
        '(': 8, ')': 9, '*': 10, '+': 11, ',': 12, '-': 13, '.': 14, '/': 15,
        '0': 16, '1': 17, '2': 18, '3': 19, '4': 20, '5': 21, '6': 22, '7': 23,
                 '8': 24, '9': 25, ':': 26, ';': 27, '<': 28, '=': 29, '>': 30, '?': 31,
                 '@': 32, 'A': 33, 'B': 34, 'C': 35, 'D': 36, 'E': 37, 'F': 38, 'G': 39,
                 'H': 40, 'I': 41, 'J': 42, 'K': 43, 'L': 44, 'M': 45, 'N': 46, 'O': 47,
                 'P': 48, 'Q': 49, 'R': 50, 'S': 51, 'T': 52, 'U': 53, 'V': 54, 'W': 55,
                 'X': 56, 'Y': 57, 'Z': 58, '[': 59, '\\': 60, ']': 61, '^': 62, '_': 63,
                 '\x00': 64, '\x01': 65, '\x02': 66, '\x03': 67, '\x04': 68, '\x05': 69, '\x06': 70, '\x07': 71,
                 '\x08': 72, '\x09': 73, '\x0A': 74, '\x0B': 75, '\x0C': 76, '\x0D': 77, '\x0E': 78, '\x0F': 79,
                 '\x10': 80, '\x11': 81, '\x12': 82, '\x13': 83, '\x14': 84, '\x15': 85, '\x16': 86, '\x17': 87,
                 '\x18': 88, '\x19': 89, '\x1A': 90, '\x1B': 91, '\x1C': 92, '\x1D': 93, '\x1E': 94, '\x1F': 95,
                 'FNC3': 96, 'FNC2': 97, 'SHIFT': 98, 'Code C': 99, 'Code B': 100, 'FNC4': 101, 'FNC1': 102, 'START A': 103,
                 'START B': 104, 'START C': 105, 'STOP': 106
    }

    CharSetB = {
        ' ': 0, '!': 1, '"': 2, '#': 3, '$': 4, '%': 5, '&': 6, "'": 7,
        '(': 8, ')': 9, '*': 10, '+': 11, ',': 12, '-': 13, '.': 14, '/': 15,
        '0': 16, '1': 17, '2': 18, '3': 19, '4': 20, '5': 21, '6': 22, '7': 23,
                 '8': 24, '9': 25, ':': 26, ';': 27, '<': 28, '=': 29, '>': 30, '?': 31,
                 '@': 32, 'A': 33, 'B': 34, 'C': 35, 'D': 36, 'E': 37, 'F': 38, 'G': 39,
                 'H': 40, 'I': 41, 'J': 42, 'K': 43, 'L': 44, 'M': 45, 'N': 46, 'O': 47,
                 'P': 48, 'Q': 49, 'R': 50, 'S': 51, 'T': 52, 'U': 53, 'V': 54, 'W': 55,
                 'X': 56, 'Y': 57, 'Z': 58, '[': 59, '\\': 60, ']': 61, '^': 62, '_': 63,
                 '': 64, 'a': 65, 'b': 66, 'c': 67, 'd': 68, 'e': 69, 'f': 70, 'g': 71,
                 'h': 72, 'i': 73, 'j': 74, 'k': 75, 'l': 76, 'm': 77, 'n': 78, 'o': 79,
                 'p': 80, 'q': 81, 'r': 82, 's': 83, 't': 84, 'u': 85, 'v': 86, 'w': 87,
                 'x': 88, 'y': 89, 'z': 90, '{': 91, '|': 92, '}': 93, '~': 94, '\x7F': 95,
                 'FNC3': 96, 'FNC2': 97, 'SHIFT': 98, 'Code C': 99, 'FNC4': 100, 'Code A': 101, 'FNC1': 102, 'START A': 103,
                 'START B': 104, 'START C': 105, 'STOP': 106
    }

    CharSetC = {
        '00': 0, '01': 1, '02': 2, '03': 3, '04': 4, '05': 5, '06': 6, '07': 7,
                 '08': 8, '09': 9, '10': 10, '11': 11, '12': 12, '13': 13, '14': 14, '15': 15,
                 '16': 16, '17': 17, '18': 18, '19': 19, '20': 20, '21': 21, '22': 22, '23': 23,
                 '24': 24, '25': 25, '26': 26, '27': 27, '28': 28, '29': 29, '30': 30, '31': 31,
                 '32': 32, '33': 33, '34': 34, '35': 35, '36': 36, '37': 37, '38': 38, '39': 39,
                 '40': 40, '41': 41, '42': 42, '43': 43, '44': 44, '45': 45, '46': 46, '47': 47,
                 '48': 48, '49': 49, '50': 50, '51': 51, '52': 52, '53': 53, '54': 54, '55': 55,
                 '56': 56, '57': 57, '58': 58, '59': 59, '60': 60, '61': 61, '62': 62, '63': 63,
                 '64': 64, '65': 65, '66': 66, '67': 67, '68': 68, '69': 69, '70': 70, '71': 71,
                 '72': 72, '73': 73, '74': 74, '75': 75, '76': 76, '77': 77, '78': 78, '79': 79,
                 '80': 80, '81': 81, '82': 82, '83': 83, '84': 84, '85': 85, '86': 86, '87': 87,
                 '88': 88, '89': 89, '90': 90, '91': 91, '92': 92, '93': 93, '94': 94, '95': 95,
                 '96': 96, '97': 97, '98': 98, '99': 99, 'Code B': 100, 'Code A': 101, 'FNC1': 102, 'START A': 103,
                 'START B': 104, 'START C': 105, 'STOP': 106
    }

    ValueEncodings = {0: '11011001100',  1: '11001101100',  2: '11001100110',
                      3: '10010011000',  4: '10010001100',  5: '10001001100',
                      6: '10011001000',  7: '10011000100',  8: '10001100100',
                      9: '11001001000', 10: '11001000100', 11: '11000100100',
                      12: '10110011100', 13: '10011011100', 14: '10011001110',
                      15: '10111001100', 16: '10011101100', 17: '10011100110',
                      18: '11001110010', 19: '11001011100', 20: '11001001110',
                      21: '11011100100', 22: '11001110100', 23: '11101101110',
                      24: '11101001100', 25: '11100101100', 26: '11100100110',
                      27: '11101100100', 28: '11100110100', 29: '11100110010',
                      30: '11011011000', 31: '11011000110', 32: '11000110110',
                      33: '10100011000', 34: '10001011000', 35: '10001000110',
                      36: '10110001000', 37: '10001101000', 38: '10001100010',
                      39: '11010001000', 40: '11000101000', 41: '11000100010',
                      42: '10110111000', 43: '10110001110', 44: '10001101110',
                      45: '10111011000', 46: '10111000110', 47: '10001110110',
                      48: '11101110110', 49: '11010001110', 50: '11000101110',
                      51: '11011101000', 52: '11011100010', 53: '11011101110',
                      54: '11101011000', 55: '11101000110', 56: '11100010110',
                      57: '11101101000', 58: '11101100010', 59: '11100011010',
                      60: '11101111010', 61: '11001000010', 62: '11110001010',
                      63: '10100110000', 64: '10100001100', 65: '10010110000',
                      66: '10010000110', 67: '10000101100', 68: '10000100110',
                      69: '10110010000', 70: '10110000100', 71: '10011010000',
                      72: '10011000010', 73: '10000110100', 74: '10000110010',
                      75: '11000010010', 76: '11001010000', 77: '11110111010',
                      78: '11000010100', 79: '10001111010', 80: '10100111100',
                      81: '10010111100', 82: '10010011110', 83: '10111100100',
                      84: '10011110100', 85: '10011110010', 86: '11110100100',
                      87: '11110010100', 88: '11110010010', 89: '11011011110',
                      90: '11011110110', 91: '11110110110', 92: '10101111000',
                      93: '10100011110', 94: '10001011110', 95: '10111101000',
                      96: '10111100010', 97: '11110101000', 98: '11110100010',
                      99: '10111011110', 100: '10111101110', 101: '11101011110',
                      102: '11110101110', 103: '11010000100', 104: '11010010000',
                      105: '11010011100', 106: '11000111010'
                      }

    def makeCode(self, code):
        """ Create the binary code
        return a string which contains "0" for white bar, "1" for black bar """

        current_charset = None
        pos = sum = 0
        skip = False
        for c in range(len(code)):
            if skip:
                skip = False
                continue

            # Only switch to char set C if next four chars are digits
            if len(code[c:]) >= 4 and code[c:c + 4].isdigit() and current_charset != self.CharSetC or \
               len(code[c:]) >= 2 and code[c:c + 2].isdigit() and current_charset == self.CharSetC:
                # If char set C = current and next two chars ar digits, keep C
                if current_charset != self.CharSetC:
                    # Switching to Character set C
                    if pos:
                        strCode += self.ValueEncodings[
                            current_charset['Code C']]
                        sum += pos * current_charset['Code C']
                    else:
                        strCode = self.ValueEncodings[self.CharSetC['START C']]
                        sum = self.CharSetC['START C']
                    current_charset = self.CharSetC
                    pos += 1
            elif self.CharSetB.has_key(code[c]) and current_charset != self.CharSetB and \
                    not(self.CharSetA.has_key(code[c]) and current_charset == self.CharSetA):
                # If char in chrset A = current, then just keep that
                # Switching to Character set B
                if pos:
                    strCode += self.ValueEncodings[current_charset['Code B']]
                    sum += pos * current_charset['Code B']
                else:
                    strCode = self.ValueEncodings[self.CharSetB['START B']]
                    sum = self.CharSetB['START B']
                current_charset = self.CharSetB
                pos += 1
            elif self.CharSetA.has_key(code[c]) and current_charset != self.CharSetA and \
                    not(self.CharSetB.has_key(code[c]) and current_charset == self.CharSetB):
                # if char in chrset B== current, then just keep that
                # Switching to Character set A
                if pos:
                    strCode += self.ValueEncodings[current_charset['Code A']]
                    sum += pos * current_charset['Code A']
                else:
                    strCode += self.ValueEncodings[self.CharSetA['START A']]
                    sum = self.CharSetA['START A']
                current_charset = self.CharSetA
                pos += 1

            if current_charset == self.CharSetC:
                val = self.CharSetC[code[c:c + 2]]
                skip = True
            else:
                val = current_charset[code[c]]

            sum += pos * val
            strCode += self.ValueEncodings[val]
            pos += 1

        # Checksum
        checksum = sum % 103

        strCode += self.ValueEncodings[checksum]

        # The stop character
        strCode += self.ValueEncodings[current_charset['STOP']]

        # Termination bar
        strCode += "11"

        return strCode

    def crear_imagen(self, valor, alto="35", extension="png"):
        import Image
        import ImageDraw
        from string import lower, upper
        # Get the bar code list
        bits = self.makeCode(valor)

        # Crea una imágen nueva
        margen = 0
        im = Image.new("1", (len(bits) + margen, alto))

        # Create drawer
        draw = ImageDraw.Draw(im)

        # Borra la imágen
        draw.rectangle(((0, 0), (im.size[0], im.size[1])), fill=256)

        # Draw the bar codes
        for bit in range(len(bits)):
            if bits[bit] == '1':
                draw.rectangle(
                    ((bit + margen, 0), (bit + margen, alto)), fill=0)

        # Guarda la imágen resultante
        ruta = "/tmp/tmp" + valor[9:] + '_bar.' + lower(extension)
        #ruta ="/tmp/"+base64.standard_b64encode(valor[9:])+lower(extension)
        im.save(ruta, upper(extension))
        return convertir_imagen(ruta, valor)


def convertir_imagen(archivo_imagen, codigo):
    import os
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from PIL import Image

    # Se redimensiona la imágen
    imagen = Image.open(archivo_imagen)
    imagen = imagen.resize(
        (int(6.708 * inch), int(0.354 * inch)), Image.ANTIALIAS)
    imagen.save(archivo_imagen)

    # Pone la imágen en un pdf
    pdf_imagen = (archivo_imagen.split('.')[0]) + '.pdf'
    c = canvas.Canvas(pdf_imagen, pagesize=A4)
    # Pinta la imágen centrada en el pié del archivo
    ancho_imagen = 6.708 * inch
    ancho_A4 = 8.27 * inch
    centro_x = ancho_A4 / 2
    c.drawImage(archivo_imagen, ((centro_x) - (ancho_imagen / 2)), 0.6 * inch)
    c.drawCentredString(centro_x, 0.4 * inch, codigo)
    c.showPage()
    c.save()

    os.remove(archivo_imagen)  # Se elimina la imágen
    return pdf_imagen
