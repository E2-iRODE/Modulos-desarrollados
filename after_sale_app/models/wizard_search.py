from odoo import models, fields, api


class WizardSearchOrderLine(models.TransientModel):
    """Fila liviana para mostrar órdenes sin disparar computes de sale.order."""
    _name = 'wizard.search.order.line'
    _description = 'Fila de orden en wizard búsqueda'

    wizard_id    = fields.Many2one('wizard.search.order', ondelete='cascade')
    order_id     = fields.Many2one('sale.order', string='Orden')
    name         = fields.Char(string='Referencia')
    partner_name = fields.Char(string='Cliente')
    date_order   = fields.Datetime(string='Fecha')
    state        = fields.Selection([
        ('draft',  'Cotizacion'),
        ('sent',   'Cotizacion Enviada'),
        ('sale',   'Orden confirmada'),
        ('cancel', 'Cancelado'),
    ], string='Estado de la orden')
    invoice_status = fields.Selection([
        ('upselling', 'Oportunidad de venta adicional'),
        ('invoiced',  'Totalmente facturado'),
        ('to invoice','Para facturar'),
        ('no',        'Nada que facturar'),
    ], string='Estado de facturación')
    delivery_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('started', 'Iniciada'),
        ('partial', 'Parcial'),
        ('full',    'Completamente Entregado'),
        ('no',      'Sin entregas'),
    ], string='Estado de entrega')
    currency_id  = fields.Many2one('res.currency')
    amount_total = fields.Float(string='Total')

    def action_select_line(self):
        self.ensure_one()
        after_sale = self.wizard_id.after_sale_id
        if not after_sale:
            raise models.ValidationError('No se encontró el seguimiento.')
        vals = {'order_id': self.order_id.id}
        if not after_sale.partner_id:
            vals['partner_id'] = self.order_id.partner_id.id
        after_sale.write(vals)
        return {'type': 'ir.actions.act_window_close'}


class WizardSearchOrder(models.TransientModel):
    _name = 'wizard.search.order'
    _description = 'Buscar Orden de Venta por Cliente'

    after_sale_id = fields.Many2one('after.sale', string='Seguimiento', readonly=True)
    partner_id    = fields.Many2one('res.partner', string='Cliente', readonly=True, required=True)

    date_from             = fields.Date(string='Fecha desde')
    date_to               = fields.Date(string='Fecha hasta')
    state_filter          = fields.Selection([
        ('draft',  'Cotizacion'),
        ('sent',   'Cotizacion Enviada'),
        ('sale',   'Orden confirmada'),
        ('cancel', 'Cancelado'),
    ], string='Estado de la orden')
    invoice_status_filter = fields.Selection([
        ('upselling', 'Oportunidad de venta adicional'),
        ('invoiced',  'Totalmente facturado'),
        ('to invoice','Para facturar'),
        ('no',        'Nada que facturar'),
    ], string='Estado de facturación')
    delivery_status_filter = fields.Selection([
        ('pending', 'Pendiente'),
        ('started', 'Iniciada'),
        ('partial', 'Parcial'),
        ('full',    'Completamente Entregado'),
        ('no',      'Sin entregas'),
    ], string='Estado de entrega')
    amount_min = fields.Float(string='Total mínimo')
    amount_max = fields.Float(string='Total máximo')
    product_filter_ids = fields.Many2many(
        'product.product',
        'wizard_search_order_product_rel',
        'wizard_id', 'product_id',
        string='Productos',
    )
    line_ids = fields.One2many('wizard.search.order.line', 'wizard_id', string='Órdenes')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ctx = self.env.context
        if ctx.get('default_after_sale_id'):
            res['after_sale_id'] = ctx['default_after_sale_id']
        if ctx.get('default_partner_id'):
            res['partner_id'] = ctx['default_partner_id']
        return res

    def _build_domain(self):
        """Construye el domain ORM según los filtros activos."""
        domain = [('partner_id', '=', self.partner_id.id)]

        if self.date_from:
            domain += [('date_order', '>=', fields.Datetime.from_string(
                str(self.date_from) + ' 00:00:00'))]
        if self.date_to:
            domain += [('date_order', '<=', fields.Datetime.from_string(
                str(self.date_to) + ' 23:59:59'))]
        if self.state_filter:
            domain += [('state', '=', self.state_filter)]
        if self.invoice_status_filter:
            domain += [('invoice_status', '=', self.invoice_status_filter)]

        
        if self.delivery_status_filter:
            if self.delivery_status_filter == 'no':
                domain += [('delivery_status', 'in', ['no', False])]
            else:
                domain += [('delivery_status', '=', self.delivery_status_filter)]

        if self.amount_min:
            domain += [('amount_total', '>=', self.amount_min)]
        if self.amount_max:
            domain += [('amount_total', '<=', self.amount_max)]
        if self.product_filter_ids:
            domain += [('order_line.product_id', 'in', self.product_filter_ids.ids)]

        return domain

    def _load_lines(self):
        """Carga line_ids usando ORM."""
        domain = self._build_domain()
        orders = self.env['sale.order'].search(domain, order='date_order desc')

        self.line_ids.unlink()
        self.env['wizard.search.order.line'].create([{
            'wizard_id':        self.id,
            'order_id':         o.id,
            'name':             o.name,
            'partner_name':     o.partner_id.name,
            'date_order':       o.date_order,
            'state':            o.state,
            'invoice_status':   o.invoice_status,
            'delivery_status':  o.delivery_status or 'no',
            'currency_id':      o.currency_id.id,
            'amount_total':     o.amount_total,
        } for o in orders])

    def action_open(self):
        self.ensure_one()
        self._load_lines()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_apply_filters(self):
        self.ensure_one()
        self._load_lines()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_clear_filters(self):
        self.ensure_one()
        self.write({
            'date_from': False,
            'date_to': False,
            'state_filter': False,
            'invoice_status_filter': False,
            'delivery_status_filter': False,
            'amount_min': 0.0,
            'amount_max': 0.0,
            'product_filter_ids': [(5, 0, 0)],
        })
        self._load_lines()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }