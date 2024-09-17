from odoo import api, exceptions, fields, models, _


class FbiTeam(models.Model):
    _inherit = 'crm.team'
    _description = 'Sales Team'

    @api.model
    def action_your_pipeline(self):
        action = self.env["ir.actions.actions"]._for_xml_id("fbi_crm.crm_lead_action_telemarketer_pipeline")
        return self._action_update_to_pipeline(action)
    
    def assing_users_into_teams(self):
        # for team in self.search([]):
        #     team_res_id = team.get_external_id()
        #     res_id_xml = team_res_id[team.id]
        #     #### GET ALL TELPRO
        #     team.member_ids = [(5,)]
        #     team_users = []
        #     if res_id_xml == 'fbi_crm.fbi_crm_team_dematicall':
        #         team_users = self.env['res.users'].sudo().search([('name', 'ilike', 'TelPro')]).ids
        #     if res_id_xml == 'fbi_crm.fbi_crm_team_telpro_ynov_it':
        #         team_users = self.env['res.users'].sudo().search([('name', 'ilike', 'TelF')]).ids
        #     team.member_ids = [(6, 0, team_users)]
            
        
        #### Update all team by telemarketer
        for lead in self.env['crm.lead'].sudo().search([]):
            if not lead.telemarketer_id:
                continue
            user = lead.telemarketer_id
            if lead.team_id and user in (lead.team_id.member_ids | lead.team_id.user_id):
                continue
            team_domain = [('use_leads', '=', True)] if lead.type == 'lead' else [('use_opportunities', '=', True)]
            team = self.env['crm.team']._get_default_team_id(user_id=user.id, domain=team_domain)
            lead.team_id = team.id
                
                
