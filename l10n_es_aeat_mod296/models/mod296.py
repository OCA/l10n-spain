# -*- encoding: utf-8 -*-
##############################################################################
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models, api


class L10nEsAeatMod296Report(models.Model):

    _description = 'AEAT 296 report'
    _inherit = 'l10n.es.aeat.report'
    _name = 'l10n.es.aeat.mod296.report'

    number = fields.Char(default='296')
    casilla_01 = fields.Integer(
        string='[01] Número de perceptores', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [01] Resumen de los datos incluidos en la declaración - '
             'Número total de perceptores')
    casilla_02 = fields.Float(
        string='[02] Base retenciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [02] Resumen de los datos incluidos en la declaración - '
             'Base retenciones e ingresos a cuenta')
    casilla_03 = fields.Float(
        string='[03] Retenciones', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [03] Resumen de los datos incluidos en la declaración - '
             'Retenciones e ingresos a cuenta')
    casilla_04 = fields.Float(
        string='[04] Retenciones ingresadas', readonly=True,
        states={'calculated': [('readonly', False)]},
        help='Casilla [04] Resumen de los datos incluidos en la declaración - '
             'Retenciones e ingresos a cuenta ingresados')
    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Moneda', readonly=True,
        related='company_id.currency_id', store=True)
    lines296 = fields.One2many('l10n.es.aeat.mod296.report.line', 'mod296_id',
                               string="Lines")

    def __init__(self, pool, cr):
        self._aeat_number = '296'
        super(L10nEsAeatMod296Report, self).__init__(pool, cr)

    @api.multi
    def _get_partner_domain(self):
        res = super(L10nEsAeatMod296Report, self)._get_partner_domain()
        partners = self.env['res.partner'].search(
            [('is_non_resident', '=', True)])
        res += [('partner_id', 'in', partners.ids)]
        return res

    @api.multi
    def calculate(self):
        self.ensure_one()
        self.lines296.unlink()
        line_lst = []
        move_lines_base = self._get_tax_code_lines(['IRPBI'])
        move_lines_cuota = self._get_tax_code_lines(['ITRPC'])
        partner_lst = set([x.partner_id for x in
                           (move_lines_base + move_lines_cuota)])
        for partner in partner_lst:
            part_base_lines = move_lines_base.filtered(
                lambda x: x.partner_id == partner)
            part_cuota_lines = move_lines_cuota.filtered(
                lambda x: x.partner_id == partner)
            line_lst.append({
                'mod296_id': self.id,
                'partner_id': partner.id,
                'domicilio': partner.street,
                'complemento_domicilio': partner.street2,
                'poblacion': partner.city,
                'provincia': partner.state_id,
                'zip': partner.zip,
                'pais': partner.country_id,
                'move_line_ids': part_base_lines + part_cuota_lines,
                'base_retenciones_ingresos': sum([x.tax_amount for x in
                                                  part_base_lines]),
                'retenciones_ingresos': sum([x.tax_amount for x in
                                             part_cuota_lines])
            })
        self.lines296 = line_lst
        self.casilla_01 = len(partner_lst)
        self.casilla_02 = sum([x.tax_amount for x in move_lines_base])
        self.casilla_03 = sum([x.tax_amount for x in move_lines_cuota])


class L10nEsAeatMod296ReportLine(models.Model):
    _description = 'AEAT 296 report line'
    _name = 'l10n.es.aeat.mod296.report.line'

    mod296_id = fields.Many2one('l10n.es.aeat.mod296.report', string='Mod 296')
    partner_id = fields.Many2one('res.partner', string='Partner')
    move_line_ids = fields.Many2many('account.move.line', string='Move Lines')
    base_retenciones_ingresos = fields.Float(string='Base retenciones e '
                                             'ingresos a cuenta')
    porcentaje_retencion = fields.Float(string='% retención')
    retenciones_ingresos = fields.Float(string='Retenciones e ingresos a '
                                        'cuenta')
    fisica_juridica = fields.Selection([('F', 'Persona fisica'),
                                        ('J', 'Persona Juridica o entidad')],
                                       string='F/J')
    naturaleza = fields.Selection([('D', 'Renta dineraria'),
                                   ('E', 'Renta en especie')],
                                  string='Naturaleza')
    fecha_devengo = fields.Date(string='Fecha devengo')
    clave = fields.Selection(
        [('1', '1 - Dividendos y otras rentas derivadas de la participación '
          'en fondos propios de entidades.'),
         ('2', '2 - Intereses y otras rentas derivadas de la cesión a terceros'
          ' de capitales propios.'),
         ('3', '3 - Cánones derivados de patentes, marcas de fábrica o de '
          'comercio, dibujos o meodelos, planos, fórmulas o procedimientos '
          'secretos.'),
         ('4', '4 - Cánones derivados de derechos sobre obras literarias y '
          'artísticas.'),
         ('5', '5 - Cánones derivados de derechos sobre obras científicas.'),
         ('6', '6 - Cánones derivados de derechos sobre películas '
          'cinematográficas y obras sonoras o visuales grabadas.'),
         ('7', '7 - Cánones derivados de informaciones relativas a '
          'experiencias industriales, comerciales o científicas (know-how).'),
         ('8', '8 - Cánones derivados de derechos sobre programas '
          'informáticos.'),
         ('9', '9 - Cánones derivados de derechos personales susceptibles de '
          'cesión, tales como los derechos de imagen.'),
         ('10', '10 - Cánones derivados de equipos industriales, comerciales '
          'o científicos.'),
         ('11', '11 - Otros cánones no relacionados anteriormente.'),
         ('12', '12 - Rendimientos de capital mobiliario de operaciones de '
          'capitalización y de contratos de seguros de vida o invalidez.'),
         ('13', '13 - Otros rendimientos de capital mobiliario no citados '
          'anteriormente.'),
         ('14', '14 - Rendimientos de bienes inmuebles.'),
         ('15', '15 - Rendimientos de actividades empresariales.'),
         ('16', '16 - Rentas derivadas de prestaciones de asistencia técnica.'
          ), ('17', '17 - Rentas de actividades artísticas.'),
         ('18', '18 - Rentas de actividades deportivas.'),
         ('19', '19 - Rentas de actividades profesionales.'),
         ('20', '20 - Rentas del trabajo.'),
         ('21', '21 - Pensiones y haberes pasivos.'),
         ('22', '22 - Retribuciones de administradores y miembros de consejos '
          'de Administración.'),
         ('23', '23 - Rendimientos derivados de operaciones de reaseguros.'),
         ('24', '24 - Entidades de navegación marítima o aérea.'),
         ('25', '25 - Otras rentas')], string='Clave')
    subclave = fields.Selection(
        [('1', '1 - Retención practicada a los tipos generales o escalas de '
          'tributación del artículo 25 del texto refundido de la Ley del '
          'Impuesto sobre la Renta de no Residentes.'),
         ('2', '2 - Retención practicada aplicando límites de imposición de '
          'Convenios.'),
         ('3', '3 - Exención interna (principalmente: artículo 14 del texto '
          'refundido de la Ley del Impuesto sobre la Renta de no Residentes)'),
         ('4', '4 - Exención por aplicación de un Convenio.'),
         ('5', '5 - Sin retención por previo pago del Impuesto por el '
          'contribuyente o su representante.'),
         ('6', '6 - El perceptor declarado es una entidad extranjera de '
          'gestión colectiva de derechos de la propiedad intelectual, '
          'habiéndose practicado retención aplicando el límite de imposición, '
          'o la exención, de un Convenio.'),
         ('7', '7 - El perceptor es un contribuyente del Impuesto sobre la '
          'Renta de las Personas Físicas del régimen especial aplicable a los '
          'trabajadores desplazados a territorio español.'),
         ('8', '8 - El perceptor declarado es una entidad residente en el '
          'extranjero comercializadora de acciones o participaciones de '
          'instituciones de inversión colectiva españolas, habiéndose '
          'practicado retención aplicando un límite de imposición fijado en '
          'el Convenio inferior.'),
         ('9', '9 - El perceptor declarado es una entidad residente en el '
          'extranjero comercializadora de acciones o participaciones de '
          'instituciones de inversión colectiva españoas, habiéndose '
          'practicado retención aplicando el tipo de gravamen.')],
        string='Subclave')
    mediador = fields.Boolean(string='Mediador')
    codigo = fields.Selection(
        [('1', '1. El código emisor corresponde a un N.I.F.'),
         ('2', '2. El código emisor corresponde a un código I.S.I.N.'),
         ('3', '3. El código emisor corresponde a valores extranjeros que no '
          'tienen asignado I.S.I.N., cuyo emisor no dispone de NIF')],
        string='Código')
    codigo_emisor = fields.Char(string='Código emisor', size=12)
    pago = fields.Selection([('1', 'Como emisor'),
                             ('2', 'Como mediador')], string='Pago')
    tipo_codigo = fields.Selection([('C', 'Identificación con el Código Cuenta'
                                     ' Valores (C.C.V.)'),
                                    ('O', 'Otra identificación')],
                                   string='Tipo código')
    cuenta_valores = fields.Many2one('res.partner.bank',
                                     string='Código Cuenta Valores')
    pendiente = fields.Boolean(string='Pendiente')
    ejercicio_devengo = fields.Many2one('account.fiscalyear',
                                        string='Ejercicio devengo')
    domicilio = fields.Char(string='Domicilio', size=50)
    complemento_domicilio = fields.Char(string='Complemento del domicilio',
                                        size=40)
    poblacion = fields.Char(string='Problación/Ciudad', size=30)
    provincia = fields.Many2one('res.country.state',
                                string='Provincia/Región/Estado')
    zip = fields.Char(string='Código postal', size=10)
    pais = fields.Many2one('res.country', string='Pais')
    nif_pais_residencia = fields.Char(string='Nif en el país de residencia',
                                      size=20)
    fecha_nacimiento = fields.Date(string='Fecha de nacimiento')
    ciudad_nacimiento = fields.Char(string='Ciudad nacimiento', size=35)
    pais_nacimiento = fields.Many2one('res.country', string='Pais nacimiento')
    pais_residencia_fiscal = fields.Many2one('res.country', string='Pais o '
                                             'territorio de residencia fiscal')

    @api.one
    @api.onchange('partner_id')
    def onchange_partner(self):
        if self.partner_id:
            self.domicilio = self.partner_id.street
            self.complemento_domicilio = self.partner_id.street2
            self.poblacion = self.partner_id.city
            self.provincia = self.partner_id.state_id
            self.zip = self.partner_id.zip
            self.pais = self.partner_id.country_id
