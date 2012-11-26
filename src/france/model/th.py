# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

"""
openFisca, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

This file is part of openFisca.

    openFisca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    openFisca is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with openFisca.  If not, see <http://www.gnu.org/licenses/>.
"""
from __future__ import division
from numpy import ( maximum as max_, minimum as min_, logical_xor as xor_, 
                     logical_not as not_, round) 

from france.model.data import QUIMEN

CHEF = QUIMEN['pref']
PART = QUIMEN['cref']
ENFS = [QUIMEN['enf1'], QUIMEN['enf2'], QUIMEN['enf3'], QUIMEN['enf4'], QUIMEN['enf5'], QUIMEN['enf6'], QUIMEN['enf7'], QUIMEN['enf8'], QUIMEN['enf9'], ]

ALL = [x[1] for x in QUIMEN]
        

def _th(zthabm):
    '''
    Taxe d'habitation
    '''
    return -zthabm