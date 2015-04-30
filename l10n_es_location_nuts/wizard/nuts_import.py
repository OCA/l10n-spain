# -*- coding: utf-8 -*-
# Python source code encoding : https://www.python.org/dev/peps/pep-0263/
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright :
#        (c) 2015 Antiun Ingenieria, SL (Madrid, Spain, http://www.antiun.com)
#                 Antonio Espinosa <antonioea@antiun.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp import models, api
import logging

logger = logging.getLogger(__name__)


class NutsImport(models.TransientModel):
    _inherit = 'nuts.import'
    _es_state_map = {
        'ES111': 'l10n_es_toponyms.ES15',  # A Coruña
        'ES112': 'l10n_es_toponyms.ES27',  # Lugo
        'ES113': 'l10n_es_toponyms.ES32',  # Ourense
        'ES114': 'l10n_es_toponyms.ES36',  # Pontevedra
        'ES120': 'l10n_es_toponyms.ES33',  # Asturias
        'ES130': 'l10n_es_toponyms.ES39',  # Cantabria
        'ES211': 'l10n_es_toponyms.ES01',  # Araba/Álava
        'ES212': 'l10n_es_toponyms.ES20',  # Gipuzkoa
        'ES213': 'l10n_es_toponyms.ES48',  # Bizkaia
        'ES220': 'l10n_es_toponyms.ES31',  # Navarra
        'ES230': 'l10n_es_toponyms.ES26',  # La Rioja
        'ES241': 'l10n_es_toponyms.ES22',  # Huesca
        'ES242': 'l10n_es_toponyms.ES44',  # Teruel
        'ES243': 'l10n_es_toponyms.ES50',  # Zaragoza
        'ES300': 'l10n_es_toponyms.ES28',  # Madrid
        'ES411': 'l10n_es_toponyms.ES05',  # Ávila
        'ES412': 'l10n_es_toponyms.ES09',  # Burgos
        'ES413': 'l10n_es_toponyms.ES24',  # León
        'ES414': 'l10n_es_toponyms.ES34',  # Palencia
        'ES415': 'l10n_es_toponyms.ES37',  # Salamanca
        'ES416': 'l10n_es_toponyms.ES40',  # Segovia
        'ES417': 'l10n_es_toponyms.ES42',  # Soria
        'ES418': 'l10n_es_toponyms.ES47',  # Valladolid
        'ES419': 'l10n_es_toponyms.ES49',  # Zamora
        'ES421': 'l10n_es_toponyms.ES02',  # Albacete
        'ES422': 'l10n_es_toponyms.ES13',  # Ciudad Real
        'ES423': 'l10n_es_toponyms.ES16',  # Cuenca
        'ES424': 'l10n_es_toponyms.ES19',  # Guadalajara
        'ES425': 'l10n_es_toponyms.ES45',  # Toledo
        'ES431': 'l10n_es_toponyms.ES06',  # Badajoz
        'ES432': 'l10n_es_toponyms.ES10',  # Cáceres
        'ES511': 'l10n_es_toponyms.ES08',  # Barcelona
        'ES512': 'l10n_es_toponyms.ES17',  # Girona
        'ES513': 'l10n_es_toponyms.ES25',  # Lleida
        'ES514': 'l10n_es_toponyms.ES43',  # Tarragona
        'ES521': 'l10n_es_toponyms.ES03',  # Alicante / Alacant
        'ES522': 'l10n_es_toponyms.ES12',  # Castellón / Castelló
        'ES523': 'l10n_es_toponyms.ES46',  # Valencia / València
        'ES531': 'l10n_es_toponyms.ES07',  # Eivissa y Formentera
        'ES532': 'l10n_es_toponyms.ES07',  # Mallorca
        'ES533': 'l10n_es_toponyms.ES07',  # Menorca
        'ES611': 'l10n_es_toponyms.ES04',  # Almería
        'ES612': 'l10n_es_toponyms.ES11',  # Cádiz
        'ES613': 'l10n_es_toponyms.ES14',  # Córdoba
        'ES614': 'l10n_es_toponyms.ES18',  # Granada
        'ES615': 'l10n_es_toponyms.ES21',  # Huelva
        'ES616': 'l10n_es_toponyms.ES23',  # Jaén
        'ES617': 'l10n_es_toponyms.ES29',  # Málaga
        'ES618': 'l10n_es_toponyms.ES41',  # Sevilla
        'ES620': 'l10n_es_toponyms.ES30',  # Murcia
        'ES630': 'l10n_es_toponyms.ES51',  # Ceuta
        'ES640': 'l10n_es_toponyms.ES52',  # Melilla
        'ES703': 'l10n_es_toponyms.ES38',  # El Hierro
        'ES704': 'l10n_es_toponyms.ES38',  # Fuerteventura
        'ES705': 'l10n_es_toponyms.ES38',  # Gran Canaria
        'ES706': 'l10n_es_toponyms.ES38',  # La Gomera
        'ES707': 'l10n_es_toponyms.ES38',  # La Palma
        'ES708': 'l10n_es_toponyms.ES38',  # Lanzarote
        'ES709': 'l10n_es_toponyms.ES38',  # Tenerife
        'ESZZZ': False,  # Extra-Regio NUTS 3
    }

    @api.model
    def state_mapping(self, data, node):
        mapping = super(NutsImport, self).state_mapping(data, node)
        level = data.get('level', 0)
        code = data.get('code', '')
        if self._current_country.code == 'ES' and level == 4:
            toponyms = self._es_state_map.get(code, False)
            if toponyms:
                state = self.env.ref(toponyms)
                if state:
                    mapping['state_id'] = state.id
        return mapping
