# -*- coding: utf-8 -*-

# Author = 'Funceme'
# Credits = 'Leidinice Silva', 'Micael Costa, Duarte Junior'
# Maintainer = 'Funceme'
# Date = 24/01/2018  (dd/mm/aaaa)
# Comment = 'Este script foi desenvolvido dentro do Termo de Cooperação 
#        0050.0100467.16.9 entre Funceme e Petrobras sob o contexto do
#        Projeto Projeção de Vazão Natural Afluente com base na escala 
#        de tempo e clima.'
# Description = 'Compute best multicriteria distance of m1, m2 and m3.'


""" Compute best indices of m1, m2 and m3. """

import os
import glob
import calendar
import netCDF4
import texttable as tt
import xlsxwriter

from pylab import *
from netCDF4 import Dataset
from os.path import expanduser
from dateutil.relativedelta import *
from datetime import datetime, date
from hidropy.utils.hidropy_utils import lsname
from hidropy.utils.all_basins_dict_daily import basinsf

from PyFuncemeClimateTools.DefineDates import index_between_dates
from PyFuncemeClimateTools import ClimateStats as cs

from os.path import expanduser

HIDROPY_DIR = os.environ['HIDROPY_DIR']

var_name  = 'flow'
time_freq = 'daily'
data_base = 'ons_obs'
hind_obs1 = '19810101_20151231'
hind_obs2 = '20160101_*'
localdir  = '/io'

__author__ = "Leidinice Silva"
__email__  = "leidinice.silvae@funceme.br"
__date__   = "12/19/2017"
__description__ = "Compute best indices of m1, m2 and m3."


def define_dates(target_date):
    """ Define date start run list.
    """
    str_mon = target_date.strftime("%b").lower()

    start_rundate = '{0}{1:02d}{2:02d}'.format(target_date.year, target_date.month, target_date.day)

    return str_mon, start_rundate


def import_model_data(method, basin):
    """ Import model data.
    """
    
    model_2w = []
    model_4w = []
    
    for year in range(2009, 2014 + 1):
    
        for mon in range(1, 12 + 1):
            c = calendar.TextCalendar(calendar.MONDAY)
            
            for i in c.itermonthdays(year, mon):

                if i != 0:
                    day = date(year, mon, i)
                    
                    if day.weekday() == calendar.MONDAY:
                        date_monday = datetime(year, mon, i)
                        
                        str_mon, start_rundate = define_dates(date_monday)

                        dir_modelname  = "{0}{1}/{2}/smap_weather_climate/gfs05_rsm2008/{3}/{4}/{5}/{6}". \
                         format(HIDROPY_DIR, localdir, var_name, method, year, str_mon, macro)

                        file_modelname = "{0}/{1}_{2}_{3}_gfs05_rsm2008_fcst_{4}_smap_{5}.nc".format(dir_modelname,
								 var_name, time_freq, method, start_rundate, basin)
                        #print file_modelname
                        
                        try:
                            model_data = Dataset(os.path.join(dir_modelname, file_modelname))
                            var_data   = model_data.variables[var_name][:]
                            aux_2w   = np.nanmean(var_data[0:14])
                            aux_4w   = np.nanmean(var_data[14:])
                            
                        except:
                            var = np.nan

                        model_2w.append(aux_2w)
                        model_4w.append(aux_4w)


    model_data.close()

    model_2w_new = np.array(model_2w)
    model_4w_new = np.array(model_4w)


    return model_2w_new, model_4w_new


