import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


INSTALLMENT_FEE_CATEGORY = 'Cuotas'


class SaleOrderInstallmentTerm(models.Model):
    _inherit = 'sale.order'

    installment_term_id = fields.Many2one(
        comodel_name='pos.payment.installment.term',
        string='Plan de cuotas',
        ondelete='set null',
        
        help='Al seleccionar un plan, el precio de cualquier linea cuya '
             'categoria de producto sea "Cuotas" se calcula automaticamente.',
    )
    installment_count = fields.Integer(
        string='Numero de cuotas',
        compute='_compute_installment_info',
        store=False,
    )
    installment_surcharge = fields.Float(
        string='Recargo (%)',
        compute='_compute_installment_info',
        store=False,
        digits=(16, 2),
    )
    installment_name= fields.Char(
        string='Nombre del plan de cuotas',
        compute='_compute_installment_info',
        store=False,
    )

    payment_method_id = fields.Many2one(
    'pos.payment.method',
    string='Metodo de pago POS'
)


    @api.depends('installment_term_id')
    def _compute_installment_name(self):
        pass

    @api.depends('installment_term_id')
    def _compute_installment_info(self):
        for order in self:
            try:
                if order.installment_term_id:
                    order.installment_count    = order.installment_term_id.installments or 0
                    order.installment_surcharge = order.installment_term_id.surcharge_percent or 0.0
                    order.installment_name = order.installment_term_id.payment_method_id.name
                else:
                    order.installment_count    = 0
                    order.installment_surcharge = 0.0
                    order.installment_name = order.installment_term_id.payment_method_id.name if order.installment_term_id else ''

            except Exception as e:
                _logger.warning('_compute_installment_info [%s]: %s', order.id, e)
                order.installment_count    = 0
                order.installment_surcharge = 0.0
                order.installment_name = order.installment_term_id.payment_method_id.name if order.installment_term_id else ''

    @api.onchange('installment_term_id', 'order_line')
    def _onchange_installment_term_update_fee(self):
        for order in self:
            try:
                fee_lines = [l for l in (order.order_line or []) if _is_fee_line(l)]

                if not order.installment_term_id:
                    for line in fee_lines:
                        try:
                            line.price_unit = 0.0
                        except Exception as e:
                            _logger.warning('reset price_unit: %s', e)
                    continue

                surcharge_pct = order.installment_term_id.surcharge_percent or 0.0
                if surcharge_pct <= 0:
                    continue

                base = 0.0
                for line in (order.order_line or []):
                    try:
                        if not _is_fee_line(line) and not line.display_type:
                            base += line.price_subtotal or 0.0
                    except Exception as e:
                        _logger.warning(' base sum: %s', e)

                fee_amount = round(base * surcharge_pct / 100.0, 2)
                _logger.info('fee_amount=%.2f (base=%.2f pct=%.2f)', fee_amount, base, surcharge_pct)

                for line in fee_lines:
                    try:
                        line.price_unit = fee_amount
                    except Exception as e:
                        _logger.warning('set price_unit: %s', e)

            except Exception as e:
                _logger.error(' _onchange [%s]: %s', order.id, e)


def _is_fee_line(line):
    """
    True si el producto de la linea pertenece a la categoria 'Cuotas'
    o a cualquier subcategoria de ella.
    La deteccion es por CATEGORIA, no por nombre de producto,
    lo que permite variantes: Gastos Admin, Gastos Admin Extendidos, etc.
    """
    try:
        
        if not line:
            return False
        if not line.product_id or not line.product_id.id:
            return False
        if line.display_type:          
            return False

        
        categ = line.product_id.categ_id
        if not categ or not categ.id:
            return False

       
        visited = set()
        while categ and categ.id and categ.id not in visited:
            visited.add(categ.id)
            if (categ.name or '').strip() == INSTALLMENT_FEE_CATEGORY:
                return True
            parent = categ.parent_id
            categ = parent if (parent and parent.id) else None

        return False

    except Exception as e:
        _logger.warning('null _is_fee_line: %s', e)
        return False
