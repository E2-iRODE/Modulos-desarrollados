from odoo import models, fields,api






class Reparacion(models.Model):
    _inherit = 'repair.order'
    
    compatible_products = fields.Many2many(
        'product.product',        
        readonly=True,
        compute="_compute_compatible_products"
    )
    user_id=fields.Many2many( 'hr.employee', string='Técnico Responsable')
    seleccion_reparacion = fields.Boolean(string='Es vehiculo', default=True)
    


    #info del vehiculo
    vehiculo_id = fields.Many2one('fleet.vehicle', string='Vehículo')
    modelo_inf=fields.Char(string='Modelo',  readonly=True)
    model_year_inf=fields.Char(string='Año', readonly=True)
    model_color_inf=fields.Char(string='Color',  readonly=True)   
    license_plate_inf=fields.Char(string='Placa', readonly=True)

    #info del producto
    #product_id ya existe en el modelo repair.order
    modelo_inf_prod=fields.Char(string='Modelo',  readonly=True)
    marca_inf=fields.Char(string='Marca',  readonly=True)
    linea_inf=fields.Char(string='Linea',  readonly=True)

    @api.onchange('vehiculo_id')
    def _onchange_vehiculo_id(self):
        if self.vehiculo_id:
            info=self.env['fleet.vehicle'].search([('id','=',self.vehiculo_id.id)])
            self.modelo_inf=info.model_id.name
            self.license_plate_inf=info.license_plate
            self.model_year_inf=info.model_year
            self.model_color_inf=info.color

            
            self.product_id=''
            self.modelo_inf_prod=''
            self.marca_inf=''
            self.linea_inf=''
        

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            info= self.env['product.template'].search([
            ('name', '=', self.product_id.name)
                                                ])
            self.modelo_inf_prod=info.modelo_id.name
            self.marca_inf=info.marca_id.name
            self.linea_inf=info.linea_id.name

            self.vehiculo_id=''
            self.modelo_inf=''
            self.license_plate_inf=''
            self.model_year_inf=''
            self.model_color_inf=''

       


    @api.depends("vehiculo_id","product_id")
    def _compute_compatible_products(self):
        for rec in self:
            productos = self.env['product.product']

            if rec.vehiculo_id:

                modelo = rec.vehiculo_id.model_id

                productos = self.env['product.product'].search([
                    ('product_tmpl_id.compatible_vehiculo', 'in', modelo.id)
                ])
            if rec.product_id:
                productos = self.env['product.product'].search([
                    ('product_tmpl_id.compatible', 'in', rec.product_id.id)
                ])
                

            rec.compatible_products = productos