from odoo import models, fields, api
from odoo.exceptions import UserError

class Lease(models.Model):
    _name = 'real_estate.lease'
    _description = 'Property Lease Agreement'
    
    name = fields.Char(string='Lease Reference', required=True)
    property_id = fields.Many2one(
        'real_estate.property',
        string='Property',
        required=True,
        ondelete='cascade',  # If property deleted, delete lease too
        index=True
    )
    tenant_id = fields.Many2one(
        'real_estate.tenant',
        string='Tenant',
        required=True,
        ondelete='cascade',
        index=True
    )
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    monthly_rent = fields.Float(string='Monthly Rent', required=True)
    deposit_paid = fields.Float(string='Deposit Paid')
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('at_risk', 'At Risk'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True)

    def mark_as_active(self):
        """Mark lease as active"""
        for record in self:
            record.write({'state': 'active'})
            
    def mark_set_back_to_draft(self):
        """Mark lease as draft"""
        for record in self:
            record.write({'state': 'draft'})

    def copy(self, default=None):
        """Prevent duplicating lease records."""
        raise UserError("You cant copy a lease")

    # def copy(self, default=None):
    #     """Old copy behavior kept for reference."""
    #     return super(Lease, self).copy(default=default)

    @api.model
    def create(self, vals):
        """Override create to generate lease reference"""
        vals['name'] = self.env['ir.sequence'].next_by_code('real_estate.lease')
        return super(Lease, self).create(vals)
    
