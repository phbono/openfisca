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


from datetime import date
import pickle
import os

from src.qt.QtGui import (QGroupBox, QVBoxLayout, QDialog, QLabel, QDateEdit, QComboBox, QSpinBox, 
                          QDoubleSpinBox, QPushButton, QApplication, QFileDialog, QMessageBox, 
                          QDialogButtonBox)
from src.qt.QtCore import QObject, SIGNAL, SLOT, QDate, Qt, QVariant

from src.views.ui_composition import Ui_Menage
from src.views.ui_logement import Ui_Logement
from src.widgets.InfoComp import InfoComp
from src.widgets.Declaration import Declaration

from src.core.config import CONF, get_icon
from src.plugins.__init__ import OpenfiscaPluginWidget, PluginConfigPage
from src.core.utils_old import of_import
from src.core.baseconfig import get_translation
_ = get_translation('composition', 'src.plugins.scenario') # TODO:


class S:
    name = 0
    birth = 1
    decnum = 2
    decpos = 3
    decbtn = 4
    famnum = 5
    fampos = 6


class CompositionConfigPage(PluginConfigPage):
    def __init__(self, plugin, parent):
        PluginConfigPage.__init__(self, plugin, parent)
        self.get_name = lambda: _("Composition")
        
    def setup_page(self):

        axis_group = QGroupBox(_("Axis"))
#        choices = [('cvs', 'csv'),
#                   ('xls', 'xls'),]
#        table_format = self.create_combobox(_('Table export format'), choices, 'format')
        
        #xaxis          
        layout = QVBoxLayout()
#        layout.addWidget(axis_format)
        axis_group.setLayout(layout)
        
        vlayout = QVBoxLayout()
        vlayout.addWidget(axis_group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)


