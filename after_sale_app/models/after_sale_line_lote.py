from odoo import models, fields, api


class AfterSaleLineLote(models.Model):

    _name = 'after.sale.line.lote'
    _description = 'Línea de artículo por lote/serie'
    _order = 'after_sale_id, product_id, lote_nombre'

    after_sale_id = fields.Many2one(
        'after.sale',
        string="Seguimiento",
        required=True,
        ondelete='cascade',
    )
    sale_line_id = fields.Many2one(
        'sale.order.line',
        string="Línea de venta",
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product',
        string="Producto",
        readonly=True,
    )
    lote_nombre = fields.Char(string="Lote / Serie", readonly=True)
    qty_entregada = fields.Float(string="Cant. Entregada", readonly=True, digits=(16, 2))
    qty_ordenada = fields.Float(string="Cant. Ordenada", readonly=True, digits=(16, 2))
    price_unit = fields.Float(string="Precio Unit.", readonly=True, digits=(16, 2))
    currency_id = fields.Many2one('res.currency', string="Moneda", readonly=True)
    stock_actual = fields.Float(
        string="Stock Real",
        compute="_compute_stock_actual",
        store=False,
        readonly=True,
    )

    @api.depends('product_id')
    def _compute_stock_actual(self):
        for rec in self:
            if rec.product_id and rec.product_id.type == 'product':
                rec.stock_actual = rec.product_id.qty_available
            else:
                rec.stock_actual = 0.0
