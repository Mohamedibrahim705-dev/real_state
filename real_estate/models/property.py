from odoo import models, fields, api
from odoo.exceptions import UserError

class Property(models.Model):
    _name = 'real_estate.property'
    _description = 'Real Estate Property'
    
    name = fields.Char(string='Property Name', required=True, index=True)
    description = fields.Text(string='Description')
    price = fields.Float(string='Monthly Rent', required=True) 
    deposit= fields.Float(string='Deposite', required=True)   
    bedrooms = fields.Integer(string='Bedrooms', required=True)
    available = fields.Boolean(string='Available', default=True, index=True)    
    agent_id = fields.Many2one('res.users', string='Sales Person')

    property_image = fields.Binary(string="Property Image")
    lease_ids = fields.One2many(
        'real_estate.lease',
        'property_id',
        string='Leases',
    )
    lease_count = fields.Integer(      #Computed field to count the number of leases associated with the property
        string='Leases',               # result in xml view as "Leases (count)"
        compute='_compute_lease_count',
    )
    property_type = fields.Selection([
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
        ('commercial', 'Commercial'),
    ], string='Property Type', required=True)

    @api.depends('lease_ids')           # Compute the number of leases associated with the property
    def _compute_lease_count(self):
        for record in self:
            record.lease_count = len(record.lease_ids)

    def mark_as_occupied(self):
            """Mark property as no longer available"""
            for record in self:
                record.write({'available': False, 'price': record.price + 1000})
        
    def mark_as_available(self):
            """Mark property as available"""
            for record in self:
                record.write({'available': True})

    def update_description(self):                        
        for record in self:
            record.write({'description' : 'Mohamed Ibrahim'})

    def export_excel(self):                        
        for record in self:
            record.write({'description' : 'Mohamed Ibrahim'})

    def deposit_add(self):
        
        for record in self:
            record.write({'deposit': record.deposit + 1000})

    def add_bedroom(self):
        for record in self:
            record.write({'bedrooms': record.bedrooms + 1})   

    def property_type_as_villa(self):
        for record in self:
            if record.available  == True:
                record.write({'property_type': 'villa'})     

    def set_agent_name(self):
      for record in self:
             if record.agent_id.name:
                record.write({'description': record.agent_id.name + ' '+' is the Agent who is Responsible for Fund And Financials'})
             else:
               record.write({'description': 'No Agent Assigned Yet'}) 

    def set_agent_email(self):
        for record in self:
              if record.agent_id.login:
                 record.write({'description': record.agent_id.login + ' '+' is the email of the Agent who is Responsible for Fund And Financials'})
              else:
                 record.write({'description': 'No Agent Assigned Yet'}) 

    def price_appears_if_available(self):
        for record in self:
            if record.available:
                record.write({ str(record.price) + ' '+'EGP'})
            else:
                record.write({'description': 'This Property is Not Available Now'}) 

    def write(self, vals):
        if 'bedrooms' in vals:
            if vals["available"] == True and vals.get('bedrooms') != self.bedrooms :
                raise UserError("You cannot edit Bedrooms while the property is unavailable.")

        return super(Property, self).write(vals)

    def action_open_related_leases(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("real_estate.action_lease")
        action['views'] = [
            
            (self.env.ref('real_estate.view_lease_form').id, 'form'),
        ]
        action['domain'] = [('property_id', '=', self.id)]
        action['context'] = {
            **self.env.context,
            'default_property_id': self.id,
        }
        return action
    
    
            

   
