'''
Created on Sep 5, 2012

@author: benjello
'''

from widgets.AggregateOuput import AggregateOutputWidget 
from Config import CONF

def get_config(widget):
    '''
    Sets some country specific parameters of the widgets
    '''
    country = CONF.get('simulation', 'country')
    if country == 'france':
        if isinstance(widget, AggregateOutputWidget):
            widget.varlist = ['irpp', 'ppe', 'af', 'cf', 'ars', 'aeeh', 'asf', 'aspa', 'aah', 'caah', 'rsa', 'aefa', 'api', 'logt']
            widget.selected_vars = set(['revdisp', 'nivvie']) 


if __name__ == '__main__':
    pass