class CompositionWidget(OpenfiscaPluginWidget, Ui_Menage):    
    """
    Scenario Graph Widget
    """
    CONF_SECTION = 'composition'
    CONFIGWIDGET_CLASS = CompositionConfigPage
    DISABLE_ACTIONS_WHEN_HIDDEN = False

    def __init__(self, simulation_scenario = None, parent = None):
        super(CompositionWidget, self).__init__(parent)
        self.setupUi(self)
        if parent is not None:
            self.parent = parent
        if simulation_scenario is not None:
            self.set_scenario(simulation_scenario)

        self.setLayout(self.verticalLayout)
        # Initialize xaxes
        country = CONF.get('parameters','country')
        build_axes = of_import('utils','build_axes', country)
        axes = build_axes(country)
        xaxis = CONF.get('composition', 'xaxis')
        
        axes_names = []
        for axe in axes:
            self.xaxis_box.addItem(axe.label, QVariant(axe.name))
            axes_names.append(axe.name)
                        
        self.xaxis_box.setCurrentIndex(axes_names.index(xaxis))            
        
        # Initialize maxrev # make it country dependant  
        self.maxrev_box.setMinimum(0)
        self.maxrev_box.setMaximum(100000000)
        self.maxrev_box.setSingleStep(1000)
        self.maxrev_box.setSuffix(u"€")
        maxrev = CONF.get('composition', 'maxrev')
        self.maxrev_box.setValue(maxrev)
        
        self.connect(self.open_btn, SIGNAL('clicked()'), self.openScenario)
        self.connect(self.save_btn, SIGNAL('clicked()'), self.saveScenario)
        self.connect(self.add_btn, SIGNAL('clicked()'), self.addPerson)
        self.connect(self.rmv_btn, SIGNAL('clicked()'), self.rmvPerson)
        self.connect(self.lgt_btn, SIGNAL('clicked()'), self.openLogement)
        self.connect(self.inf_btn, SIGNAL('clicked()'), self.openInfoComp)
        self.connect(self.reset_btn, SIGNAL('clicked()'), self.resetScenario)
        self.connect(self.xaxis_box, SIGNAL('currentIndexChanged(int)'), self.set_xaxis)
        self.connect(self.maxrev_box, SIGNAL('valueChanged(int)'), self.set_maxrev)
        self.connect(self, SIGNAL('compoChanged()'), self.changed)
        self._listPerson = []
        self.addPref()
        self.rmv_btn.setEnabled(False)
        self.emit(SIGNAL("ok()"))
        
    #------ Public API ---------------------------------------------    

    def set_scenario(self, scenario_simulation):
        """
        Set scenario_simualtion
        """
        from datetime import datetime
        
        xaxis = CONF.get('composition', 'xaxis')
        maxrev = CONF.get('composition', 'maxrev')
        nmen = CONF.get('composition', 'nmen')
        self.nmen = nmen
        country = CONF.get('parameters', 'country')
        datesim = CONF.get('parameters', 'datesim')
        #print date_str
        #datesim = datetime.strptime(date_str ,"%Y-%m-%d").date()
        year = datesim.year
        self.scenario_simulation = scenario_simulation
        self.scenario_simulation.set_config(year = year, country = country, xaxis = xaxis, 
                                            nmen = self.nmen, maxrev = maxrev, reforme = False, mode ='bareme')
        self.scenario_simulation.set_param()
        self.scenario = self.scenario_simulation.scenario
        self.parent.scenario = self.scenario

    def set_xaxis(self):
        '''
        Sets the varying variable of the scenario
        '''
        widget = self.xaxis_box
        if isinstance(widget, QComboBox):
            data  = widget.itemData(widget.currentIndex())
            xaxis = unicode(data.toString())
            self.scenario.xaxis = xaxis
            CONF.set('composition', 'xaxis', xaxis)
        self.emit(SIGNAL('compoChanged()'))
    
    def set_maxrev(self):
        '''
        Sets the varying variable of the scenario
        '''
        widget = self.maxrev_box
        if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
            maxrev = widget.value()
            self.scenario.maxrev = maxrev
            CONF.set('simulation', 'maxrev', maxrev) 
        self.emit(SIGNAL('compoChanged()'))

    def changed(self):
        self.disconnectAll()
        self.scenario.genNbEnf()
        self.populate()
        self.emit(SIGNAL('changed()'))
        self.connectAll()
        
    def nbRow(self):
        return self.scenario.nbIndiv()

    def populate(self):
        self.populateBirth()
        self.populateQuifoyCombo()
        self.populateFoyerCombo()
        self.populateQuifamCombo()
        self.populateFamilleCombo()

    def populateBirth(self):
        for noi, vals in self.scenario.indiv.iteritems():
            birth = QDate(vals['birth'])
            self._listPerson[noi][S.birth].setDate(birth)
        
    def populateFoyerCombo(self):
        declarKeys = self.scenario.declar.keys()
        for noi, vals in self.scenario.indiv.iteritems():
            noidec = vals['noidec']
            box = self._listPerson[noi][S.decnum]
            box.clear()
            button = self._listPerson[noi][S.decbtn]
            button.setText('Foyer %d' % (noidec+1))
            if vals['quifoy'] == 'vous':
                box.addItems(['%d' % (noidec+1)])
                button.setEnabled(True)
            else :
                box.addItems(['%d' % (k+1) for k in declarKeys])
                button.setEnabled(False)
                box.setCurrentIndex(declarKeys.index(noidec))

    def populateQuifoyCombo(self):
        for noi, vals in self.scenario.indiv.iteritems():
            quifoy = vals['quifoy']
            # retrieve the foyer combobox of individu number noi
            box = self._listPerson[noi][S.decpos]
            # set the combobox to 'vous' 'conj' or 'pac'
            if   quifoy == 'vous': box.setCurrentIndex(0)
            elif quifoy == 'conj': box.setCurrentIndex(1)
            elif quifoy[:3] == 'pac': box.setCurrentIndex(2)

    def populateFamilleCombo(self):
        familleKeys = self.scenario.famille.keys()
        for noi, vals in self.scenario.indiv.iteritems():
            noichef = vals['noichef']
            box = self._listPerson[noi][S.famnum]
            box.clear()
            if vals['quifam'] == 'parent 1':
                box.addItems(['%d' % (noichef+1)])
            else :
                box.addItems(['%d' % (k+1) for k in familleKeys])
                box.setCurrentIndex(familleKeys.index(noichef))

    def populateQuifamCombo(self):
        for noi, vals in self.scenario.indiv.iteritems():
            quifam = vals['quifam']
            # retrieve the foyer combobox of individu number noi
            box = self._listPerson[noi][S.fampos]
            # set the combobox to 'parent 1' 'parent 2' or 'enfant'
            if   quifam == 'chef': box.setCurrentIndex(0)
            elif quifam == 'part': box.setCurrentIndex(1)
            elif quifam[:3] == 'enf': box.setCurrentIndex(2)

    def birthChanged(self, date):
        senderNoi = int(self.sender().objectName()[3])
        self.scenario.indiv[senderNoi].update({'birth': date.toPyDate()})
        self.emit(SIGNAL('compoChanged()'))

    def foyerChanged(self):
        sender = self.sender()
        noi = int(sender.objectName()[3])
        newfoyer = int(sender.currentText()[-1])-1
        self.scenario.modify(noi, newFoyer = newfoyer)
        self.emit(SIGNAL('compoChanged()'))

    def quifoyChanged(self, newQuifoy):
        senderNoi = int(self.sender().objectName()[3])
        self.scenario.modify(senderNoi, newQuifoy = newQuifoy)
        self.emit(SIGNAL('compoChanged()'))

    def familleChanged(self):
        sender = self.sender()
        noi = int(sender.objectName()[3])
        newfamille = int(sender.currentText()[-1])-1
        self.scenario.modifyFam(noi, newFamille = newfamille)
        self.emit(SIGNAL('compoChanged()'))

    def quifamChanged(self, newFam):
        if newFam == 'parent 1' : qui = 'chef'
        elif newFam == 'parent 2' : qui = 'part'
        elif newFam == 'enfant' : qui = 'enf'
        senderNoi = int(self.sender().objectName()[3])
        self.scenario.modifyFam(senderNoi, newQuifam = qui)
        self.emit(SIGNAL('compoChanged()'))
        

    def addPref(self):
        noi = 0
        self._listPerson.append([QLabel('%d' % (noi+1), self),
                                 QDateEdit(self),
                                 QComboBox(self),
                                 QComboBox(self),
                                 QPushButton(self),
                                 QComboBox(self),
                                 QComboBox(self)])

        temp = self._listPerson[0]

        temp[S.birth].setDisplayFormat(QApplication.translate("Page01", "dd MMM yyyy", None, QApplication.UnicodeUTF8))
        temp[S.birth].setObjectName('Bir%d' % noi)
        temp[S.birth].setCurrentSection(QDateEdit.YearSection)

        temp[S.decpos].setObjectName('Dec%d' % noi)
        temp[S.decpos].addItems(['vous'])
        temp[S.decpos].setEnabled(False)

        temp[S.decnum].setObjectName('Foy%d' % noi)
        temp[S.decnum].setEnabled(False)

        temp[S.fampos].addItems(['parent 1'])            
        temp[S.fampos].setObjectName('Fam%d' % noi)
        temp[S.fampos].setEnabled(False)

        temp[S.famnum].setObjectName('Fam%d' % noi)
        temp[S.famnum].setEnabled(False)

        temp[S.decbtn].setObjectName('But%d' % noi)

        for i in xrange(7):
            self.gridLayout.addWidget(temp[i], noi + 2, i)
            self.gridLayout.setAlignment(temp[i], Qt.AlignCenter)

        self.emit(SIGNAL('compoChanged()'))
                
    def addPerson(self):
        noi = self.nbRow()
        self.addRow()
        if noi == 1: self.scenario.addIndiv(noi, birth = date(1975,1,1), quifoy = 'conj', quifam = 'part')
        else:        self.scenario.addIndiv(noi, birth = date(2000,1,1), quifoy = 'pac' , quifam = 'enf')
        
        self.emit(SIGNAL('compoChanged()'))
            
    def addRow(self):
        noi = len(self._listPerson)
        self._listPerson.append([QLabel('%d' % (noi+1), self),
                                 QDateEdit(self),
                                 QComboBox(self),
                                 QComboBox(self),
                                 QPushButton(self),
                                 QComboBox(self),
                                 QComboBox(self)])
        temp = self._listPerson[-1]

        temp[S.birth].setDisplayFormat(QApplication.translate("Page01", "dd MMM yyyy", None, QApplication.UnicodeUTF8))
        temp[S.birth].setObjectName('Bir%d' % noi)
        temp[S.birth].setCurrentSection(QDateEdit.YearSection)

        temp[S.decpos].setObjectName('Dec%d' % noi)
        temp[S.decpos].addItems(['vous', 'conj', 'pac'])

        temp[S.decnum].setObjectName('Foy%d' % noi)

        temp[S.fampos].setObjectName('Fam%d' % noi)
        temp[S.fampos].addItems(['parent 1', 'parent 2', 'enfant'])

        temp[S.famnum].setObjectName('Fam%d' % noi)

        temp[S.decbtn].setObjectName('But%d' % noi)
        
        for i in xrange(7):
            self.gridLayout.addWidget(temp[i], noi +2, i)
            self.gridLayout.setAlignment(temp[i], Qt.AlignCenter)


        self.rmv_btn.setEnabled(True)
        if len(self.scenario.indiv) == 9:
            self.add_btn.setEnabled(False)

    def rmvPerson(self, noi = None):
        if noi == None: 
            noi = self.nbRow() - 1
        self.scenario.rmvIndiv(noi)
        self.rmvRow()
        self.add_btn.setEnabled(True)

        self.emit(SIGNAL('compoChanged()'))

    def rmvRow(self):
        '''
        Enlève le dernier individu et l'efface dans le foyer
        '''
        toDel = self._listPerson.pop()
        for widget in toDel:
            widget.setParent(None)
        if len(self.scenario.indiv) == 1: self.rmv_btn.setEnabled(False)


    def resetScenario(self):
        '''
        Resets scenario
        '''
        while self.nbRow() > 1:
            self.rmvPerson()
        self.scenario_simulation.reset_scenario
        self.emit(SIGNAL('compoChanged()'))
        
    def openDeclaration(self):
        noi = int(self.sender().objectName()[3])
        self.scenario.genNbEnf()
        msg = self.scenario.check_consistency()
        if msg:
            QMessageBox.critical(self, u"Ménage non valide",
                                 msg, 
                                 QMessageBox.Ok, QMessageBox.NoButton)
            return False
        self._declaration = Declaration(self, noi)
        self._declaration.exec_()
        self.emit(SIGNAL('compoChanged()'))

    def openLogement(self):
        self._logement = Logement(self.scenario, self)
        self._logement.exec_()
        self.emit(SIGNAL('compoChanged()'))

    def openInfoComp(self):
        self._infocomp = InfoComp(self.scenario, self)
        self._infocomp.exec_()
        self.emit(SIGNAL('compoChanged()'))
        
    def disconnectAll(self):
        for person in self._listPerson:
            QObject.disconnect(person[S.birth],  SIGNAL('dateChanged(QDate)'), self.birthChanged)
            QObject.disconnect(person[S.decpos], SIGNAL('currentIndexChanged(QString)'), self.quifoyChanged)
            QObject.disconnect(person[S.decnum], SIGNAL('currentIndexChanged(int)'), self.foyerChanged)
            QObject.disconnect(person[S.fampos], SIGNAL('currentIndexChanged(QString)'), self.quifamChanged)
            QObject.disconnect(person[S.famnum], SIGNAL('currentIndexChanged(int)'), self.familleChanged)
            QObject.disconnect(person[S.decbtn], SIGNAL('clicked()'), self.openDeclaration)
            
    def connectAll(self):
        for person in self._listPerson:
            QObject.connect(person[S.birth],  SIGNAL('dateChanged(QDate)'), self.birthChanged)
            QObject.connect(person[S.decpos], SIGNAL('currentIndexChanged(QString)'), self.quifoyChanged)
            QObject.connect(person[S.decnum], SIGNAL('currentIndexChanged(int)'), self.foyerChanged)
            QObject.connect(person[S.fampos], SIGNAL('currentIndexChanged(QString)'), self.quifamChanged)
            QObject.connect(person[S.famnum], SIGNAL('currentIndexChanged(int)'), self.familleChanged)
            QObject.connect(person[S.decbtn], SIGNAL('clicked()'), self.openDeclaration)

    def openScenario(self):
        cas_type_dir = CONF.get('paths', 'cas_type_dir')
        fileName = QFileDialog.getOpenFileName(self,
                                               u"Ouvrir un cas type", 
                                               cas_type_dir, 
                                               u"Cas type OpenFisca (*.ofct)")
        if not fileName == '':
            n = len(self.scenario.indiv)
            try:
                self.scenario.openFile(fileName)
                while n < self.nbRow():
                    self.addRow()
                    n += 1
                while n > self.nbRow(): 
                    self.rmvRow()
                    n -= 1
                self.emit(SIGNAL('compoChanged()'))
                self.emit(SIGNAL("ok()"))
            except Exception, e:
                QMessageBox.critical(
                    self, "Erreur", u"Erreur lors de l'ouverture du fichier : le fichier n'est pas reconnu",
                    QMessageBox.Ok, QMessageBox.NoButton)

        
    def saveScenario(self):
        cas_type_dir = CONF.get('paths', 'cas_type_dir')
        default_fileName = os.path.join(cas_type_dir, 'sans-titre')
        fileName = QFileDialog.getSaveFileName(self,
                                               u"Sauver un cas type", 
                                               default_fileName, 
                                               u"Cas type OpenFisca (*.ofct)")
        if not fileName == '':
            self.scenario.saveFile(fileName)


    #------ OpenfiscaPluginMixin API ---------------------------------------------
    #------ OpenfiscaPluginWidget API ---------------------------------------------

    def get_plugin_title(self):
        """
        Return plugin title
        Note: after some thinking, it appears that using a method
        is more flexible here than using a class attribute
        """
        return "Table"

    
    def get_plugin_icon(self):
        """
        Return plugin icon (QIcon instance)
        Note: this is required for plugins creating a main window
              (see SpyderPluginMixin.create_mainwindow)
              and for configuration dialog widgets creation
        """
        return get_icon('OpenFisca22.png')
            
    def get_plugin_actions(self):
        """
        Return a list of actions related to plugin
        Note: these actions will be enabled when plugin's dockwidget is visible
              and they will be disabled when it's hidden
        """
        from src.core.utils.qthelpers import create_action
        

        self.open_action = create_action(self, _("&Open..."),
                icon='fileopen.png', tip=_("Open composition file"),
                triggered=self.load)
        self.register_shortcut(self.open_action, context="Editor",
                               name="Open file", default="Ctrl+O")
        self.save_action = create_action(self, _("&Save"),
                icon='filesave.png', tip=_("Save current file"),
                triggered=self.save)
        self.register_shortcut(self.save_action, context="Editor",
                               name="Save file", default="Ctrl+S")

