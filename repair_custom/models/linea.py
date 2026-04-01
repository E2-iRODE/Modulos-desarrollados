
from odoo import models, fields, api






class Linea(models.Model):
    _name = 'product.linea'
    _description = 'Línea de Producto'

    name = fields.Char(string='Nombre de la Línea', required=True)