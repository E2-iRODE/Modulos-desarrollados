from odoo import models, fields, api







class Modelo(models.Model):
    _name = 'product.model'
    _description = 'Modelo de Vehículo'

    name = fields.Char(string='Nombre del Modelo', required=True)