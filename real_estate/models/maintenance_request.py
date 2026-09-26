from odoo import models, fields, api
from datetime import timedelta

class MaintenanceRequest(models.Model):
    _name = 'maintenance.request'
    _description = 'Property Maintenance Request'
     # _inherit = ['mail.thread', 'mail.activity.mixin']
     
    name = fields.Char()
    lease_id = fields.Many2one('real_estate.lease')
    assigned_to = fields.Many2one(
        'res.users',
        string='Assigned To',
        default=lambda self: self.env.user,
        index=True,
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted')
    ], string="State", default='draft')
    tenant_phone = fields.Char(string="Tenant Phone")
    preferred_date = fields.Date(string="Preferred Date")
    tenant_id = fields.Many2one(related='lease_id.tenant_id', store=True)
    property_id = fields.Many2one(related='lease_id.property_id', store=True)
    assigned_to = fields.Many2one('res.users', string='Assigned To')
    issue_type = fields.Selection([
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('air_condition', 'Air Condition'),
        ('appliance', 'Appliance'),
        ('other', 'Other')
    ], required=True)
    description = fields.Text(required=True, tracking=True)
    urgency = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('emergency', 'Emergency')
    ], default='medium', required=True)
    scheduled_date = fields.Date()
    completion_date = fields.Date()
    actual_cost = fields.Float()

    def _cron_auto_high_energency_schdual_tomorrow(self):
        """Cron job to handle high/emergency maintenance requests scheduled for tomorrow.
        Finds requests with high or emergency urgency scheduled for tomorrow and
        can trigger notifications, change state, or create activities."""
        tomorrow = fields.Date.today() + timedelta(days=1)
        
        high_urgency_requests = self.search([
            ('urgency', 'in', ['high', 'emergency']),
            ('scheduled_date', '=', tomorrow),
            ('state', 'in', ['draft', 'in_progress']),
        ])
        
        for request in high_urgency_requests:
            if request.assigned_to:
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'note': f'High/Emergency maintenance request "{request.name}" scheduled for tomorrow ({tomorrow}). Please prepare.',
                    'res_id': request.id,
                    'res_model_id': self.env.ref('real_estate.model_maintenance_request').id,
                    'user_id': request.assigned_to.id,
                    'date_deadline': tomorrow,
                })
            
            if request.tenant_id:
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'note': f'Reminder: Your high/emergency maintenance request "{request.name}" is scheduled for tomorrow ({tomorrow}).',
                    'res_id': request.id,
                    'res_model_id': self.env.ref('real_estate.model_maintenance_request').id,
                    'user_id': request.tenant_id.user_id.id if request.tenant_id.user_id else self.env.user.id,
                    'date_deadline': tomorrow,
                })
        
        return True
    
    def send_reminder_email(self):
     template_xml_id = "real_estate.email_template_maintenance"
     if not template_xml_id:
        return

     template = self.env.ref(template_xml_id, raise_if_not_found=False)
     if not template:
        return

     for main in self:
        if not main.assigned_to.email:
            main.message_post(
                body="Could not send reminder: Assigned user has no email."
            )
            continue
        template.send_mail(main.id, force_send=True)

    def _cron_auto_send_email_reminder_main(self):
     next_email = self.search(
        [
            ("scheduled_date", "=", fields.Date.today() + timedelta(days=1)),
        ]
    )
     for main in next_email:
        main.send_reminder_email()
