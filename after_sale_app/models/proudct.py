


from odoo import models,fields,api
from odoo.exceptions import UserError



class ProductProduct(models.Model):
    _inherit = "product.product"




    def action_quick_add(self):
        active_id = self.env.context.get('active_id')
        after_sale = self.env['after.sale'].browse(active_id)

        if not after_sale.partner_id:
            raise UserError("Selecciona un cliente primero.")

        order = after_sale.order_nueva.filtered(lambda o: o.state == 'draft')[:1]
        
        if not order:
            order = self.env['sale.order'].create({
                'partner_id': after_sale.partner_id.id,
                'after_sale_id': after_sale.id,
                'origin': after_sale.name,
            })

        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.id,
            'product_uom_qty': 1,
            'price_unit': self.lst_price,
        })

        # En lugar de solo la notificación, devolvemos una acción que mantiene la ventana abierta
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '¡Añadido!',
                'message': f'{self.name} se agregó a {order.name}',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'} # Opcional: quitar si quieres que siga abierta
            }
        }