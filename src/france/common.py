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
from numpy import (round, ceil, floor, maximum as max_, minimum as min_, 
                   logical_not as not_, arange)
from france.data import QUIFAM, QUIMEN
from france.pfam import nb_enf

CHEF = QUIFAM['chef']
PART = QUIFAM['part']
ENFS = [QUIFAM['enf1'], QUIFAM['enf2'], QUIFAM['enf3'], QUIFAM['enf4'], QUIFAM['enf5'], QUIFAM['enf6'], QUIFAM['enf7'], QUIFAM['enf8'], QUIFAM['enf9'], ]

ALL = [x[1] for x in QUIMEN]

def _uc(agem, _option = {'agem': ALL}):
    '''
    Calcule le nombre d'unités de consommation du ménage avec l'échelle de l'insee
    'men'
    '''
    uc_adt = 0.5
    uc_enf = 0.3
    uc = 0.5
    for agm in agem.itervalues():
        age = floor(agm/12)
        adt = (15 <= age) & (age <= 150)
        enf = (0  <= age) & (age <= 14)
        uc += adt*uc_adt + enf*uc_enf
    return uc

def _typ_men(isol, af_nbenf):
    '''
    type de menage
    'men'
    TODO: prendre les enfants du ménages et non ceux de la famille
    '''
    _0_kid = af_nbenf == 0
    _1_kid = af_nbenf == 1
    _2_kid = af_nbenf == 2
    _3_kid = af_nbenf >= 3
    
    return (0*(isol & _0_kid) + # Célibataire
            1*(not_(isol) & _0_kid) + # Couple sans enfants
            2*(not_(isol) & _1_kid) + # Couple un enfant
            3*(not_(isol) & _2_kid) + # Couple deux enfants
            4*(not_(isol) & _3_kid) + # Couple trois enfants et plus
            5*(isol & _1_kid) + # Famille monoparentale un enfant
            6*(isol & _2_kid) + # Famille monoparentale deux enfants
            7*(isol & _3_kid) ) # Famille monoparentale trois enfants et plus
            
    
def _revdisp_i(rev_trav, pen, rev_cap, ir_lps, psoc, ppe, impo):
    '''
    Revenu disponible
    'ind'
    '''
    return rev_trav + pen + rev_cap + ir_lps + psoc + ppe + impo

def _revdisp(revdisp_i, _option = {'revdisp_i': ALL}):
    '''
    Revenu disponible - ménage
    'men'
    '''
    r = 0
    for rev in revdisp_i.itervalues():
        r += rev
    return r

def _nivvie(revdisp, uc):
    '''
    Niveau de vie du ménage
    'men'
    '''
    return revdisp/uc

def _revnet_i(rev_trav, pen, rev_cap):
    '''
    Revenu net individuel
    'ind'
    '''
    return rev_trav + pen + rev_cap 

def _revnet(revnet_i, _option = {'revnet_i': ALL}):
    '''
    Revenu net du ménage
    'ind'
    '''
    r = 0
    for rev in revnet_i.itervalues():
        r += rev
    return r

def _nivvie_net(revnet, uc):
    '''
    Niveau de vie net du ménage
    'men'
    '''
    return revnet/uc


def _revini_i(rev_trav, pen, rev_cap, cotpat_contrib, cotsal_contrib):
    '''
    Revenu initial individuel
    'ind'
    '''
    return rev_trav + pen + rev_cap - cotpat_contrib - cotsal_contrib

def _revini(revini_i, _option = {'revini_i': ALL}):
    '''
    Revenu initial du ménage
    'ind'
    '''
    r = 0
    for rev in revini_i.itervalues():
        r += rev
    return r

def _nivvie_ini(revini, uc):
    '''
    Niveau de vie initial du ménage
    'men'
    '''
    return revini/uc




def _revprim_i(rev_trav, rev_cap, cotpat, cotsal):
    '''
    Revenu primaire individuel
    'ind'
    '''
    return rev_trav + rev_cap - cotpat - cotsal

def _revprim(revprim_i, _option = {'revprim_i': ALL}):
    '''
    Revenu net du ménage
    'ind'
    '''
    r = 0
    for rev in revprim_i.itervalues():
        r += rev
    return r


def _rev_trav(sal_net, rag, ric, rnc):
    '''Revenu du travail'''
    return sal_net + rag + ric + rnc

def _pen(chonet, rstnet, alr, alv, rto):
    '''Pensions'''
    return chonet + rstnet + alr + alv + rto

