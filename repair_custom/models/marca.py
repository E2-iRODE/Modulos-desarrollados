


from odoo import models, fields,api





class Marca(models.Model):
    _name = 'product.marca'
    _description = 'Marca de producto'

    name = fields.Char(string="Nombre de la marca", required=True)