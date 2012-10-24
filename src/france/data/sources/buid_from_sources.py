'''
Created on Sep 19, 2012

@author: benjello
'''

from pandas import  HDFStore, read_csv, ExcelFile, concat

    
def csv2hdf5(csv_name, h5_name, dfname):
    table = read_csv(csv_name)
    store = HDFStore(h5_name)
    store[dfname] = table
    store.close() 

def test(h5_name, dfname):
    store = HDFStore(h5_name)
    table = store[dfname]
    print table
    print table.columns
    store.close()
    
        
def build_totals():
    h5_name = "../amounts.h5"
    store = HDFStore(h5_name)
    files = ['totals_pfam']
    first = True
    for xlsfile in files:
        xls = ExcelFile(xlsfile + '.xls')
        df = xls.parse('data', na_values=['NA'])
        print df
        if first:
            amounts_df = df
            first = False
        else:
            amounts_df = concat(amounts_df, df)

    amounts_df = amounts_df.set_index("var")
    print amounts_df.to_string()
    
    
    store['amounts'] = amounts_df
    store.close
    
def build_actualisation():
    h5_name = "../actualisation_groups.h5"
    store = HDFStore(h5_name)
    xls = ExcelFile('actualisation_groups.xls')
    df = xls.parse('data', na_values=['NA'])
    store['actualisation'] = df
    print df.to_string()
    print store
    from numpy import unique, isnan
    coeff_list = sorted(unique(df['coeff'].dropna()))
    print coeff_list
    groups = {}
    for coeff in coeff_list:
        groups[coeff] = list(df[ df['coeff']==coeff ]['var'])
    print groups
    
if __name__ == '__main__':
    
#    h5_name = 'survey.h5'    
#    dfname = 'survey_2006'
#    csv_name = "final06.csv"
#    
#    #csv2hdf5(csv_name, h5_name, dfname)
#    
#    test(h5_name, dfname)

    #build_actualisation()
    
    build_totals()