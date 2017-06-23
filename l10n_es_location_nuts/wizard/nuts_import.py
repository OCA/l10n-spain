# -*- coding: utf-8 -*-
# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2015 Tecnativa - Jairo Llopis
# Copyright 2017 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
import logging

logger = logging.getLogger(__name__)


class NutsImport(models.TransientModel):
    _inherit = 'nuts.import'
    _es_state_map = {
        'ES111': 'base.state_es_c',  # A Coruña
        'ES421': 'base.state_es_ab',  # Albacete
        'ES521': 'base.state_es_a',  # Alicante / Alacant
        'ES611': 'base.state_es_al',  # Almería
        'ES211': 'base.state_es_vi',  # Araba/Álava
        'ES120': 'base.state_es_o',  # Asturias
        'ES411': 'base.state_es_av',  # Ávila
        'ES431': 'base.state_es_ba',  # Badajoz
        'ES511': 'base.state_es_b',  # Barcelona
        'ES213': 'base.state_es_bi',  # Bizkaia
        'ES412': 'base.state_es_bu',  # Burgo
        'ES432': 'base.state_es_cc',  # Cáceres
        'ES612': 'base.state_es_ca',  # Cádiz
        'ES130': 'base.state_es_s',  # Cantabria
        'ES522': 'base.state_es_cs',  # Castellón / Castelló
        'ES630': 'base.state_es_ce',  # Ceuta
        'ES422': 'base.state_es_cr',  # Ciudad Real
        'ES613': 'base.state_es_co',  # Córdoba
        'ES423': 'base.state_es_cu',  # Cuenca
        'ES531': 'base.state_es_pm',  # Eivissa y Formentera
        'ES703': 'base.state_es_tf',  # El Hierro
        'ES704': 'base.state_es_gc',  # Fuerteventura
        'ES212': 'base.state_es_ss',  # Gipuzkoa
        'ES512': 'base.state_es_gi',  # Girona
        'ES705': 'base.state_es_gc',  # Gran Canaria
        'ES614': 'base.state_es_gr',  # Granada
        'ES424': 'base.state_es_gu',  # Guadalajara
        'ES615': 'base.state_es_h',  # Huelva
        'ES241': 'base.state_es_hu',  # Huesca
        'ES616': 'base.state_es_j',  # Jaén
        'ES706': 'base.state_es_tf',  # La Gomera
        'ES707': 'base.state_es_tf',  # La Palma
        'ES230': 'base.state_es_lo',  # La Rioja
        'ES708': 'base.state_es_gc',  # Lanzarote
        'ES413': 'base.state_es_le',  # León
        'ES513': 'base.state_es_l',  # Lleida
        'ES112': 'base.state_es_lu',  # Lugo
        'ES300': 'base.state_es_m',  # Madrid
        'ES617': 'base.state_es_ma',  # Málaga
        'ES532': 'base.state_es_pm',  # Mallorca
        'ES640': 'base.state_es_ml',  # Melilla
        'ES533': 'base.state_es_ba',  # Menorca
        'ES620': 'base.state_es_mu',  # Murcia
        'ES220': 'base.state_es_na',  # Navarra
        'ES113': 'base.state_es_or',  # Ourense
        'ES414': 'base.state_es_p',  # Palencia
        'ES114': 'base.state_es_po',  # Pontevedra
        'ES415': 'base.state_es_sa',  # Salamanca
        'ES416': 'base.state_es_sg',  # Segovia
        'ES618': 'base.state_es_se',  # Sevilla
        'ES417': 'base.state_es_so',  # Soria
        'ES514': 'base.state_es_t',  # Tarragona
        'ES709': 'base.state_es_tf',  # Tenerife
        'ES242': 'base.state_es_te',  # Teruel
        'ES425': 'base.state_es_to',  # Toledo
        'ES523': 'base.state_es_v',  # Valencia / València
        'ES418': 'base.state_es_va',  # Valladolid
        'ES419': 'base.state_es_za',  # Zamora
        'ES243': 'base.state_es_z',  # Zaragoza
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
