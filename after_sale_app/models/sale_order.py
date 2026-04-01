from odoo import models,fields,api
from odoo.exceptions import ValidationError





class SaleOrder(models.Model):
    _inherit = 'sale.order'

    
    after_sale_id = fields.Many2one('after.sale', string="Origen Post-Venta")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.after_sale_id:
                record.after_sale_id.write({
                    'order_nueva': [(4, record.id)]
                })
        return records