def import_ons_data(basin):
    """ Import obs data.
    """
    
    obs_2w = []
    obs_4w = []

    for year in range(2009, 2014 + 1):

        for mon in range(1, 12 + 1):
            c = calendar.TextCalendar(calendar.MONDAY)
            
            for i in c.itermonthdays(year, mon):

                if i != 0:
                    day = date(year, mon, i)

                    if day.weekday() == calendar.MONDAY:

                        date_saturday = datetime(year, mon, i)
                        date_saturday_new = date_saturday + relativedelta(days=-2)

                        date_final = date_saturday + relativedelta(days=+41)

                        str_mon, start_rundate = define_dates(date_saturday_new)
                        str_mon, end_rundate   = define_dates(date_final)

                        # 1981-2015 
                        file_name1 = '{0}{1}/{2}/ons_daily/1981-present/{3}/' \
                                     '{2}_{4}_{5}_{6}_{7}.nc'.format(HIDROPY_DIR,
                                                                     localdir,
                                                                     var_name,
                                                                     macro,
                                                                     time_freq,
                                                                     data_base,
                                                                     hind_obs1,
                                                                     basin)

                        ons_data1 = Dataset(file_name1)
                        ons1 = ons_data1.variables[var_name][:] 

                        date_start = os.path.basename(file_name1).split('_')[4]
                        date_end   = os.path.basename(file_name1).split('_')[5]
                        
                        i1, i2 = index_between_dates(date_start, date_end,
                                                     start_rundate, end_rundate,
                                                     'days')
                        aux = ons1[i1:i2+1]

                        obs_2w.append(np.nanmean(aux[0:14]))
                        obs_4w.append(np.nanmean(aux[14:]))
            
    ons_data1.close()

    ons_2w_new = np.squeeze(obs_2w)
    ons_4w_new = np.squeeze(obs_4w)

    return ons_2w_new, ons_4w_new


tab = tt.Texttable()
tab_inform = [[]]

# Target basin
macros = basinsf(macro=1)
header = ['Usina', 'dmcr_2w_m1', 'dmcr_2w_m2', 'dmcr_2w_m3', 'dmcr_4w_m1', 'dmcr_4w_m2', 'dmcr_4w_m3', 'best_2w', 'best_4w']
wb = xlsxwriter.Workbook('dict_daily_multicriteria_distance_all_methods_2009_2014_smap.xlsx')
ws = wb.add_worksheet('plan1')
ws.write_row(0, 0, header)
line = 1


