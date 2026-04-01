from odoo import models,fields,api
from odoo.exceptions import ValidationError





class SaleOrder(models.Model):
    _inherit = 'sale.order'

    
    after_sale_id = fields.Many2one('after.sale', string="Origen Post-Venta")

  