# -*- encoding: utf-8 -*-

import wizard
import netsvc
import pooler

logger = netsvc.Logger()

diccio_cuentas = {
	'20': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'280': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'290': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'21': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'23': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'281': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'291': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'22': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'282': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'292': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2403': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2404': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2413': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2414': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2423': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2424': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2493': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2494': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'293': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2943': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2944': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2953': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2954': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2405': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2415': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2425': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'250': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'251': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'252': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'253': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'254': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'255': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'257': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'258': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'26': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2495': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'259': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2945': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'2955': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'297': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'298': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'474': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'580': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'581': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'582': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'583': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'584': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'599': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'30': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'31': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'32': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'33': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'34': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'35': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'36': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'407': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'39': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'430': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'431': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'432': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'433': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'434': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'435': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'436': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'437': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'490': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'493': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'5580': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'44': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'460': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'470': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'471': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'472': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'5531': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'5533': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'544': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'5303': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5304': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5313': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5314': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5323': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5324': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5333': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5334': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5343': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5344': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5353': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5354': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5523': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5524': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5393': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5394': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'593': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5943': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5944': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5953': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5954': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5305': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5315': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5325': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5335': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5345': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5355': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'540': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'541': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'542': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'543': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'545': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'546': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'547': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'548': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'551': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5525': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5590': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5593': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'565': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'566': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'549': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5945': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'5955': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'597': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'598': {'tipo': 'asset', 'cierre': 'balance', 'conciliar': False },
		'480': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'567': {'tipo': 'receivable', 'cierre': 'unreconciled', 'conciliar': True },
		'57': {'tipo': 'cash', 'cierre': 'balance', 'conciliar': False },
		'100': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'101': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'102': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'1030': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'1040': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'110': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'112': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'113': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'114': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'115': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'119': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'108': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'109': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'120': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'121': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'118': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'129': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'557': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'111': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'133': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'1340': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'137': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'130': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'131': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'132': {'tipo': 'equity', 'cierre': 'balance', 'conciliar': False },
		'14': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'1605': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'170': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'1625': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'174': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'1615': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'1635': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'171': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'172': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'173': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'175': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'176': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'177': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'178': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'179': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'180': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'185': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'189': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'1603': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'1604': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'1613': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'1614': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'1623': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'1624': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'1633': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'1634': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'479': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'181': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'585': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'586': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'587': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'588': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'589': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'499': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'529': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5105': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'520': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'527': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5125': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'524': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'194': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'500': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'501': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'505': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'506': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'509': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5115': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5135': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5145': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'521': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'522': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'523': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'525': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'526': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'528': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'551': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5525': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5530': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5532': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'555': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5565': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5566': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5595': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5598': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'560': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'561': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'569': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'1034': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'1044': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'190': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'192': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5103': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5104': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5113': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5114': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5123': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5124': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5133': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5134': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5143': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5144': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5523': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5524': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5563': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'5564': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'400': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'401': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'403': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'404': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'405': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'406': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'41': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'438': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'465': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'466': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'475': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'476': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'477': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'485': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'568': {'tipo': 'payable', 'cierre': 'unreconciled', 'conciliar': True },
		'6': {'tipo': 'expense', 'cierre': 'none', 'conciliar': False },
		'8': {'tipo': 'expense', 'cierre': 'none', 'conciliar': False },
		'7': {'tipo': 'income', 'cierre': 'none', 'conciliar': False },
		'9': {'tipo': 'income', 'cierre': 'none', 'conciliar': False },

}

inicial_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Crear Subcuentas Contables">
	<field name="n_digitos"/>
</form>'''


inicial_fields = {
	'n_digitos': {'string':'N.Digitos (mínimo 6)', 'type':'integer', 'required': True, 'default': 6},
}


class l10n_sp_crearcuentas(wizard.interface):
	def _localizar_conf(self, padre):
		loc = str(padre)
		while loc:
			if loc in diccio_cuentas.keys():
				return diccio_cuentas[loc]
			loc = loc[0:len(loc)-1]
		return {}

	def _crear_cuentas(self, cr, uid, data, context):
		digitos = data['form']['n_digitos']
		if digitos < 6:
			return False

		cr.execute ("""select distinct child_id from account_account_rel
				left join account_account acc
				on acc.id = account_account_rel.child_id
				where child_id not in
				(select distinct parent_id from account_account_rel)
				and acc.type = 'view';
		""")

		cuentas_ids = [a for (a,) in cr.fetchall()]
		if not isinstance(cuentas_ids, list):
			return True
		cuentas_padre = pooler.get_pool(cr.dbname).get('account.account').read(cr, uid, cuentas_ids, ['code','name',])
		for cuenta in cuentas_padre:
			cuenta_conf = self._localizar_conf(cuenta['code'])
			if not cuenta_conf:
				continue
			vals = {
		        'code': cuenta['code'] + (digitos-len(cuenta['code'])) * '0',
			'reconcile': cuenta_conf['conciliar'],
			'close_method': cuenta_conf['cierre'],
			'parent_id': [(6, 0, [cuenta['id']])],
			'type': cuenta_conf['tipo'],
			'name': cuenta['name']
			}
			pooler.get_pool(cr.dbname).get('account.account').create(cr,uid,vals)

		return {}


	states = {
		'init': {
			'actions': [],
			'result': {'type':'form', 'arch':inicial_form, 'fields':inicial_fields, 'state':[('end','Cancel'),('done','OK') ]}
		},
		'done': {
			'actions': [_crear_cuentas],
			'result': {'type':'state', 'state':'end'}
		}
	}

l10n_sp_crearcuentas('l10n_chart_ES_2008.crearcuentas')
