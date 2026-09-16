from odoo import models, fields, api

class Tenant(models.Model):
    _name = 'real_estate.tenant'
    _description = 'Real Estate Tenant'
    _order = 'name asc'
    
    # === CORE FIELDS ===
    name = fields.Char(string='Tenant Name', required=True, index=True)
    user_id = fields.Many2one('res.users', string='Related User', index=True)
    email = fields.Char(string='Email', required=True, index=True)
    description = fields.Text(string='Description')
    phone = fields.Char(string='Phone Number')
    mobile = fields.Char(string='Mobile Number')
    city = fields.Char(string='City')
    date_joined = fields.Date(string='Date Joined', default=fields.Date.today, readonly=True)
    date_of_birth = fields.Date(string='Date of Birth')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(string='Active', default=True) 
    crm_lead_id = fields.Many2one('crm.lead', string='CRM Lead', ondelete='set null', index=True)
    website = fields.Char(string='Website')
    age_category = fields.Selection([
        ('A', '1-20'),
        ('B', '21-40'),
        ('C', '41-60')],string='Age Category')

    def update_notes(self):
        for record in self:
            record.write({'notes' : record.name})

    def update_Crm_Lead_Notes(self):
            for record in self:
                record.write({'notes' : record.crm_lead_id.name})
    def update_Crm_Lead_website(self):
            for record in self:
                record.write({'notes' : record.crm_lead_id.website}) 
    def crm_change_to_email(self):
                for record in self:
                    if record.crm_lead_id.website:
                        record.write({'notes' : record.crm_lead_id.email_from})
                    else:
                        record.write({'notes' : record.website}) 
                             