#        Tabbbify Composition widget to compare two menage
#        self.save_all_action = create_action(self, _("Sav&e all"),
#                icon='save_all.png', tip=_("Save all opened files"),
#                triggered=self.save_all)
#        self.register_shortcut(self.save_all_action, context="Editor",
#                               name="Save all", default="Ctrl+Shift+S")
#        save_as_action = create_action(self, _("Save &as..."), None,
#                'filesaveas.png', _("Save current file as..."),
#                triggered=self.save_as)

        self.file_menu_actions = [self.open_action, self.save_action,
                             self.save_all_action]
    
        return self.file_menu_actions
    
    def register_plugin(self):
        """
        Register plugin in OpenFisca's main window
        """
        self.main.add_dockwidget(self)


    def refresh_plugin(self):
        '''
        Update Scenario Table
        '''
        pass
    
    def closing_plugin(self, cancelable=False):
        """
        Perform actions before parent main window is closed
        Return True or False whether the plugin may be closed immediately or not
        Note: returned value is ignored if *cancelable* is False
        """
        return True

#
#        SpyderPluginWidget.visibility_changed(self, enable)
#        if self.dockwidget.isWindow():
#            self.dock_toolbar.show()
#        else:
#            self.dock_toolbar.hide()
#        if enable:
#            self.refresh_plugin()


