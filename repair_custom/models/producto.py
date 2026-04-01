from odoo import models, fields, api







class Producto(models.Model):
    _inherit = 'product.template'

    modelo_id = fields.Many2one('product.model', string='Modelo')
    marca_id = fields.Many2one('product.marca', string='Marca')
    linea_id = fields.Many2one('product.linea', string='Línea')
    compatible=fields.Many2many('product.product', string='Compatibilidad')
    compatible_vehiculo = fields.Many2many('fleet.vehicle.model', string='Compatibilidad Vehículo')
    es_repuesto = fields.Boolean(string='Es repuesto', default=False)

