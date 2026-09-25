
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class RealEstatePortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(RealEstatePortal, self)._prepare_portal_layout_values()
        tenant_model = request.env['real_estate.tenant']
        tenant_domain = [('email', '=', request.env.user.email)]
        if 'user_id' in tenant_model._fields:
            tenant_domain = ['|', ('user_id', '=', request.env.user.id), ('email', '=', request.env.user.email)]
        tenant = tenant_model.sudo().search(tenant_domain, limit=1)

        lease_count = 0
        if tenant:
            lease_count = request.env['real_estate.lease'].sudo().search_count([
                ('tenant_id', '=', tenant.id)
            ])
        values.update({
            'lease_count': lease_count,
            'tenant': tenant,
        })
        return values

    @http.route(['/my/leases', '/my/leases/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_leases(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        tenant = values.get('tenant')
        if not tenant:
            values.update({
                'leases': request.env['real_estate.lease'].sudo().browse(),
            })
            return request.render('real_estate.portal_my_leases', values)

        leases = request.env['real_estate.lease'].sudo().search([
            ('tenant_id', '=', tenant.id),
            ('state', '=', 'active')
        ], order='start_date desc')
        values.update({
            'leases': leases,
        })
        return request.render('real_estate.portal_my_leases', values)



# class RealEstate(http.Controller):
#     @http.route('/real_estate/real_estate', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/real_estate/real_estate/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('real_estate.listing', {
#             'root': '/real_estate/real_estate',
#             'objects': http.request.env['real_estate.real_estate'].search([]),
#         })

#     @http.route('/real_estate/real_estate/objects/<model("real_estate.real_estate"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('real_estate.object', {
#             'object': obj
#         })

