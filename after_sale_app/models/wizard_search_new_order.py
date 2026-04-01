from odoo import models, fields, api


class WizardOrderLine(models.TransientModel):
    _name = 'wizard.order.line'
    _description = 'Fila de orden en wizard'

    wizard_id    = fields.Many2one('wizard.search.order.nueva', ondelete='cascade')
    order_id     = fields.Many2one('sale.order', string='Orden')
    name         = fields.Char(string='Referencia')
    partner_name = fields.Char(string='Cliente')
    date_order   = fields.Datetime(string='Fecha')
    state        = fields.Selection([
        ('draft',  'Presupuesto'),
        ('sent',   'Enviado'),
        ('sale',   'Confirmada'),
        ('done',   'Bloqueado'),
        ('cancel', 'Cancelado'),
    ])
    invoice_status = fields.Selection([
        ('upselling', 'Oportunidad de venta adicional'),
        ('invoiced',  'Totalmente facturado'),
        ('to invoice','Para facturar'),
        ('no',        'Nada que facturar'),
    ])
    delivery_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('started', 'Iniciada'),
        ('partial', 'Parcial'),
        ('full',    'Completamente Entregado'),
        ('no',      'Sin entregas'),
    ])
    currency_id  = fields.Many2one('res.currency')
    amount_total = fields.Float(string='Total')

    def action_select_line(self):
        self.ensure_one()
        after_sale = self.wizard_id.after_sale_id
        if not after_sale:
            raise models.ValidationError('No se encontró el seguimiento.')
        after_sale.write({'order_nueva': [(4, self.order_id.id)]})
        return {'type': 'ir.actions.act_window_close'}


class WizardSearchOrderNueva(models.TransientModel):
    _name = 'wizard.search.order.nueva'
    _description = 'Agregar Orden a order_nueva'

    after_sale_id = fields.Many2one('after.sale', readonly=True)

    
    partner_filter         = fields.Many2one('res.partner', string='Cliente')
    date_from              = fields.Date(string='Fecha desde')
    date_to                = fields.Date(string='Fecha hasta')
    state_filter           = fields.Selection([
        ('draft',  'Cotizacion'),
        ('sent',   'Cotizacion Enviada'),
        ('sale',   'Orden confirmada'),
        ('cancel', 'Cancelado'),
    ], string='Estado de la orden')
    invoice_status_filter  = fields.Selection([
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
    amount_min             = fields.Float(string='Total mínimo')
    amount_max             = fields.Float(string='Total máximo')
    product_filter_ids     = fields.Many2many(
        'product.product',
        'wizard_search_order_nueva_product_rel',
        'wizard_id', 'product_id',
        string='Productos',
    )

    line_ids = fields.One2many('wizard.order.line', 'wizard_id', string='Resultados')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('default_after_sale_id'):
            res['after_sale_id'] = self.env.context['default_after_sale_id']
        return res

    def _build_domain(self):
        """Construye el domain ORM con todos los filtros activos."""
        domain = []

        # Búsqueda global 
        if self.partner_filter:
            domain += [('partner_id', '=', self.partner_filter.id)]

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
        """Carga line_ids usando ORM — búsqueda global sin límite de cliente."""
        domain = self._build_domain()
        orders = self.env['sale.order'].search(domain, order='date_order desc', limit=300)

        self.line_ids.unlink()
        self.env['wizard.order.line'].create([{
            'wizard_id':       self.id,
            'order_id':        o.id,
            'name':            o.name,
            'partner_name':    o.partner_id.name,
            'date_order':      o.date_order,
            'state':           o.state,
            'invoice_status':  o.invoice_status,
            'delivery_status': o.delivery_status or 'no',
            'currency_id':     o.currency_id.id,
            'amount_total':    o.amount_total,
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
            'partner_filter':         False,
            'date_from':              False,
            'date_to':                False,
            'state_filter':           False,
            'invoice_status_filter':  False,
            'delivery_status_filter': False,
            'amount_min':             0.0,
            'amount_max':             0.0,
            'product_filter_ids':     [(5, 0, 0)],
        })
        self._load_lines()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }