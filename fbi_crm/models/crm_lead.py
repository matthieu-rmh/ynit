# -*- coding: utf-8 -*-

import io
import os
import csv
import base64
import logging

from datetime import date, timedelta, datetime
from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import _
from odoo import modules, tools

from odoo.addons.crm.models import crm_stage

_logger = logging.getLogger(__name__)

class FbiLead(models.Model):
    _inherit = 'crm.lead'
    ##### FIX ORDER
    _order = 'stage_id_order ASC, activity_date_deadline_order ASC, id DESC'   
    
    
    @api.depends('activity_date_deadline')
    def _compute_activity_date_deadline_order(self):
        for record in self:
            record.activity_date_deadline_order = record.activity_date_deadline
            
    @api.depends('stage_id')
    def _compute_stage_id_order(self):
        for record in self:
            record.stage_id_order = record.stage_id and record.stage_id.id or 200
            
    activity_date_deadline_order = fields.Date(
        'Next Activity Deadline Order',
        compute='_compute_activity_date_deadline_order', compute_sudo=False, store=True, groups="base.group_user")
    stage_id_order = fields.Integer(
        'Stage Lead Order',
        compute='_compute_stage_id_order', compute_sudo=False, store=True, groups="base.group_user")
    ##### FIX ORDER
    
    @api.depends('partner_id')
    def _compute_function(self):
        """ compute the new values when partner_id has changed """
        for lead in self:
            if not lead.function or lead.partner_id.function:
                lead.function = lead.partner_id.function
    
    function = fields.Char('Fonction', compute='_compute_function', readonly=False, store=True)
    # region Fields
    code_relance_id = fields.Many2one('crm.code_relance')
    user_id = fields.Many2one(
        'res.users', string='Salesperson',
        domain=lambda self: [('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id)],
        check_company=True, index=True, tracking=True)
    telemarketer_id = fields.Many2one('res.users', string="Télévendeur", default=lambda self: self.env.user,
                                      domain=lambda self: [('groups_id', 'in',
                                                            self.env.ref('fbi_crm.group_fbi_crm_telemarketer').id)])
    commercial_annonce_id = fields.Many2one('crm.commercial_annonce', string="Commercial annoncé", required=False)
    lead_priority = fields.Selection([('p0', 'P0'),
                                      ('p1', 'P1'),
                                      ('p2', 'P2'),
                                      ('p3', 'P3'),
                                      ('p4', 'P4'),
                                      ('p5', 'P5'),
                                      ('p6', 'P6')],
                                     string='Priorité',
                                     required=False)
    priority = fields.Selection(
        crm_stage.AVAILABLE_PRIORITIES, string='Potentiel', index=True,
        default=crm_stage.AVAILABLE_PRIORITIES[0][0])
    
    linkedin = fields.Char(string='LinkedIn')
    ### DEPARTEMENT
    departement = fields.Char(string='Departement', compute='_compute_zip_departement', readonly=False, store=True)

    contact_bis_nom = fields.Char(string='Nom du contact 2')
    title_bis = fields.Many2one('res.partner.title', string='Titre 2', compute='_compute_title2', readonly=False, store=True)
    contact_bis_fonction = fields.Char(string='Fonction 2')
    contact_bis_telephone = fields.Char(string='Téléphone 2')
    contact_bis_email = fields.Char('Email 2')
    contact_bis_linkedin = fields.Char('LinkedIn 2')

    company_nom_commercial = fields.Char(string='Nom Commercial')
    company_nom_enseigne = fields.Char(string="Nom de l'Enseigne")
    company_date_creation = fields.Date(string='Date de Création')
    company_siren = fields.Char(string='N° SIREN')
    company_siret = fields.Char(string='N° SIRET')
    company_code_naf = fields.Char(string='Code NAF')
    company_code_naf_family = fields.Char(string='Famille des NAF', compute='_compute_company_code_naf_family', readonly=False, store=True)
    company_nb_sites = fields.Char(string='Nombre de Site')

    company_dernier_ca = fields.Float(string='Dernier CA')
    company_annee_ca = fields.Char(string='Année CA')
    company_dernier_effectif = fields.Char(string='Dernier Effectif')
    company_annee_effectif = fields.Char(string='Année Effectif')
    company_tranche_effectif = fields.Char(string='Tranche Effectif')
    company_zone_vente = fields.Char(string='Zone de Vente')
    company_type = fields.Char()

    potential_doc_entrants_descriptif = fields.Char(string='Documents Entrants')
    #### FEAT 13/03/2024
    potential_doc_entrants_nbr_facture_fournisseur = fields.Char(string='#Nbr Facture Fournisseur')
    potential_doc_entrants_nbr_bon_de_livraison = fields.Char(string='#Nbr Bon de Livraison')
    potential_doc_entrants_nbr_bon_de_commande = fields.Char(string='#Nbr Bon de Commande')
    potential_saisie_en_interne = fields.Boolean(string='Saisie en interne ?')
    potential_doc_sortants_descriptif = fields.Char(string='Documents Sortants')

    potential_logiciel_comptable = fields.Char(string='Logiciel Comptable')
    potential_logiciel_metier = fields.Char(string='Logiciel Métier')
    potential_chorus = fields.Boolean(string='Chorus')

    commentaire_choice = fields.Selection([('fac_four',
                                            "Accepte de nous rencontrer pour découvrir notre solution qui permet la "
                                            "dématérialisation des factures fournisseurs et l'import des écritures "
                                            "dans leur logiciel comptable"),
                                           ('doc_entrants',
                                            "Accepte de nous rencontrer pour découvrir notre nouvelle solution qui "
                                            "permet de dématérialiser et classer les documents entrants de "
                                            "l'entreprise"),
                                           ('pres_flux_sortants',
                                            "Accepte de nous rencontrer pour une présentation de notre solution qui "
                                            "permet de dématérialiser les flux sortants")],
                                          string="Commentaire type")
    rdv_visio = fields.Boolean(string="RDV Visio")
    commentaire_lines = fields.Text(string="Commentaire libre")    
    # endregion    
    
    ####### FIX TAB EVALUATION
    # EVAL DEMATICALL
    eval_dematicall_fonction_interlocuteur = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")], 
                                            string="Fonction de l'Interlocuteur")
    eval_dematicall_suivi_argumentaire = fields.Selection([
                                                ('1', "1"),
                                                ('2', "2"),
                                                ('3', "3"),
                                                ('4', "4"),
                                                ('5', "5")],
                                            string="Suivi de l'Argumentaire")
    eval_dematicall_interpret_donner_envie_rythme_de_voix_sourire = fields.Selection([
                                                ('1', "1"),
                                                ('2', "2"),
                                                ('3', "3"),
                                                ('4', "4"),
                                                ('5', "5")],
                                            string="Interprétation / Donner Envie / Rythme de Voix / Sourire")
    eval_dematicall_parle_de_visio_avant_rdv = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Parle de Visio avant RDV")
    eval_dematicall_comprehension_rdv_par_prospect = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Compréhension du RDV par le Prospect")
    eval_dematicall_rdv_propose_10_jours = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="RDV proposé à 10 Jours")
    eval_dematicall_rdv_force = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="RDV Forcé")
    eval_dematicall_implication_prospect_rdv_note = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Implication Prospect (Le RDV à t-il été noté ?)")
    eval_dematicall_eligibilite_volume_150_documents = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Éligibilité Volume (150 Documents)")
    eval_dematicall_valide = fields.Selection([
                                                ('oui', "Oui"),
                                                ('non', "Non"),
                                                ('j72h', "Vérification J72H")],
                                            string="Validé")
    # eval_dematicall_verificateur = fields.Selection([
    #                                             ('telpro', "Tel Pro"),
    #                                             ('superviseur', "Superviseur")],
    #                                         string="Vérificateur")
    eval_dematicall_verificateur = fields.Many2one('res.users', string="Vérificateur", default=lambda self: self.env.user,
                                      domain=lambda self: [('groups_id', 'in', self.env.ref('fbi_crm.group_fbi_crm_manager').id)])
    eval_dematicall_raison_non_validation_precisions_demander = fields.Text(string="Raison non-validation/Précision(s) à demander")

    # EVAL CONTRÔLE QUALITÉ - ACCUEIL
    eval_fbi_validation_nom_personne_a_contacter = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")], 
                                            string="Validation du Nom de la personne à contacter")
    eval_fbi_validation_fonction_personne_a_contacter = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Validation de la fonction de la personne à contacter")
    eval_fbi_accueil_objection_1 = fields.Char(string="Objection 1")
    eval_fbi_accueil_objection_2 = fields.Char(string="Objection 2")
    eval_fbi_accueil_listen_by_id = fields.Many2one('res.users', string="Réécouter par", default=lambda self: self.env.user, 
                                                domain=lambda self: [('active', "=", True), ("share", "=", False), ('groups_id', 'in', self.env.ref('fbi_crm.group_fbi_crm_telemarketer').id)])
    # EVAL CONTRÔLE QUALITÉ - SUR CONTACT ARGUMENTE
    eval_fbi_validation_fonction = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Validation de la fonction")
    eval_fbi_quelle_fonction = fields.Char(string="Quelle est la fonction")
    eval_fbi_qualite_suivi_argumentaire = fields.Selection([
                                                ('1', "1"),
                                                ('2', "2"),
                                                ('3', "3"),
                                                ('4', "4"),
                                                ('5', "5")],
                                            string="Qualité du suivi argumentaire")
    eval_fbi_qualite_closing = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Qualité du closing")
    eval_fbi_rdv_propose_a_10_jours = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="RDV proposé à 10 Jours")
    eval_fbi_objection_1 = fields.Char(string="Objection 1")
    eval_fbi_qualite_closing_1 = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Qualité du closing")
    eval_fbi_objection_2 = fields.Char(string="Objection 2")
    eval_fbi_qualite_closing_2 = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Qualité du closing")
    eval_fbi_objection_3 = fields.Char(string="Objection 3")
    eval_fbi_qualite_closing_3 = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Qualité du closing")
    eval_fbi_interpret_donner_envie_rythme_de_voix_sourire = fields.Selection([
                                                ('1', "1"),
                                                ('2', "2"),
                                                ('3', "3"),
                                                ('4', "4"),
                                                ('5', "5")],
                                            string="Interprétation / Donner Envie / Rythme de Voix / Sourire")
    eval_fbi_parle_de_visio_avant_rdv = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Parle de Visio avant RDV")
    eval_fbi_plage_horaire_disponible_sur_agenda = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Plage horaire disponible sur agenda")

    # EVAL CONTRÔLE QUALITÉ - QUALIFICATION DU RDV
    qualif_fbi_volume_indique_par_prospect = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Volume indiqué par le prospect")
    qualif_fbi_volume_indique_par_telpro = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Volume indiqué par le Télépro")
    qualif_fbi_comprehension_objet_rdv = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Compréhension objet du RDV")
    qualif_fbi_prise_conges_avec_confirmation_rdv_date_et_heure = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Prise de congés avec confirmation du RDV (Date et heure)")
    qualif_fbi_implication_prospect_rdv_note = fields.Selection([
                                                ('oui', "Oui"), 
                                                ('non', "Non")],
                                            string="Implication prospect (Le RDV a t-il été noté ?)")
    qualif_fbi_tournure_phrase_risque_fantaisiste = fields.Text(string="Tournure phrase à risque, fantaisistes... ?")
    qualif_fbi_validation = fields.Selection([
                                                ('oui', "Oui"),
                                                ('non', "Non"),
                                                ('j72h', "Vérification J72H")],
                                            string="Validation")
    # qualif_fbi_verificateur = fields.Selection([
    #                                             ('telpro', "Tel Pro"),
    #                                             ('superviseur', "Superviseur")],
    #                                         string="Vérificateur")
    qualif_fbi_verificateur = fields.Many2one('res.users', string="Vérificateur", default=lambda self: self.env.user,
                                      domain=lambda self: [('groups_id', 'in', self.env.ref('fbi_crm.group_fbi_crm_manager').id)])
    qualif_fbi_commentaire_si_revision = fields.Text(string="Commentaire si Révision")

    # EVAL CONTRÔLE QUALITÉ - VALIDATION DIRECTION
    qualif_direction_validation = fields.Selection([
                                                ('oui', "Oui"),
                                                ('non', "Non"),
                                                ('j72h', "Vérification J72H")], 
                                            string="Validation direction")
    # qualif_direction_verificateur = fields.Selection([
    #                                             ('telpro', "Tel Pro"),
    #                                             ('superviseur', "Superviseur")],
    #                                         string="Vérificateur")
    qualif_direction_verificateur = fields.Many2one('res.users', string="Vérificateur", default=lambda self: self.env.user,
                                      domain=lambda self: [('groups_id', 'in', self.env.ref('fbi_crm.group_fbi_crm_manager').id)])

    # MAIL PROSPET
    prospect_mail_body = fields.Char(string="Corps mail prospect", compute="_compute_prospect_mail_body")
    send_prospect_mail = fields.Boolean(string="Envoi mail prospect", default=True)    
    stage_id_name = fields.Char('Etape de la fiche', compute='_compute_stage_id_reference_name', groups="base.group_user")
    
    ##### FIX CHOIX DES EMAILS A ENVOYER
    calendar_user_event_count = fields.Integer('# Meetings', compute='_compute_calendar_user_event_count')
    email_template_confirm_choice = fields.Selection([
                                                ('generic', "Générique"),
                                                ('generic_visio', "Générique avec Visio"),
                                                ('invoice_supplier', "Facture Fournisseur"),
                                                ('invoice_supplier_visio', "Facture Fournisseur avec Visio"),], 
                                            string="Mail de Confirmation")
    
    #### FIX CONTACT NAME NOM ET PRENOMS
    contact_name = fields.Char('Contact Name', tracking=30, compute='_compute_contact_name', readonly=False, store=True)
    contact_firstname = fields.Char('Prénom(s) du contact')
    contact_bis_firstname = fields.Char('Prénom(s) du contact 2')
    
    ##### FIX 01/03/2024 ######
    rdv_pour_confirmation = fields.Text('RDV à Confirmer')
    rdv_72_confirmation = fields.Boolean(string='Contrôle Qualité - RDV 72H', default=False)
    
    ##### FEAT
    personalized_comments = fields.Text(string="Commentaires personnalisés")
    event_customer_decline = fields.Boolean(string='Refus RDV Client', default=False)
    
    #### FEAT : HISTORY 28/03/2024
    lead_date_dealine_line = fields.One2many(comodel_name='crm.lead.date.dealine.history', inverse_name='lead_id', string="Date Deadline History")
    
    
    ##### ONCHANGE COMMENTAIRE
    @api.onchange('commentaire_lines')
    def _onchange_commentaire_lines(self):
        if self.commentaire_lines:
            self.personalized_comments = self.commentaire_lines
            
    @api.onchange('personalized_comments')
    def _onchange_personalized_comments(self):
        if self.personalized_comments:
            self.commentaire_lines = self.personalized_comments
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.context.get('analysis_telemarketer'):
            lazy = False
        result = super(FbiLead, self).read_group( domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return result
    
    ### FIX CODE NAF
    def _fill_company_code_naf(self):
        csv_company_code_naf_datas = tools.misc.file_path('fbi_crm/data/code_naf.csv')
        with open(csv_company_code_naf_datas, 'r', encoding = 'utf8') as ppfile:
            csvreader = csv.reader(ppfile, delimiter=';')
            # header = next(csvreader)
            for row in csvreader:
                code_naf = str(str(row[0])[:5]).strip()
                leads = self.search([('company_code_naf', 'like', code_naf.strip() + '%')])
                for lead in leads:
                    lead.company_code_naf = str(row[0]).strip()
        return True
    
    @api.depends('company_code_naf')
    def _compute_company_code_naf_family(self):
        for lead in self:
            if lead.company_code_naf:
                code_naf = str(str(lead.company_code_naf)[:5]).strip()
                family = self.env['crm.code.naf.family'].sudo().search([('code', '=', code_naf)])
                # lead.company_code_naf = code_naf
                lead.company_code_naf_family = family.label
    
    @api.depends('partner_id')
    def _compute_contact_name(self):
        """ compute the new values when partner_id has changed """
        for lead in self:
            continue
            # lead.update(lead._prepare_contact_name_from_partner(lead.partner_id))
    
    ##### FIX DEPARTEMENT
    @api.depends('zip')
    def _compute_zip_departement(self):
        for lead in self:
            if lead.zip:
                lead.departement = str(lead.zip)[:2]
        
    ##### FIX TITLE 2
    @api.depends('partner_id')
    def _compute_title2(self):
        for lead in self:
            if not lead.title_bis or lead.partner_id.title:
                lead.title_bis = lead.partner_id.title
    
    ##### FIX ACTIVITES COUNT
    lead_activities_count = fields.Integer('Nb d\'activités de la fiche', compute='_compute_lead_activities_count')
    lead_stages_count = fields.Integer('Nb de changement d\'étape de la fiche', compute='_compute_lead_activities_count')
    last_date_calling_lead = fields.Datetime('Date du dernier appel', compute='_compute_lead_last_date_calling')
    
    def _compute_lead_last_date_calling(self):
        for lead in self:
            date_last_call = False
            mail_activity_type_id = self.env['ir.model.data'].sudo()._xmlid_to_res_id('mail.mail_activity_data_call')
            lastCalling = self.env['mail.message'].sudo().search([('mail_activity_type_id', '=', mail_activity_type_id), ('res_id', '=', lead.id), ('model', '=', 'crm.lead')], order='id DESC')
            for cDate in lastCalling:
                date_last_call = cDate.date
                break
            lead.last_date_calling_lead = date_last_call
    
    def _compute_lead_activities_count(self):
        for lead in self:
            count = 0
            count_stage = 0
            subtype_message = self.env['ir.model.data'].sudo()._xmlid_to_res_id('crm.mt_lead_stage')
            count_stage += self.env['mail.message'].sudo().search_count([('subtype_id', '=', subtype_message), ('res_id', '=', lead.id), ('model', '=', 'crm.lead')])
            count += self.env['mail.activity'].sudo().search_count([('res_id', '=', lead.id), ('res_model', '=', 'crm.lead')])
            lead.lead_stages_count = count_stage
            lead.lead_activities_count = count
    
    ### FIX RDV Vendeur
    def _compute_calendar_user_event_count(self):
        if self.ids:
            first_week_day = date.today() - timedelta(days=date.today().weekday() % 7)
            future_events_ids = self.env['calendar.event'].sudo().search([('start', '>=', first_week_day)]).ids
            meeting_data = self.env['calendar.attendee'].sudo()._read_group([
                ('partner_id', 'in', [self.user_id and self.user_id.partner_id and self.user_id.partner_id.id]),
                ('event_id', 'in', future_events_ids)
            ], ['partner_id'], ['partner_id'])
            mapped_data = {m['partner_id'][0]: m['partner_id_count'] for m in meeting_data}
        else:
            mapped_data = dict()
        for lead in self:
            res_id = lead.user_id and lead.user_id.partner_id and lead.user_id.partner_id.id or False
            lead.calendar_user_event_count = mapped_data.get(res_id, 0)
    
    ##### ONCHANGE COMMENTAIRE SET RDV CONFIRMATION TEXT
    @api.onchange('qualif_fbi_commentaire_si_revision')
    def _onchange_qualif_fbi_commentaire_si_revision(self):
        if self.qualif_fbi_commentaire_si_revision:
            self.rdv_pour_confirmation = self.qualif_fbi_commentaire_si_revision
        
    ##### CHANGE RDV VISIO
    @api.onchange('email_template_confirm_choice')
    def _onchange_email_template_confirm_choice(self):
        if self.email_template_confirm_choice in ['generic_visio', 'invoice_supplier_visio']:
            self.rdv_visio = True
        else:
            self.rdv_visio = False
             
    ###### CHANGE EMAIL FROM IF NULL
    @api.onchange('contact_bis_email')
    def _onchange_email_from(self):
         if self.contact_bis_email and not self.email_from:
             self.email_from = self.contact_bis_email
        
    @api.depends('stage_id')
    def _compute_stage_id_reference_name(self):
        for record in self:
            record.stage_id_name = 'Aucun'
            if self.stage_id:
                stage_model_data = self.env['ir.model.data'].sudo().search([
                                                ('res_id', '=', record.stage_id and record.stage_id.id), 
                                                ('model', '=', 'crm.stage'), 
                                                ('module', 'ilike', 'crm')], 
                                            limit=1)
                if stage_model_data:
                    record.stage_id_name = stage_model_data.name

    
    @api.depends("contact_bis_nom", "commercial_annonce_id", "rdv_visio")
    def _compute_prospect_mail_body(self):
        event = sorted(self.calendar_event_ids, key=lambda evt: evt.start, reverse=True)[0] \
            if self.calendar_event_count > 0 else False

        self.prospect_mail_body = \
            (self.contact_bis_nom if self.contact_bis_nom else "Bonjour") + \
            ",\r\n\r\nPour faire suite à votre entretien téléphonique" + \
            ((" avec " + self.commercial_annonce_id.name) if self.commercial_annonce_id else "") + \
            ", nous vous remercions pour votre accueil"

        if event:
            self.prospect_mail_body += \
                " et vous confirmons notre rendez-vous qui aura lieu " + \
                ("en visio" if self.rdv_visio else "dans vos locaux") + \
                event.start.strftime(" le %d/%m/%Y à %H:%M")

        self.prospect_mail_body += \
            ".\r\nNous pourrons ainsi vous présenter notre " \
            "solution qui permet notamment la digitalisation, le classement et la validation des factures " \
            "fournisseurs ainsi que la simplification de la saisie des écritures comptables.\r\n\r\n" \
            "Dans cette attente nous vous souhaitons une agréable journée.\r\n\r\n" + \
            (("Pour " + self.commercial_annonce_id.name) if self.commercial_annonce_id else "Cordialement") + \
            (" - " + self.telemarketer_id.phone if self.telemarketer_id.phone else "")
    

    # region CRUD
    @api.model_create_multi
    def create(self, vals_list):
        known_sirets = [str(lead.company_siret).strip() for lead in self.env['crm.lead'].search([])]
        known_phones = [str(lead.phone).strip() for lead in self.env['crm.lead'].search([])]
        code_relance_99 = self.env['ir.model.data'].sudo()._xmlid_to_res_id('fbi_crm.crm_code_relance_99')

        for vals in vals_list:
            new_telemarketer_id = vals.get('telemarketer_id')
            new_commercial_annonce_id = vals.get('commercial_annonce_id')
            new_company_siret = str(vals.get('company_siret')).strip()
            new_phone = str(vals.get('phone')).strip()
            if isinstance(new_telemarketer_id, int):
                new_telemarketer_id = self.env['res.users'].browse(new_telemarketer_id)
            # Mise en place du commercial référant par rapport au tel pro
            if not new_commercial_annonce_id and new_telemarketer_id and \
                    new_telemarketer_id.default_commercial_annonce_id:
                vals.update({'commercial_annonce_id': new_telemarketer_id.default_commercial_annonce_id.id})
            if new_company_siret in known_sirets or new_phone in known_phones:
                vals.update({'code_relance_id': code_relance_99})
        # Super
        return super().create(vals_list)

    def write(self, vals):
        new_code_relance_id = vals.get('code_relance_id')
        # from_event : on ajoute dans le contexte si on vient d'un évènement d'un calendrier auquel cas on ne fait pas ce test
        # "PYTEST_CURRENT_TEST" in os.environ : Signifie qu'on est dans un test unitaire        
        
        # if not self.env.user.has_group('fbi_crm.group_fbi_crm_controle_qualite') and vals.get('stage_id') and \
        #         not self.env.context.get('from_event') and not self.env.is_superuser():
        #     raise UserError(_("L'état de l'opportunité ne peut être changé"))

        if isinstance(new_code_relance_id, int):
            new_code_relance_id = self.env['crm.code_relance'].browse(new_code_relance_id)

        for record in self:
            # Interdiction de code relance si le lead est validé
            if record.calendar_event_count == 1:
                event = record.calendar_event_ids[0]
                if event.state == "validated" and new_code_relance_id and record.code_relance_id != new_code_relance_id:
                    raise UserError(_("Le code relance ne peut pas être modifié quand le RDV est validé"))

            # Changement de l'étape du lead si code relance différent
            if new_code_relance_id and record.code_relance_id.state != new_code_relance_id.state:
                if new_code_relance_id.state == "non_exploitable":
                    record._change_opportunity_stage('fbi_crm.stage_non_exploitable', vals)
                    ##### FIX REMOVE ALL ACTIVITIES #####
                    all_activities = self.env['mail.activity'].sudo().search([('res_id', '=', record.id), ('res_model', '=', 'crm.lead'), ('res_name', '=', str(record.name).strip())])
                    for h_act in all_activities:
                        h_act.sudo().unlink()
                    ##### FIX REMOVE ALL ACTIVITIES #####
                elif new_code_relance_id.state == "rdv":
                    record._change_opportunity_stage('fbi_crm.stage_rdv', vals)
                elif new_code_relance_id.state == "en_cours":
                    record._change_opportunity_stage('fbi_crm.stage_en_cours', vals)

        return super().write(vals)
    # endregion

    # region Actions
    def action_schedule_meeting(self, smart_calendar=True):
        #### FEAT DEMANDE 23/04/2024 == DEGRADE
        # for lead in self:
        #     if lead.user_id.vendor_ms_calendar_url:
        #         return {
        #             'type': 'ir.actions.act_url',
        #             'url': lead.user_id.vendor_ms_calendar_url,
        #             'target': 'new',
        #         }
        #     else:
        #         # Gérer le cas où l'URL est vide
        #         raise ValidationError("L'URL du calendrier du vendeur n'est pas défini.")
        # return True
        #### FEAT DEMANDE 23/04/202 == DEGRADE
        
        # La création d'un évènement de calendrier rajoute un participant lié au lead par le fait qu'il y ait
        #  l'id du lead dans default_partner_ids du contexte de l'action.
        # Pour empêcher cet ajout, il faut donc le retirer
        action = super().action_schedule_meeting(smart_calendar)
        new_partner_ids = action['context'].get('default_partner_ids')

        # Pour ce faire, il faut aller chercher le partner_id défini sur l'opportunité
        default_opportunity_id = self.env['crm.lead'].browse(action['context'].get('default_opportunity_id'))
        new_partner_crm_ids = []
        if default_opportunity_id:
            # if default_opportunity_id.partner_id and default_opportunity_id.partner_id.id in new_partner_ids:
            #     new_partner_ids.remove(default_opportunity_id.partner_id.id)
            if self.telemarketer_id:
                telemarketer_partner_id = self.telemarketer_id.partner_id
                if telemarketer_partner_id:
                    new_partner_crm_ids.append(telemarketer_partner_id.id)
                # if telemarketer_partner_id and telemarketer_partner_id.id in new_partner_ids:
                #     new_partner_ids.remove(telemarketer_partner_id.id)

            if self.user_id:
                user_partner_id = self.user_id.partner_id
                if user_partner_id:
                    new_partner_crm_ids.append(user_partner_id.id)
                # if user_partner_id and user_partner_id.id not in new_partner_ids:
                #     new_partner_ids.append(user_partner_id.id)
                    
                ### UNCHECK USER_ID
                self.env['calendar.filters'].sudo().search([
                    ('user_id', '=', self.env.user.id),
                    ('partner_id', '!=', user_partner_id.id),
                    ('partner_checked', '=', True)
                ]).partner_checked = False
                
                calendar_filter = self.env['calendar.filters'].search([
                            ('user_id', '=', self.env.user.id),
                            ('partner_id', '=', user_partner_id.id)
                        ], limit=1)
                
                if calendar_filter:
                    if not calendar_filter.partner_checked:
                        calendar_filter.partner_checked = True
                else:
                    self.env['calendar.filters'].create({
                            'user_id': self.env.user.id,
                            'partner_id': user_partner_id.id,
                            'partner_checked': True
                    })

        action['context'].update({
            # 'default_partner_ids': new_partner_ids,
            'search_default_opportunity_id': False,
            # 'default_opportunity_id': False,
            'default_partner_ids': new_partner_crm_ids,
        })
        return action

    # Fonction pour ouvrir l'URL
    def open_vendor_url(self):
        _logger.info('================== OPEN VENDOR URL ====================')
        for lead in self:
            if lead.user_id.vendor_ms_calendar_url:
                return {
                    'type': 'ir.actions.act_url',
                    'url': lead.user_id.vendor_ms_calendar_url,
                    'target': 'new',
                }
            else:
                # Gérer le cas où l'URL est vide
                raise ValidationError("L'URL du calendrier du vendeur n'est pas défini.")
    # endregion
    
    #### CHANGE TEAM FROM TELEVENDEUR
    @api.depends('telemarketer_id', 'type')
    def _compute_team_id(self):
        """ When changing the telemarketer, also set a team_id or restrict team id
        to the ones user_id is member of. """
        for lead in self:
            if not lead.telemarketer_id:
                continue
            user = lead.telemarketer_id
            if lead.team_id and user in (lead.team_id.member_ids | lead.team_id.user_id):
                continue
            team_domain = [('use_leads', '=', True)] if lead.type == 'lead' else [('use_opportunities', '=', True)]
            team = self.env['crm.team']._get_default_team_id(user_id=user.id, domain=team_domain)
            lead.team_id = team.id
    
    #### TEST IF TELEMARKETER EXIST
    def is_dematicall(self):
        return True if self.telemarketer_id else False
    
    #### GET ID XML
    def _get_res_id(self, xml_id):
        return self.env['ir.model.data'].sudo()._xmlid_to_res_id(xml_id)
    
    #### CREATE ACTIVITY CRON
    def _create_activity_user_if_not_exists(self, activity_type_xmlid, date_deadline=False, notes="", user_id=""):
        activity_type_id = self._get_res_id(activity_type_xmlid)
        model_id = self.env['ir.model']._get_id('crm.lead')
        
        exist_activities = self.env['mail.activity'].search([
                                            ('activity_type_id', '=', activity_type_id),
                                            ('res_id', '=', self.id),
                                            ('res_model_id', '=', model_id),
                                            ('user_id', '=', user_id or self.user_id and self.user_id.id or self._get_verificateur())
        ])
        
        for eActivty in exist_activities:
            eActivty.sudo().unlink()
            break
        
        if not self.env['mail.activity'].search([
                                            ('activity_type_id', '=', activity_type_id),
                                            ('res_id', '=', self.id),
                                            ('res_model_id', '=', model_id)]):
            activity = self.env['mail.activity'].create({
                'res_id': self.id,
                'res_model_id': model_id,
                'activity_type_id': activity_type_id,
                'user_id': self.telemarketer_id and self.telemarketer_id.id or self._get_verificateur(),
                'note': notes
            })
            if date_deadline:
                activity.date_deadline = str(date_deadline)
            else:
                activity.date_deadline = activity.with_context({'opportunity_id': self.id})._calculate_date_deadline(activity.activity_type_id)
                
    #### CREATE ACTIVITIE AFTER STATE CHANGE
    def _create_activity_if_not_exists(self, activity_type_xmlid, date_deadline=False, notes=""):
        activity_type_id = self._get_res_id(activity_type_xmlid)
        model_id = self.env['ir.model']._get_id('crm.lead')
        if not self.env['mail.activity'].search([
                                            ('activity_type_id', '=', activity_type_id),
                                            ('res_id', '=', self.id),
                                            ('res_model_id', '=', model_id)]):
            activity = self.env['mail.activity'].create({
                'res_id': self.id,
                'res_model_id': model_id,
                'activity_type_id': activity_type_id,
                'user_id': self.telemarketer_id and self.telemarketer_id.id or self._get_verificateur(),
                'note': notes
            })
            if date_deadline:
                activity.date_deadline = str(date_deadline)
            else:
                activity.date_deadline = activity.with_context({'opportunity_id': self.id})._calculate_date_deadline(activity.activity_type_id)
    
    #### GET VERIFICATEUR
    def _get_verificateur(self):
        if self.qualif_direction_verificateur:
            verificateur = self.qualif_direction_verificateur
            return verificateur.id
        elif self.qualif_fbi_verificateur:
            verificateur = self.qualif_fbi_verificateur
            return verificateur.id
        elif self.eval_dematicall_verificateur:
            verificateur = self.eval_dematicall_verificateur
            return verificateur.id
        else:
            return self.telemarketer_id.id if self.telemarketer_id else self.env.user.id
    
    #### GET SUPERVISEURS
    # def _get_superviseur(self):
    #     superviseurs = self.env.ref('fbi_crm.group_fbi_crm_manager').users
    
    #### Confirmation RDV
    def _send_propsect_mail(self):
        # YOU MUST ADD THE PROSPECT TO THE GUESTS FOR THIS TO WORK
        event = sorted(self.calendar_event_ids, key=lambda evt: evt.start, reverse=True)[0]
        event.with_context(no_mail_to_attendees=True).partner_ids |= self.partner_id
        event.with_context(no_mail_to_attendees=True).partner_ids |= self.user_id and self.user_id.partner_id 
        ics_files = event._get_ics_file()
        ics_file = ics_files.get(event.id)
        
        for attendee in event.attendee_ids:
            # if not attendee.email:
            #     raise ValidationError("Le prospect n'a pas d'adresse email.")
            # AN OUTLOOK INVITATION
            # CONFIRMATION EMAIL ARE SENT TO THE SALESPERSON WHICH HE CAN FORWARD TO THE PROSPECT
            # if self.user_id and self.user_id.partner_id and attendee.partner_id == self.user_id.partner_id:
            if attendee.email and attendee.partner_id == self.partner_id:
                self.env.ref('fbi_crm.fbi_crm_template_meeting_prospect_mail').send_mail(attendee.id,
                    email_values={
                        'email_to': attendee.email,
                        'email_cc': self.user_id.email,
                        'attachment_ids': [self.env['ir.attachment'].create({
                            'name': 'invitation.ics',
                            'type': 'binary',
                            'mimetype': 'text/calendar',
                            'datas': base64.b64encode(ics_file),
                        }).id]
                    }, force_send=True)
        
    def action_direction_delete_rdv_client(self):
        self.ensure_one()
        if not self.is_dematicall():
            raise ValidationError("Le Télévendeur n'est pas défini.")
        if self.is_dematicall():
            self.stage_id = self._get_res_id('fbi_crm.stage_annule_client')
            meeting_data = self.env['calendar.event'].sudo().search([
                                                        ('res_id', '=', self.id), 
                                                        ('res_model', '=', 'crm.lead')
                                                    ], order='id DESC', limit=1)
            meeting_data.sudo().unlink()
    
    def action_direction_confirm_rdv(self):
        _logger.info('================== ENVOI RDV ====================')
        self.ensure_one()
        if not self.is_dematicall():
            raise ValidationError("Le Télévendeur n'est pas défini.")
        if self.is_dematicall():
            ### COUNT 20 Days
            if self.calendar_event_count == 0:
                raise ValidationError("Un RDV doit être pris pour cette fiche.")
            ### GET MEETING
            meeting = self.env['calendar.event'].sudo().search([
                                                        ('res_id', '=', self.id), 
                                                        ('res_model', '=', 'crm.lead')
                                                    ], order='id DESC', limit=1)
            if meeting.start.date() > date.today():
                delta = int(((meeting.start.date()) - date.today()).days)
                #### If an appointment is made on D+20, 
                ### D-7 reminder activity will be automatically created 
                ## Information entered + passing the “Appointment to be confirmed on D-7” form.
                if delta >= 20:
                    ### OPEN WIZARD TO CHOICE TELEMARKETER
                    return {
                        'name': _('Télévendeur / Manager'),
                        'res_model': 'crm.lead.choise.telemarketer',
                        'view_mode': 'form',
                        'context': {
                            'active_model': 'crm.lead',
                            'active_ids': self.ids,
                            'rappel_j_7': True,
                            'date_deadline': (meeting.start.date() - timedelta(days=7)),
                        },
                        'target': 'new',
                        'type': 'ir.actions.act_window',
                    }
                    
                    # self._create_activity_if_not_exists('fbi_crm.mail_activity_type_rappel_J7', date_deadline=(meeting.start.date() - timedelta(days=7)), notes='Confirmer le RDV SVP avant 7 jours.')
                    # self.stage_id = self._get_res_id('fbi_crm.stage_rdv_attente_conf_J_7')
                #### If an appointment is made on D-20, 
                ### the form will be changed to "Commercial Shipping Appointment + Archives"
                else:
                    self.stage_id = self._get_res_id('fbi_crm.stage_envoi_et_archive')
                    ### SEND EMAILS
                    ### EMAIL VENDEUR SEULEMNT
                    _logger.info('================== PAR DEFAUT ENVOI VISIO ====================')
                    template_mail = 'fbi_crm.fbi_crm_template_meeting_confirmed_mail'
                    to_emails = ',' .join([
                        user.email for user in (
                            self.env.ref('fbi_crm.group_fbi_crm_dm').users | 
                            self.env.ref('fbi_crm.group_fbi_crm_manager').users) if user.email
                        ])
                    if self.env.context.get('rdv_physique'):
                        _logger.info('================== ENVOI PHYSIQUE ====================')
                        to_emails_physique = self.env['fbi.crm.lead.emails.to'].sudo().search([('name', '=', 'RDV_PHYSIQUE')]).remove_to
                        to_emails_physique_remove = to_emails_physique.split(',')
                        template_mail = 'fbi_crm.fbi_crm_template_meeting_confirmed_mail_presentiel'
                        to_emails = ',' .join([
                        user.email for user in (
                            self.env.ref('fbi_crm.group_fbi_crm_dm').users | 
                            self.env.ref('fbi_crm.group_fbi_crm_manager').users) if user.email and user.email not in to_emails_physique_remove
                        ])
                        
                    #### COMMERCIAL
                    for rdvTo in self.env['fbi.crm.lead.emails.to'].sudo().search([('name', '=', 'RDV')]):
                        rdvUsers = rdvTo.user_ids and rdvTo.user_ids.ids
                        if self.user_id and self.user_id.id in rdvUsers:
                            to_emails_rdv_join = rdvTo.add_to
                            to_emails_rdv_join = to_emails_rdv_join.split(',')
                            to_emails += ',' + ',' .join(str(x) for x in to_emails_rdv_join)
                            _logger.info('================== AUTRES DESTINATAIRES ====================')
                            _logger.info(to_emails)
                        
                    self.env.ref(template_mail).send_mail(self.id,
                        email_values={
                            'email_to': self.user_id.email,
                            'email_cc': to_emails,
                        }, force_send=True)
                    ### EMAIL VENDEUR - PROSPECT
                    # DISABLE VISIO 27/03/2024
                    ## self._send_propsect_mail()
                    ### END SEND EMAILS
            else:
                raise ValidationError("Un RDV avec une date future doit être pris pour cette fiche.")
        
    #### TELProd / Manager to CTRL QUALITE
    def action_telpro_manager_ctrl_qualite(self):
        self.ensure_one()
        if not self.is_dematicall():
            raise ValidationError("Le Télévendeur n'est pas défini.")
        if self.is_dematicall():
            self.stage_id = self._get_res_id('fbi_crm.stage_controle_qualite')
    
    #### Passage of the “Appointment to send” form
    def action_direction_validate(self):
        self.ensure_one()
        if not self.is_dematicall():
            raise ValidationError("Le Télévendeur n'est pas défini.")
        if self.is_dematicall():
            self.stage_id = self._get_res_id('fbi_crm.stage_rdv_a_envoyer')
    
    #### Listening to the new exchange - Adding a note to the sheet
    def action_to_validation_direction(self):
        _logger.info('==================')
        _logger.info('Action to validate')
        self.ensure_one()
        if not self.is_dematicall():
            raise ValidationError("Le Télévendeur n'est pas défini.")
        if self.is_dematicall():
            self.stage_id = self._get_res_id('fbi_crm.stage_validation_dm')
            self.rdv_72_confirmation = False
            
            ### DEMANDE APRES MISE EN PROD 10/04/2024
            meetingCrm = self.env['calendar.event'].sudo().search([
                                                        ('res_id', '=', self.id), 
                                                        ('res_model', '=', 'crm.lead')
                                                    ], order='id DESC', limit=1)
            _logger.info('Meeting')
            if meetingCrm:
                _logger.info('Meeting Exist')
                meetingCrm._send_prise_rdv_vendeur()
            _logger.info('==================')
            ### DEMANDE APRES MISE EN PROD 10/04/2024
    
    #### Information on the "D+72h" form, the reason for this need for confirmation 
    #### and the person (Supervisor or TelPro)
    #### who must request it - Transfer of the form to "Quality Control"
    def action_direction_pass_to_ctrl_qualite(self):
        self.ensure_one()
        if not self.is_dematicall():
            raise ValidationError("Le Télévendeur n'est pas défini.")
        
        ### OPEN WIZARD TO CHOICE TELEMARKETER
        return {
            'name': _('Télévendeur / Manager'),
            'res_model': 'crm.lead.choise.telemarketer',
            'view_mode': 'form',
            'context': {
                'active_model': 'crm.lead',
                'active_ids': self.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
        
        # if self.is_dematicall():
        #     self.stage_id = self._get_res_id('fbi_crm.stage_rdv_attente_conf_72h')
        #     #### CREATE ACTIVITIE 72
        #     self._create_activity_if_not_exists('fbi_crm.mail_activity_type_rappel_72h')
    
    #### Call from the customer to cancel the appointment - Change of form to 'Cancellation manager made'
    def action_manager_cancel_done(self):
        self.ensure_one()
        if not self.is_dematicall():
            raise ValidationError("Le Télévendeur n'est pas défini.")
        if self.is_dematicall():
            self.stage_id = self._get_res_id('fbi_crm.stage_annulation_manager_faite')
            #### DELETE LAST RDV
            meeting_data = self.env['calendar.event'].sudo().search([
                                                        ('res_id', '=', self.id), 
                                                        ('res_model', '=', 'crm.lead')
                                                    ], order='id DESC', limit=1)          
            #### DELETE MEETING
            meeting_data.sudo().unlink()
           
    
    #### Passage of the form "To be canceled - Direction decision"
    def action_confirm_cancel_direction(self):
        self.ensure_one()
        if not self.is_dematicall():
            raise ValidationError("Le Télévendeur n'est pas défini.")
        if self.is_dematicall():
            self.stage_id = self._get_res_id('fbi_crm.stage_a_annuler_direction_decision')
    
    #### Passage of the form "To cancel direction" CLICK ON A BUTTON - WITHOUT LOG NOTE
    def action_to_cancel_direction(self):
        self.ensure_one()
        if not self.is_dematicall():
            raise ValidationError("Le Télévendeur n'est pas défini.")
        if self.is_dematicall():
            self.stage_id = self._get_res_id('fbi_crm.stage_a_annuler_direction')
    
    ##### CHANGE STAGE TO CTRL QUALITE
    def action_controle_qualite(self):
        self.ensure_one()
        if not self.is_dematicall():
            raise ValidationError("Le Télévendeur n'est pas défini.")
        if self.is_dematicall():
            if self.calendar_event_count == 0:
                stage_id_target = self._get_res_id('fbi_crm.stage_controle_qualite')
                stageObject = self.env['crm.stage'].browse(stage_id_target)
                raise ValidationError("Un RDV doit être pris pour passer dans l'état " + stageObject.name)
            self.stage_id = self._get_res_id('fbi_crm.stage_controle_qualite')
        self.rdv_72_confirmation = False
        self.event_customer_decline = False
        return True
    
    #### CHANGE TO VALIDATION DM
    def action_direction(self):
        self.ensure_one()
        if not self.is_dematicall():
            raise ValidationError("Le Télévendeur n'est pas défini.")
        
        if self.is_dematicall() and self.qualif_fbi_validation:
            if self.qualif_fbi_validation == 'non':
                self.stage_id = self._get_res_id('fbi_crm.stage_a_annuler_direction')
            else:
                self.stage_id = self._get_res_id('fbi_crm.stage_validation_dm')
        return True
    
    def action_validation_direction(self):
        self.ensure_one()
        if not self.is_dematicall():
            raise ValidationError("Le Télévendeur n'est pas défini.")
        
        if self.is_dematicall() and self.qualif_direction_validation:
            if self.qualif_fbi_validation == 'non':
                self.stage_id = self._get_res_id('fbi_crm.stage_a_annuler')
            else:
                self.stage_id = self._get_res_id('fbi_crm.stage_controle_qualite')
        return True

    # region Protected Functions
    def _change_opportunity_stage(self, stage_xmlid, vals):
        stage = self.env['ir.model.data'].sudo()._xmlid_to_res_id(stage_xmlid)
        if stage:
            vals.update({'stage_id': stage})
    # endregion
    
    ### MASS ACTIONS TO NON EXPLOITABLE
    def action_to_non_exploitable_crm(self):
        crm_active_ids = self.env.context.get('active_ids')
        if len(crm_active_ids) > 200:
            raise ValidationError("Faire l'action tous les 200 Enregistemnts")
        for lead in crm_active_ids:
            crm_lead = self.browse(lead)
            crm_lead.active = True
            crm_lead.stage_id = self._get_res_id('fbi_crm.stage_non_exploitable')
            
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        
    ## FIX REMOVE ALL ACTIVITIES CRM
    def action_remove_all_activites_crm(self):
        crm_active_ids = self.env.context.get('active_ids')
        for lead in crm_active_ids:
            crm_lead = self.browse(lead)
           
            all_activities = self.env['mail.activity'].sudo().search([('res_id', '=', lead), ('res_model', '=', 'crm.lead'), ('res_name', '=', str(crm_lead.name))])
            for h_act in all_activities:
                h_act.sudo().unlink()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    ## FIX REMOVE ALL HISTORY CRM
    def action_remove_all_history_crm(self):
        crm_active_ids = self.env.context.get('active_ids')
        for lead in crm_active_ids:
            crm_lead = self.browse(lead)
            all_history = self.env['mail.message'].sudo().search([('res_id', '=', lead), ('model', '=', 'crm.lead'), ('record_name', '=', str(crm_lead.name))])
            for h_message in all_history:
                h_message.sudo().unlink()
                
            all_activities = self.env['mail.activity'].sudo().search([('res_id', '=', lead), ('res_model', '=', 'crm.lead'), ('res_name', '=', str(crm_lead.name))])
            for h_act in all_activities:
                h_act.sudo().unlink()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        
    ### FIX : Export PIPELINE TO CSV PHONE DOUBLONS
    def _export_all_crm_exploitable(self):
        # Generate CSV data
        csv_data = self.generate_csv_data()
        # Create a temporary CSV file
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerows(csv_data)
        csv_buffer.seek(0)
        # Attach CSV file to record
        attachment = self.env['ir.attachment'].create({
            'name': 'leads_doublons_phone_check.csv',
            'type': 'binary',
            'datas': base64.b64encode(csv_buffer.getvalue().encode()),
        })
        
    def generate_csv_data(self):
        # leads = self.search([('active', '=', True)])
        leads = self.search([])
        csv_data = [[
            'id', 'campaign_id', 'code_relance_id', 'commercial_annonce_id', 
            'email_from', 'contact_name', 'name', 'lead_priority', 'phone', 
            'telemarketer_id', 'user_id', 'stage_id', 'company_siret', 'partner_name']]
        for record in leads:
            if record.stage_id:
            # if record.stage_id and record.stage_id.name != 'Non exploitable':
                csv_data.append([
                    record.id,
                    record.campaign_id.name,
                    record.code_relance_id.name,
                    record.commercial_annonce_id.name,
                    record.email_from,
                    record.contact_name,
                    record.name,
                    record.lead_priority,
                    record.phone,
                    record.telemarketer_id.name,
                    record.user_id.name,
                    record.stage_id.name,
                    record.company_siret,
                    record.partner_name,
                ])
        return csv_data
    ### END : Export PIPELINE TO CSV PHONE DOUBLONS
    
    #### FIX REPLACE ALL PIPELINE INTO STAGE_A_CLASSER
    def replace_all_lead_into_class_stage(self):
        id_stages = []
        if self._get_res_id('fbi_crm.stage_validation_manager'):
            id_stages.append(self._get_res_id('fbi_crm.stage_validation_manager'))
        if self._get_res_id('fbi_crm.stage_valide'):
            id_stages.append(self._get_res_id('fbi_crm.stage_valide'))
        if id_stages:
            leads = self.sudo().search([('stage_id', 'in', id_stages), ('company_id', '=', 2)])
            for l in leads:
                l.active = False
                l.stage_id = l._get_res_id('fbi_crm.stage_a_classer')
            ## UNLINK STAGE
            for s in id_stages:
                st = self.env['crm.stage'].sudo().browse(s)
                st.sudo().unlink()
                
    #### FEAT CA IN PDF REPORT
    def format_amount(self, char_ca):
        amount_float = '{:2,.2f}'.format(float(0)).replace(',', ' ')
        try:
            amount_float = '{:2,.2f}'.format(float(char_ca)).replace(',', ' ')
        except:
            pass
        return amount_float
    
    #### FIX RDV / A Valider manager / A Valider direction / Validé => Envoi commercial + Archive
    def replace_all_leads_in_send_user_id_archive(self):
        id_stages = []
        if self._get_res_id('fbi_crm.stage_rdv'):
            id_stages.append(self._get_res_id('fbi_crm.stage_rdv'))
        if self._get_res_id('fbi_crm.stage_validation_manager'):
            id_stages.append(self._get_res_id('fbi_crm.stage_validation_manager'))
        if self._get_res_id('fbi_crm.stage_validation_dm'):
            id_stages.append(self._get_res_id('fbi_crm.stage_validation_dm'))
        if self._get_res_id('fbi_crm.stage_valide'):
            id_stages.append(self._get_res_id('fbi_crm.stage_valide'))
        if id_stages:
            leads = self.sudo().search([('stage_id', 'in', id_stages)])
            for l in leads:
                l.stage_id = l._get_res_id('fbi_crm.stage_envoi_et_archive')
                
    ##### RDV MAJ ERROR
    def _set_rdv_lead(self):
        leads_name = [
            'ETS P. CLAUX & FILS & CIE', 
            'GARAGE VAL', 
            'LA MAISON DU BRICOLEUR', 
            'EST USINAGE', 
            'TECHNA', 
            'NORMACHATS INGENIERIE', 
            'GARAGE PATRY', 
            'BOBIGNY EPOXY', 
            'SOCIETE DE CHAUDRONNERIE ET DE TUYAUTERIE INDUSTRIELLE DE L\'OISE - CTIO', 
            'SAS DU COLOMBIER', 
            'CARDARELLI', 
            'LE GOFF & GILLE', 
            'SERRURERIE VILDIEU', 
            'AVIR', 
            'SAS ALBAN DUCROCQ'
        ]
        
        id_Already_Ok = []
        for l in leads_name:
            lead = self.env['crm.lead'].sudo().search([('name', 'like', l.strip() + '%')], limit=1)
            id_Already_Ok.append(lead.id)
            
        subtype_message = self.env['ir.model.data'].sudo()._xmlid_to_res_id('crm.mt_lead_stage')
        code_relance_id = self.env['crm.code_relance'].sudo().search([('name', '=', '3 - RDV APPROCHE COMPTA')], limit=1)
        for cri in code_relance_id:
            stage_id = self.env['crm.stage'].sudo().search([('name', '=', 'En cours')], limit=1)
            for si in stage_id:
                leads_All = self.env['crm.lead'].sudo().search([('id', 'not in', id_Already_Ok), ("code_relance_id", "=", cri.id), ("stage_id", "=", si.id)])
                print(len(leads_All))
                for ll in leads_All:
                    last_mess = self.env['mail.message'].sudo().search([('date', '>=', '2024-04-17 12:00:00'), ('subtype_id', '=', subtype_message), ('res_id', '=', ll.id), ('model', '=', 'crm.lead')], order='id DESC', limit=1)
                    for lm in last_mess:
                        mail_tracking_value = self.env['mail.tracking.value'].sudo().search([('mail_message_id', '=', lm.id)], order='id DESC', limit=1)
                        for mtv in mail_tracking_value:
                            old_value_integer = mtv.old_value_integer
                            if old_value_integer:
                                ll.stage_id = old_value_integer
        return True
    
    ####### CSV DERNIER CA
    def _export_dernier_ca(self):
        # Generate CSV data
        leads = self.search([('company_dernier_ca', '!=', False)])
        csv_data = [['id', 'name', 'company_dernier_ca']]
        for record in leads:
            csv_data.append([
                record.id,
                record.name,
                record.company_dernier_ca,
            ])
            record.company_dernier_ca = 0
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerows(csv_data)
        csv_buffer.seek(0)
        # Attach CSV file to record
        attachment = self.env['ir.attachment'].create({
            'name': 'company_dernier_ca.csv',
            'type': 'binary',
            'datas': base64.b64encode(csv_buffer.getvalue().encode()),
        })
        
    def _import_dernier_ca(self):
        ca = tools.misc.file_path('fbi_crm/data/fbi_company_dernier_ca.csv')
        with open(ca, 'r', encoding = 'utf8') as ppfile:
            csvreader = csv.reader(ppfile, delimiter=',')
            header = next(csvreader)
            for row in csvreader:
                lead = self.env['crm.lead'].browse(int(row[0]))
                if lead:
                    ca_lead = "".join([c for c in str(row[2]) if c.isdigit()])
                    if ca_lead:
                        lead.company_dernier_ca = float(ca_lead.strip())
        return True
    
    ###### CSV - ATTACH DATE ACTIVITY TO CRM
    def _attach_lead_activities(self):
        activities = tools.misc.file_path('fbi_crm/data/demat_sud_import_17.csv')
        with open(activities, 'r', encoding = 'utf8') as ppfile:
            csvreader = csv.reader(ppfile, delimiter=';')
            header = next(csvreader)
            no_lead = []
            no_user = []
            no_campaign = []
            no_date = []
            for row in csvreader:
                # Test if date activity exist
                if(row[4]):
                    campaign = self.env['utm.campaign'].sudo().search([('name', 'like', row[0].strip() + '%')], limit=1)
                    if campaign:
                        user = self.env['res.users'].sudo().search([('name', 'like', row[1].strip() + '%')], limit=1)
                        if user:
                            lead = self.env['crm.lead'].sudo().search([('user_id', '=', user.id), ('campaign_id', '=', campaign.id), ('company_siren', 'like', row[2].strip() + '%'), ('company_siret', 'like', row[3].strip() + '%')], limit=1)
                            if lead:
                                date_activity = datetime.strptime(str(row[4]), "%d/%m/%Y").strftime("%Y-%m-%d")
                                lead._create_activity_user_if_not_exists('mail.mail_activity_data_call', date_deadline=date_activity, notes="", user_id=user.id)
                            else:
                                no_lead.append([row[1].strip(), row[2].strip(), row[3].strip()])
                        else:
                            no_user.append([row[1].strip(), row[2].strip(), row[3].strip()])
                    else:
                        no_campaign.append([row[1].strip(), row[2].strip(), row[3].strip()])
                else:
                    no_date.append([row[1].strip(), row[2].strip(), row[3].strip()])
            
            if no_lead:
                csv_buffer = io.StringIO()
                csv_writer = csv.writer(csv_buffer, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerows(no_lead)
                csv_buffer.seek(0)
                attachment = self.env['ir.attachment'].sudo().create({
                    'name': 'no_lead_activities.csv',
                    'type': 'binary',
                    'datas': base64.b64encode(csv_buffer.getvalue().encode()),
                })   
        return True

#### FEAT TO EMAILS
class FbiLeadEmailTo(models.Model):
    _name = 'fbi.crm.lead.emails.to'
    
    name = fields.Char(string="Description")
    remove_to = fields.Char(string="Remove destinataire in mails")
    add_to = fields.Char(string="Add destinataire in mails")
    user_ids = fields.Many2many('res.users', 'fbi_crm_lead_email_to_user_rel', 'mail_id', 'user_id', string='User')
    
### FEAT DATE DEADLINE
class FbiLeadDateDeadlineHistory(models.Model):
    _name = 'crm.lead.date.dealine.history'
    
    lead_id = fields.Many2one(comodel_name='crm.lead', string="Lead Reference", required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Text(string="Description")
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.context.get('user_id', self.env.user.id), index=True)
    date_change = fields.Datetime(string="Date", copy=False, default=fields.Datetime.now)
    old_date_activity = fields.Date(string="Old acticity date")