def _chonet(cho, csgchoi, crdscho):
    '''Chômage net'''
    return cho + csgchoi + crdscho

def _rstnet(rst, csgrsti, crdsrst):
    '''Retraites nettes'''
    return rst + csgrsti + crdsrst

def _cotsoc_bar(csg_cap_bar, prelsoc_cap_bar, crds_cap_bar):
    '''Cotisations sociales sur les revenus du capital imposés au barème'''
    return csg_cap_bar + prelsoc_cap_bar + crds_cap_bar

def _cotsoc_lib(csg_cap_lib, prelsoc_cap_lib, crds_cap_lib):
    '''Cotisations sociales sur les revenus du capital soumis au prélèvement libératoire'''
    return csg_cap_lib + prelsoc_cap_lib + crds_cap_lib

def _rev_cap(fon, rev_cap_bar, cotsoc_bar, rev_cap_lib, cotsoc_lib, imp_lib, rac):
    '''
    Revenus du patrimoine
    '''
    return fon + rev_cap_bar + cotsoc_bar + rev_cap_lib + cotsoc_lib + imp_lib + rac
 
def _psoc(pfam, mini, logt):
    '''
    Prestations sociales
    '''
    return pfam + mini + logt

def _pfam(af, cf, ars, aeeh, paje, asf, crds_pfam):
    '''
    Prestations familiales
    '''
    return af + cf + ars + aeeh + paje + asf + crds_pfam

def _mini(aspa, aah, caah, asi, rsa, aefa, api, ass):
    '''
    Minima sociaux
    '''
    return aspa + aah + caah + asi + rsa + aefa + api + ass

def _logt(apl, als, alf, alset, crds_lgtm):
    '''
    Prestations logement
    '''
    return apl + als + alf + alset + crds_lgtm

def _impo(irpp):
    '''
    Impôts directs
    '''
    return irpp

def _crds(crdssal, crdsrst, crdscho, crds_cap_bar, crds_cap_lib, crds_pfam, crds_lgtm):
    '''
    Contribution au remboursemetn de la dette sociale
    '''
    return crdssal + crdsrst + crdscho + crds_cap_bar + crds_cap_lib + crds_pfam + crds_lgtm
    
def _csg(csgsali, csgsald, csgchoi, csgchod, csgrsti, csg_cap_lib, csg_cap_bar):
    '''
    Contribution sociale généralisée
    '''
    return csgsali + csgsald + csgchoi + csgchod + csgrsti + csg_cap_lib


def _cotsoc_noncontrib(cotpat_noncontrib, cotsal_noncontrib, prelsoc_cap_lib, prelsoc_cap_bar):
    '''
    Cotisations sociales non contributives
    '''
    return cotpat_noncontrib + cotsal_noncontrib + prelsoc_cap_lib + prelsoc_cap_bar

from core.utils import mark_weighted_percentiles

def _decile(nivvie, champm, wprm):
    '''
    Décile de niveau de vie disponible
    'men'
    '''
    labels = arange(1,11)
    method = 2
    decile, values = mark_weighted_percentiles(nivvie, labels, wprm*champm, method, return_quantiles=True)
#    print values
#    print len(values)
#    print (nivvie*champm).min()
#    print (nivvie*champm).max()
#    print decile.min()
#    print decile.max()
#    print (nivvie*(decile==1)*champm*wprm).sum()/( ((decile==1)*champm*wprm).sum() )
    return decile*champm

def _decile_net(nivvie_net, champm, wprm):
    '''
    Décile de niveau de vie net
    'men'
    '''
    labels = arange(1,11)
    method = 2
    decile, values = mark_weighted_percentiles(nivvie_net, labels, wprm*champm, method, return_quantiles=True)
    return decile*champm



def _pauvre50(nivvie, champm, wprm):
    '''
    Indicatrice de pauvreté à 50% du niveau de vie median
    'men'
    '''
    labels = arange(1,3)
    method = 2
    percentile, values = mark_weighted_percentiles(nivvie, labels, wprm*champm, method, return_quantiles=True) 
    threshold = .5*values[1]
    return (nivvie <= threshold)*champm 

def _pauvre60(nivvie, champm, wprm):
    '''
    Indicatrice de pauvreté à 60% du niveau de vie median
    'men'
    '''
    labels = arange(1,3)
    method = 2
    percentile, values = mark_weighted_percentiles(nivvie, labels, wprm*champm, method, return_quantiles=True) 
    threshold = .6*values[1]
    return (nivvie <= threshold)*champm

