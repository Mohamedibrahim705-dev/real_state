from datetime import timedelta 
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

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
    lease_image = fields.Binary(string="Property Image")
    user_id = fields.Many2one('res.users', string='Related User', index=True)
    tenant_id = fields.Many2one(
        'real_estate.tenant',
        string='Tenant',
        required=True,
        ondelete='cascade',
        index=True
    )
    next_electric_recharge = fields.Date(string='Electricity Bill Date')

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
    maintenance_ids = fields.One2many(
        'maintenance.request',
        'lease_id',
        string='Maintenance Requests',
    )
    tenant_age= fields.Integer(string='Tenant Age', compute='_compute_tenant_age', store=True)
    duration_months = fields.Integer(string='Duration (Months)', compute='_compute_duration', store=True)
    is_active = fields.Boolean(string='Currently Active', compute='_compute_is_active')

    def mark_as_active(self):
        """Mark lease as active"""
        if not self.env.user.has_group('real_estate.group_lease_manager'):
            raise UserError("Only users with the 'Lease Manager' role can edit leases.")
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
    

    def write(self, vals):
       if not self.env.user.has_group('real_estate.group_lease_manager'):
        raise UserError("Only users with the 'Lease Manager' role can edit leases.")
       return super(Lease, self).write(vals)
    
    def unlink(self):
       if not self.env.user.has_group('real_estate.group_lease_manager'):
        raise UserError("Only users with the 'Lease Manager' role can delete leases.")
       return super(Lease, self).unlink()

    def action_open_related_maintenance(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("real_estate.action_maintenance")
        action['views'] = [
            
            (self.env.ref('real_estate.view_maintenance_form').id, 'form'),
        ]
        action['domain'] = [('lease_id', '=', self.id)]
        action['context'] = {
            **self.env.context,
            'default_lease_id': self.id,
        }
        return action
    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        """Calculate lease duration in months"""
        for record in self:
            if record.start_date and record.end_date:
                delta = record.end_date - record.start_date
                record.duration_months = int(delta.days / 30)
            else:
                record.duration_months = 0

    @api.depends('start_date', 'end_date', 'state')
    def _compute_is_active(self):
        """Check if lease is currently active"""
        today = fields.Date.today()
        for record in self:
            if record.state == 'active' and record.start_date and record.end_date:
                record.is_active = record.start_date <= today <= record.end_date
            else:
                record.is_active = False

    @api.depends('tenant_id.date_of_birth')
    def _compute_tenant_age(self):
        """Calculate tenant age based on date of birth"""
        today = fields.Date.today()
        for record in self:
            if record.tenant_id and record.tenant_id.date_of_birth:
                dob = record.tenant_id.date_of_birth
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                record.tenant_age = age
            else:
                record.tenant_age = 0    

    @api.onchange('property_id')
    def _onchange_property_id(self):
        """Set default price when property is selected and validate availability"""
        if self.property_id and not self.property_id.available:
            raise ValidationError("The selected property is not available.")
        if self.property_id and self.property_id.price:
            self.monthly_rent = self.property_id.price 
            self.deposit_paid = self.property_id.price * 0.1 
    

    @api.onchange('start_date')          
    def _onchange_next_electric_recharge(self):
        """Update electricity bill date"""
        if self.start_date :
            self.next_electric_recharge = self.start_date + timedelta(days=30)

    def action_submit_request(self):
        """Create maintenance request and notify manager"""
        self.ensure_one()
        
        # 1. Create maintenance.request record
        maintenance_request = self.env['maintenance.request'].create({
            'property_id': self.property_id.id,
            'lease_id': self.id,
            'issue_type': 'electrical',  # Default issue type for this example
            'description': 'Maintenance request created from lease form.',
            'urgency': 'medium',  # Default urgency for this example
            'preferred_date': self.next_electric_recharge,
            'tenant_phone': self.tenant_id.phone ,
            'state': 'submitted',
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Request Submitted',
                'message': 'Your maintenance request has been submitted successfully and the manager has been notified.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    #calculate total cost of maintenance requests for this lease
    maintenance_ids= fields.One2many(
        'maintenance.request',
        'lease_id',
        string='Maintenance Requests',
    )

    total_cost = fields.Float(compute='_compute_total_cost', string='Total Cost')
    plumbing_cost = fields.Float(string='Plumbing Cost')
    electrical_cost = fields.Float(string='Electrical Cost')
    air_condition_cost = fields.Float(string='Air Condition Cost')
    appliance_cost = fields.Float(string='Appliance Cost')
    other_cost = fields.Float(string='Other Cost')
   

    @api.depends(
        'plumbing_cost',
        'electrical_cost',
        'air_condition_cost',
        'appliance_cost',
        'other_cost',
    )
    def _compute_total_cost(self):
        for lease in self:
            lease.total_cost = sum((
                lease.plumbing_cost,
                lease.electrical_cost,
                lease.air_condition_cost,
                lease.appliance_cost,
                lease.other_cost,
            ))