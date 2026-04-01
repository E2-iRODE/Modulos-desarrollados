from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    after_sale_count = fields.Integer(compute='_compute_after_sale_count')

    def _compute_after_sale_count(self):
        groups = self.env['after.sale'].read_group(
            [('partner_id', 'in', self.ids)],
            ['partner_id'],
            ['partner_id'],
        )
        counts = {g['partner_id'][0]: g['partner_id_count'] for g in groups}
        for partner in self:
            partner.after_sale_count = counts.get(partner.id, 0)

    def action_view_after_sales(self):
        self.ensure_one()
        return {
            'name': 'Seguimientos Post-Venta',
            'type': 'ir.actions.act_window',
            'res_model': 'after.sale',
            'view_mode': 'tree,form,kanban',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
            'target': 'current',
        }
