from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AfterSale(models.Model):
    _name = "after.sale"
    _description = "seguimiento de ventas"
    _rec_name = 'referencia'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    referencia = fields.Char(string="Numero", required=True, copy=False, readonly=True, index=True, default="Nuevo")
    name = fields.Char(string="Referencia", required=True, default="Nuevo")
    date = fields.Date(default=fields.Date.context_today)
    description = fields.Text(string="Descripción")
    user_id = fields.Many2many('res.users', string="Responsable", default=lambda self: self.env.user)
    notes = fields.Text(string="Notas")
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En seguimiento'),
        ('done', 'Cerrado'),
    ], string="Estado", default='draft', tracking=True, group_expand='_read_group_state')

    order_nueva = fields.Many2many(
        'sale.order',
        'after_sale_order_nueva_rel',
        'after_sale_id',
        'order_id',
        string="Órdenes Relacionadas",
    )
    garantia_ids = fields.Many2many('sr.product.warranty', string="Garantia", compute="_compute_garantias")

    partner_id = fields.Many2one('res.partner', string="Cliente", required=True)
    order_id = fields.Many2one(
        'sale.order', string="Orden de Venta",
        domain="[('partner_id', '=', partner_id)]",
        readonly=True, states={'draft': [('readonly', False)]}
    )
    order_line_ids = fields.One2many(related='order_id.order_line', string="Productos de la orden", readonly=True)
    linea_lote_ids = fields.One2many('after.sale.line.lote', 'after_sale_id', string="Artículos por Lote/Serie")

    order_state    = fields.Selection(related="order_id.state",          string="Estado de la venta",  store=True)
    invoice_status = fields.Selection(related="order_id.invoice_status", string="Estado de factura",   store=True)
    order_total    = fields.Monetary(related="order_id.amount_total",    string="Total de la Venta",   store=True)
    currency_id    = fields.Many2one(related="order_id.currency_id",                                   store=True)
    delivery_status= fields.Selection(related="order_id.delivery_status",string="Estado de Entrega",   store=True)
    date_order     = fields.Datetime(related="order_id.date_order",      string="Fecha de la Orden",   store=False)

    # ── Cambios de estado ─────────────────────────────────────────────
    @api.model
    def _read_group_state(self, states, domain, order):
     return [s[0] for s in self._fields['state'].selection]
    def action_confirm(self):
        self.ensure_one()
        if not self.order_id:
            raise ValidationError('Debes seleccionar una Orden de Venta antes de confirmar.')
        self.write({'state': 'in_progress'})

    def action_cerrar(self):
        self.ensure_one()
        self.write({'state': 'done'})

    def action_restablecer_borrador(self):
        self.ensure_one()
        self.write({'state': 'draft'})

    # ── CRUD ──────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('referencia', 'Nuevo') == 'Nuevo':
                vals['referencia'] = self.env['ir.sequence'].next_by_code('after.sale') or 'Nuevo'
        records = super().create(vals_list)
        records._sync_lineas_lote()
        return records

    def write(self, vals):
        # Validar permisos al cambiar estado
        if 'state' in vals:
            is_manager = self.env.user.has_group('after_sale_app.group_after_sale_manager')
            for record in self:
                # Solo gerente puede restablecer a borrador
                if vals['state'] == 'draft' and record.state != 'draft' and not is_manager:
                    raise ValidationError('Solo un Gerente puede restablecer a Borrador.')
                # Solo gerente puede cerrar
                if vals['state'] == 'done' and not is_manager:
                    raise ValidationError('Solo un Gerente puede cerrar el seguimiento.')

        result = super().write(vals)

        if 'order_id' in vals or 'order_nueva' in vals:
            self._sync_lineas_lote()

        return result

    # ── Sync lotes ────────────────────────────────────────────────────

    def _sync_lineas_lote(self):
        LineLote = self.env['after.sale.line.lote']
        for record in self:
            if not isinstance(record.id, int) or record.id <= 0:
                continue
            LineLote.search([('after_sale_id', '=', record.id)]).unlink()

            if not record.order_id:
                continue

            pickings_done = record.order_id.picking_ids.filtered(
                lambda p: p.state == 'done' and p.picking_type_code == 'outgoing'
            )

            nuevas_filas = []
            for line in record.order_id.order_line:
                if line.product_id.type == 'service':
                    nuevas_filas.append({
                        'after_sale_id': record.id,
                        'sale_line_id':  line.id,
                        'product_id':    line.product_id.id,
                        'lote_nombre':   '',
                        'qty_entregada': 0.0,
                        'qty_ordenada':  line.product_uom_qty,
                        'price_unit':    line.price_unit,
                        'currency_id':   line.currency_id.id,
                    })
                    continue

                if pickings_done:
                    move_lines_lote = self.env['stock.move.line'].search([
                        ('picking_id', 'in', pickings_done.ids),
                        ('move_id.sale_line_id', '=', line.id),
                        ('lot_id', '!=', False),
                        ('quantity', '>', 0),
                    ])

                    if move_lines_lote:
                        lotes_dict = {}
                        for ml in move_lines_lote:
                            lotes_dict[ml.lot_id.name] = lotes_dict.get(ml.lot_id.name, 0.0) + ml.quantity
                        for lote_nombre, qty in lotes_dict.items():
                            nuevas_filas.append({
                                'after_sale_id': record.id,
                                'sale_line_id':  line.id,
                                'product_id':    line.product_id.id,
                                'lote_nombre':   lote_nombre,
                                'qty_entregada': qty,
                                'qty_ordenada':  line.product_uom_qty,
                                'price_unit':    line.price_unit,
                                'currency_id':   line.currency_id.id,
                            })
                    else:
                        ml_sin_lote = self.env['stock.move.line'].search([
                            ('picking_id', 'in', pickings_done.ids),
                            ('move_id.sale_line_id', '=', line.id),
                            ('quantity', '>', 0),
                        ])
                        nuevas_filas.append({
                            'after_sale_id': record.id,
                            'sale_line_id':  line.id,
                            'product_id':    line.product_id.id,
                            'lote_nombre':   'Sin lote',
                            'qty_entregada': sum(ml_sin_lote.mapped('quantity')),
                            'qty_ordenada':  line.product_uom_qty,
                            'price_unit':    line.price_unit,
                            'currency_id':   line.currency_id.id,
                        })
                else:
                    nuevas_filas.append({
                        'after_sale_id': record.id,
                        'sale_line_id':  line.id,
                        'product_id':    line.product_id.id,
                        'lote_nombre':   '',
                        'qty_entregada': 0.0,
                        'qty_ordenada':  line.product_uom_qty,
                        'price_unit':    line.price_unit,
                        'currency_id':   line.currency_id.id,
                    })

            if nuevas_filas:
                LineLote.create(nuevas_filas)

    def action_refresh_lotes(self):
        self._sync_lineas_lote()

    # ── Otras acciones ────────────────────────────────────────────────

    def action_new_sale_order_inline(self):
        self.ensure_one()
        return {
            'name': 'Crear Orden de Venta',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_origin': self.name,
                'default_after_sale_id': self.id,
            }
        }

    def action_open_catalog(self):
        self.ensure_one()
        try:
            productos_en_orden = self.order_id.order_line.mapped('product_id')
            dominio_compatibles = [('compatible', 'in', productos_en_orden.ids)]
            return {
                'name': 'Seleccionar Productos',
                'type': 'ir.actions.act_window',
                'res_model': 'product.product',
                'view_mode': 'kanban',
                'views': [(self.env.ref('after_sale_app.product_view_kanban_catalog_standalone').id, 'kanban')],
                'domain': dominio_compatibles,
                'context': {'active_id': self.id, 'default_sale_ok': True},
            }
        except ValueError:
            raise ValidationError("Módulo de productos compatibles no instalado.")

    def action_open_catalog_servicios(self):
        self.ensure_one()
        try:
            productos_en_orden = self.order_id.order_line.mapped('product_id')
            dominio_compatibles = [('compatible', 'in', productos_en_orden.ids)]
            return {
                'name': 'Seleccionar Productos',
                'type': 'ir.actions.act_window',
                'res_model': 'product.product',
                'view_mode': 'kanban',
                'views': [(self.env.ref('after_sale_app.product_view_kanban_catalog_standalone').id, 'kanban')],
                'domain': dominio_compatibles,
                'context': {'active_id': self.id, 'default_sale_ok': True},
            }
        except ValueError:
            raise ValidationError("Módulo de productos compatibles no instalado.")

    def action_open_search_order_wizard(self):
        self.ensure_one()
        wizard = self.env['wizard.search.order'].create({
            'after_sale_id': self.id,
            'partner_id': self.partner_id.id,
        })
        return wizard.action_open()

    def action_wizard_search_order_nueva(self):
        self.ensure_one()
        wizard = self.env['wizard.search.order.nueva'].create({
            'after_sale_id': self.id,
        })
        return wizard.action_open()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    stock_actual = fields.Float(
        string="Stock Real",
        compute="_compute_stock_actual",
        store=False,
        readonly=True,
    )

    @api.depends('product_id')
    def _compute_stock_actual(self):
        for line in self:
            if line.product_id and line.product_id.type == 'product':
                line.stock_actual = line.product_id.qty_available
            else:
                line.stock_actual = 0.0