def get_zone(code, filename = None):
    '''
    Gets commune name and zone apl from postal code
    '''
    if filename is None:
        code_file = open('france/data/code_apl', 'r')
    else:
        code_file = open(filename, 'r')
    code_dict = pickle.load(code_file)
    code_file.close()
    if str(code) in code_dict:
        commune = code_dict[str(code)]
        return commune
    else:
        return None
    

class Logement(QDialog, Ui_Logement):
    def __init__(self, scenario, parent = None):
        super(Logement, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.scenario = scenario
        self.spinCP.setValue(scenario.menage[0]['code_postal'])
        self.spinLoyer.setValue(scenario.menage[0]['loyer'])
        self.comboSo.setCurrentIndex(scenario.menage[0]['so']-1) # -1 because 0 is "non renseigné"
        self.spinTH.setValue(scenario.menage[0]['zthabm']) # -1 because 0 is "non renseigné"                

        def update_ville(code):        
            commune = get_zone(code)
            if commune is not None:
                self.bbox.button(QDialogButtonBox.Ok).setEnabled(True)
            else:
                commune = ("Ce code postal n'est pas reconnu", '2')
                self.bbox.button(QDialogButtonBox.Ok).setEnabled(False)
                
            self.commune.setText(commune[0])
            self.spinZone.setValue(int(commune[1]))

        update_ville(self.spinCP.value())

        self.connect(self.spinCP, SIGNAL('valueChanged(int)'), update_ville)
        
        def update_th(value):
            self.spinTH.setValue(int(value))
        
        self.connect(self.spinTH, SIGNAL('valueChanged(int)'), update_th)
        
        def so_changed(value):
            if value in (0,1):
                self.spinLoyer.setValue(0)
                self.spinLoyer.setEnabled(False)
            else:
                self.spinLoyer.setValue(500)
                self.spinLoyer.setEnabled(True)
                
        self.connect(self.comboSo, SIGNAL('currentIndexChanged(int)'), so_changed)
        self.connect(self.bbox, SIGNAL("accepted()"), SLOT("accept()"))
        self.connect(self.bbox, SIGNAL("rejected()"), SLOT("reject()"))
        
        
        
    def accept(self):
        self.scenario.menage[0].update({'loyer': int(self.spinLoyer.value()),
                                        'so': int(self.comboSo.currentIndex()+1), # +1 because 0 is "non renseigné"
                                        'zone_apl': int(self.spinZone.value()),
                                        'code_postal': int(self.spinCP.value()),
                                        'zthabm' : int(self.spinTH.value())})
        QDialog.accept(self)


