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

from src.france.model.data import QUIMEN

CHEF = QUIMEN['pref']
PART = QUIMEN['cref']
ENFS = [QUIMEN['enf1'], QUIMEN['enf2'], QUIMEN['enf3'], QUIMEN['enf4'], QUIMEN['enf5'], QUIMEN['enf6'], QUIMEN['enf7'], QUIMEN['enf8'], QUIMEN['enf9'], ]

ALL = [x[1] for x in QUIMEN]
        

def _tax_hab(zthabm, aah, aspa, asi, age, isf_tot, rfr, statmarit, nbptr, _P):
    '''
    Taxe d'habitation
    'men'
    '''
    P = _P.cotsoc.gen
    # Eligibilité:
    # - âgé de plus de 60 ans, non soumis à l'impôt de solidarité sur la fortune (ISF) en n-1
    # - veuf quel que soit votre âge et non soumis à l'impôt de solidarité sur la fortune (ISF) n-1
    # - titulaire de l'allocation de solidarité aux personnes âgées (Aspa)  ou de l'allocation supplémentaire d'invalidité (Asi),  
    # bénéficiaire de l'allocation aux adultes handicapés (AAH),  
    # atteint d'une infirmité ou d'une invalidité vous empêchant de subvenir à vos besoins par votre travail.
    concern = ((age >= 60) + (statmarit == 4))*(isf_tot  <= 0)  + (aspa > 0) + (asi > 0)
    
    seuil_th = P.plaf_th_1 + P.plaf_th_supp*(max_(0, (nbptr-1)/2))
    
    elig = concern*(rfr < seuil_th) + (asi > 0)  + (aspa > 0)
    
    return -zthabm*(elig)