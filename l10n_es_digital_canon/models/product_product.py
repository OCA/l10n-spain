# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    # The selection key is used for getting the tax XML-ID, so expand it with care
    l10n_es_digital_canon = fields.Selection(
        [
            ("3_75.tablet_32", "Tablet hasta 32 Gb - 3,75"),
            ("3_75.tablet_64", "Tablet de 32,01 Gb hasta 64 Gb - 3,75"),
            ("3_75.tablet_64_plus", "Tablet de más de 64,01 Gb - 3,75"),
            ("3_25.phone_64", "Teléfono inteligente hasta 64 Gb - 3,25"),
            ("3_25.phone_128", "Teléfono inteligente de 64,01 Gb. A 128 Gb - 3,25"),
            ("3_25.phone_128_plus", "Teléfono inteligente de más de 128 Gb - 3,25"),
            ("2_5.watch_multimedia", "Reloj inteligente multimedia - 2,5"),
            ("2_5.watch_monofunc", "Reloj inteligente monofunción - 2,5"),
            ("5_33.pc_1tb", "PC sobremesa y portatil hasta 1 Tb - 5,33"),
            ("5_33.pc_6tb", "PC sobremesa y portatil de 1,01 Tb. Hasta 6 Tb - 5,33"),
            ("5_33.pc_6tb_plus", "PC sobremesa y portatil de más de 6,01 Tb - 5,33"),
            ("0_9.hdd_1tb", "HDD Para integrar hasta 1 Tb - 0,9"),
            ("1_5.hdd_6tb", "HDD Para integrar de 1,01 Tb. Hasta 6 Tb - 1,5"),
            ("3.hdd_6tb_plus", "HDD Para integrar más de 6,01 Tb - 3"),
            ("0_9.sdd_256gb", "SDD Para integrar hasta 256 Gb - 0,9"),
            ("1_5.sdd_1tb", "SDD Para integrar de 256,01 Gb. Hasta 1 Tb - 1,5"),
            ("3.sdd_1tb_plus", "SDD Para integrar de más de 1,01 Tb - 3"),
            ("3.equipo_1tb", "Equipo con disco integrado hasta 1 Tb - 3"),
            ("4.equipo_6tb", "Equipo con disco integrado de 1,01 Tb. Hasta 6 Tb - 4"),
            ("5.equipo_6tb_plus", "Equipo con disco integrado más de 6,01 Tb - 5"),
            (
                "5_25.equipo_multifunc",
                "Equipo multifunción de reprografía hasta 39 copias - 5,25",
            ),
            (
                "5_25.equipo_multifunc_39",
                "Equipo multifunción de reprografía de más de 39 copias - 5,25",
            ),
            ("4.impresora_39", "Impresora monofunción hasta 39 copias - 4"),
            ("0.impresora_39_plus", "Impresora monofuncional de más de 39 copias - 0"),
            (
                "3.escanner_29ppm",
                "Escáner con pantalla de exposición de hasta 29 ppm - 3",
            ),
            ("3.escanner_hand", "Escáner de mano - 3"),
            ("4.hdd_periferico_6tb", "Disco duro periférico HDD hasta 6 Tb - 4"),
            (
                "6_45.hdd_periferico_6tb",
                "Disco duro periférico HDD de más de 6,01 Tb - 6,45",
            ),
            ("4.sdd_periferico_1tb", "Disco duro periférico SSD hasta 1 Tb - 4"),
            (
                "6_45.sdd_periferico_1tb",
                "Disco duro periférico SSD de más de 1,01 Tb - 6,45",
            ),
            ("0_24.tarjeta_memoria_64", "Tarjeta de memoria hasta 64 Gb - 0,24"),
            (
                "0_24.tarjeta_memoria_64_plus",
                "Tarjeta de memoria de más de 64,01 Gb - 0,24",
            ),
            ("0_24.memoria_usb_64", "Memoria USB hasta 64 Gb - 0,24"),
            ("0_24.memoria_usb_64_plus", "Memoria USB de más de 64,01 Gb - 0,24"),
            ("3_15.mp3", "Reproductor MP3 - 3,15"),
            ("3_15.mp4", "Reproductor MP4 - 3,15"),
            ("1_1.phone_mp3", "Teléfono móvil no inteligente con MP3 - 1,1"),
            ("2.ebook_monofunc", "Libro electrónico monofunción - 2"),
            ("3_15.ebook_multimedia", "Libro electrónico multimedia - 3,15"),
            ("0_08.cd", "CD - 0,08"),
            ("0_21.dvd", "DVD y Blu-ray - 0,21"),
            ("1.grabadora_cd_dvd", "Grabadora externa y para integrar CD/DVD - 1"),
        ],
        string="Digital Canon Category",
    )
