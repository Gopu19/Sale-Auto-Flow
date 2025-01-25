from odoo import api, fields, models
from odoo.exceptions import ValidationError,UserError
from duplicity.errors import UserError


class SaleOrder(models.Model):
    _inherit="sale.order"
    
    
    manager_reference=fields.Text(string="Manager Reference")
    can_edit_manager_reference=fields.Boolean(string="can_edit_manager_reference",compute="_compute_can_edit_manager_reference",store= False)
    auto_workflow=fields.Boolean(string="Auto Workflow")
    
    
    
    @api.depends('manager_reference')
    def _compute_can_edit_manager_reference(self):
        for record in self:
            record.can_edit_manager_reference=self.env.user.has_group('sale_auto_flow.group_sale_admin')
            
 
  

    def action_confirm(self):
        res = super().action_confirm()
        config_param = self.env['ir.config_parameter'].sudo()
        sale_order_limit = float(config_param.get_param('sale.sale_order_limit', 0.0))
    
        for order in self:
            if order.amount_total > sale_order_limit:
                is_sale_admin = self.env.user.has_group('sale_auto_flow.group_sale_admin')
                if not is_sale_admin:
                    raise ValidationError(
                        "Only users with the Sale Admin role can confirm this order."
                    )
    
            if order.auto_workflow:
                product_groups={}
                for line in order.order_line:
                    key = (
                        line.product_id.id,
                        order.warehouse_id.id,
                        order.partner_shipping_id.id
                    )
                    if key not in product_groups:
                        product_groups[key] = []
                    product_groups[key].append(line)
    
                for key, lines in product_groups.items():
                    total_qty_by_product = {}
                    for line in lines:
                        if line.product_id not in total_qty_by_product:
                            total_qty_by_product[line.product_id] = 0
                        total_qty_by_product[line.product_id] += line.product_uom_qty
    
                    picking=self.env['stock.picking'].create({
                        'picking_type_id': order.warehouse_id.out_type_id.id,
                        'partner_id': order.partner_id.id,
                        'origin': order.name,
                        'location_id': order.warehouse_id.lot_stock_id.id,
                        'location_dest_id': order.partner_shipping_id.property_stock_customer.id
                    })
    
                    for product, total_qty in total_qty_by_product.items():
                        self.env['stock.move'].create({
                            'name': product.name,
                            'product_id': product.id,
                            'product_uom_qty': total_qty,
                            'product_uom': product.uom_id.id,
                            'picking_id': picking.id,
                            'location_id': order.warehouse_id.lot_stock_id.id,
                            'location_dest_id': order.partner_shipping_id.property_stock_customer.id
                        })
    
                    picking.action_confirm()
                    picking.action_assign()
                    picking.button_validate()
    
              
                invoice=order._create_invoices()
                invoice.action_post()
    
                journal=self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
                if journal:
                    payment=self.env['account.payment'].create({
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'partner_id': order.partner_id.id,
                        'amount': invoice.amount_total,
                        'journal_id': journal.id,
                        'ref': invoice.name,
                    })
                    payment.action_post()
    
                    payment_wizard=self.env['account.payment.register'].with_context(
                        active_model='account.move',
                        active_ids=invoice.ids
                    ).create({
                        'payment_date': fields.Date.today(),
                        'amount': invoice.amount_total,
                        'journal_id': journal.id,
                    })
                    payment_wizard.action_create_payments()
    
        return res

    
    
    
   
    
    