for macro in macros:
    
    basins = basinsf(smap=macro)
  
    bas_new1 = []
    for bas1 in basins:
	if '_porto_estrela_inc' not in (bas1):
	    bas_new1.append(bas1)

    bas_new2 = []
    for bas2 in bas_new1:
        if '_ilha_solteira_equivalente' not in (bas2):
            bas_new2.append(bas2)
 
    bas_new3 = []
    for bas3 in bas_new2:
        if '_edgard_de_souza_inc' not in (bas3):
            bas_new3.append(bas3)
                                                                
    for basin in bas_new3:
    
        print 'Processing Basin: {0}'.format(basin)

        method = 'm1'
        model_2w_m1, model_4w_m1 = import_model_data(method, basin)

        method = 'm2'
        model_2w_m2, model_4w_m2 = import_model_data(method, basin)
        
        method = 'm3'
        model_2w_m3, model_4w_m3 = import_model_data(method, basin)
        try:
            ons_2w, ons_4w = import_ons_data(basin)

            #Multicriteria distance calculation
            empa_2w_m1 = np.nansum(np.abs(np.array(ons_2w) - np.array(model_2w_m1))/np.array(ons_2w)) / float(len(np.array(ons_2w)))
            empa_2w_m2 = np.nansum(np.abs(np.array(ons_2w) - np.array(model_2w_m2))/np.array(ons_2w)) / float(len(np.array(ons_2w)))
            empa_2w_m3 = np.nansum(np.abs(np.array(ons_2w) - np.array(model_2w_m3))/np.array(ons_2w)) / float(len(np.array(ons_2w)))
                
            empa_4w_m1 = np.nansum(np.abs(np.array(ons_4w) - np.array(model_4w_m1))/np.array(ons_4w)) / float(len(np.array(ons_4w)))
            empa_4w_m2 = np.nansum(np.abs(np.array(ons_4w) - np.array(model_4w_m2))/np.array(ons_4w)) / float(len(np.array(ons_4w)))
            empa_4w_m3 = np.nansum(np.abs(np.array(ons_4w) - np.array(model_4w_m3))/np.array(ons_4w)) / float(len(np.array(ons_4w)))

            nash_2w_m1 = 1 - np.nansum((np.array(model_2w_m1) - np.array(ons_2w))**2)/np.nansum((np.array(ons_2w) - np.nanmean(np.array(ons_2w)))**2)
            nash_2w_m2 = 1 - np.nansum((np.array(model_2w_m2) - np.array(ons_2w))**2)/np.nansum((np.array(ons_2w) - np.nanmean(np.array(ons_2w)))**2)
            nash_2w_m3 = 1 - np.nansum((np.array(model_2w_m3) - np.array(ons_2w))**2)/np.nansum((np.array(ons_2w) - np.nanmean(np.array(ons_2w)))**2)        

            nash_4w_m1 = 1 - np.nansum((np.array(model_4w_m1) - np.array(ons_4w))**2)/np.nansum((np.array(ons_4w) - np.nanmean(np.array(ons_4w)))**2)        
            nash_4w_m2 = 1 - np.nansum((np.array(model_4w_m2) - np.array(ons_4w))**2)/np.nansum((np.array(ons_4w) - np.nanmean(np.array(ons_4w)))**2)        
            nash_4w_m3 = 1 - np.nansum((np.array(model_4w_m3) - np.array(ons_4w))**2)/np.nansum((np.array(ons_4w) - np.nanmean(np.array(ons_4w)))**2)        
            
            dmcr_2w_m1 = np.sqrt((1 - nash_2w_m1)**2 + empa_2w_m1**2) 
            dmcr_2w_m2 = np.sqrt((1 - nash_2w_m2)**2 + empa_2w_m2**2) 
            dmcr_2w_m3 = np.sqrt((1 - nash_2w_m3)**2 + empa_2w_m3**2) 

            dmcr_4w_m1 = np.sqrt((1 - nash_4w_m1)**2 + empa_4w_m1**2) 
            dmcr_4w_m2 = np.sqrt((1 - nash_4w_m2)**2 + empa_4w_m2**2) 
            dmcr_4w_m3 = np.sqrt((1 - nash_4w_m3)**2 + empa_4w_m3**2)

            dmcr_str_2w  = ['m1', 'm2', 'm3']
            dmcr_list_2w = [dmcr_2w_m1, dmcr_2w_m2, dmcr_2w_m3]
            
            dmcr_str_4w  = ['m1', 'm2', 'm3']
            dmcr_list_4w = [dmcr_4w_m1, dmcr_4w_m2, dmcr_4w_m3]

            best_dmcr_2w = dmcr_str_2w[np.where(dmcr_list_2w == np.min(dmcr_list_2w))[-1][-1]]
            best_dmcr_4w = dmcr_str_4w[np.where(dmcr_list_4w == np.min(dmcr_list_4w))[-1][-1]]

            #table.append([basin, dmcr_2w_m1, dmcr_2w_m2, dmcr_2w_m3, dmcr_4w_m1, dmcr_4w_m2, dmcr_4w_m3, best_dmcr_2w, best_dmcr_4w])
            line_content = [basin, dmcr_2w_m1, dmcr_2w_m2, dmcr_2w_m3, dmcr_4w_m1, dmcr_4w_m2, dmcr_4w_m3, best_dmcr_2w, best_dmcr_4w]
            try:
                ws.write_row(line, 0, line_content)
            except:
                print line_content
                line_content = [basin]
                ws.write_row(line, 0, line_content)
            line += 1
            tab_inform.append([basin, dmcr_2w_m1, dmcr_2w_m2, dmcr_2w_m3, dmcr_4w_m1, dmcr_4w_m2, dmcr_4w_m3, best_dmcr_2w, best_dmcr_4w])
        except:
            pass
tab.add_rows(tab_inform)
tab.set_cols_align(['c', 'c', 'c', 'c', 'c', 'c', 'c', 'c', 'c'])
wb.close()

tab.header(['Usina', 'dmcr_2w_m1', 'dmcr_2w_m2', 'dmcr_2w_m3', 'dmcr_4w_m1', 'dmcr_4w_m2', 'dmcr_4w_m3', 'best_2w', 'best_4w'])

table = str(tab.draw())
dir_file  = "/home/musf/duarte/micael/"
file_name = '{0}dict_daily_multicriteria_distance_all_methods_2009_2014_teste_smap.py'.format(dir_file)
file_save = open(file_name, 'w')
print np.shape(table)
file_save.write(table)  
file_save.close()
exit()



