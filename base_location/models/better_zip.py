# -*- coding: utf-8 -*-
# Copyright 2016 Nicolas Bessi, Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class BetterZip(models.Model):
    '''City/locations completion object'''

    _name = "res.better.zip"
    _description = __doc__
    _order = "name asc"

    def domain_city_id(self):
        if self.country_id:
            return [('country_id', '=', self.country_id.id)]
        return ""

    def domain_state_id(self):
        if self.country_id:
            return [('country_id', '=', self.country_id.id)]
        return ""

    name = fields.Char('ZIP')
    code = fields.Char(
        'City Code',
        size=64,
        help="The official code for the city"
    )
    city = fields.Char('City', required=True)
    city_id = fields.Many2one(
        'res.city',
        'City',
    )
    state_id = fields.Many2one(
        'res.country.state',
        'State',
    )
    country_id = fields.Many2one('res.country', 'Country')
    enforce_cities = fields.Boolean(
        related='country_id.enforce_cities',
        readonly=True,
    )
    latitude = fields.Float()
    longitude = fields.Float()

    @api.multi
    @api.depends('name', 'city', 'state_id', 'country_id')
    def name_get(self):
        result = []
        for rec in self:
            name = []
            if rec.name:
                name.append(rec.name)
            name.append(rec.city)
            if rec.state_id:
                name.append(rec.state_id.name)
            if rec.country_id:
                name.append(rec.country_id.name)
            result.append((rec.id, ", ".join(name)))
        return result

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id:
            if self.state_id.country_id != self.country_id:
                self.state_id = False
            if self.city_id.country_id != self.country_id:
                self.city_id = False
            return {
                'domain': {
                    'state_id': self.domain_city_id(),
                    'city_id': self.domain_state_id(),
                }
            }
        else:
            self.state_id = False
            self.city_id = False
            return {
                'domain': {
                    'state_id': False,
                    'city_id': False,
                }
            }

    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id:
            self.city = self.city_id.name
            self.country_id = self.city_id.country_id
            if not self.country_id.enforce_cities:
                self.state_id = self.city_id.state_id
                self._onchange_state_id()

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id:
            self.country_id = self.state_id.country_id

    @api.constrains('state_id', 'country_id', 'city_id')
    def constrains_country(self):
        for rec in self:
            if rec.state_id and rec.state_id.country_id != \
                    rec.country_id:
                raise ValidationError(_(
                    "The country of the state differs from the country in "
                    "location %s") % rec.name)
            if rec.city_id and rec.city_id.country_id \
                    != rec.country_id:
                raise ValidationError(_(
                    "The country of the city differs from the country in "
                    "location %s") % rec.name)
            if rec.city_id and rec.city_id.state_id \
                    != rec.state_id:
                raise ValidationError(_(
                    "The state of the city differs from the state in "
                    "location %s") % rec.name)
