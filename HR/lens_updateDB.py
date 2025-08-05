import os
from Common.connect_EDM import EdgeDriver
import xlwings as xw
from dateutil import parser
import tkinter as tk
import time

class UpdateLensDB:
    def __init__(self, logger):

        self.logger = logger
        self.app = None
        self.wb1 = None
        
        self.edge_run_once = False
        
    def _check_xls_open(self):
      
        try:
            self.app = xw.apps.active
            self.wb1 = [book for book in self.app.books if book.name.startswith('OpticLab')][0]
            self.run_once = False
            return True
        except:
            if not self.edge_run_once:
                self.edge_driver = EdgeDriver()
                self.edge_driver.run()
                self.edge_run_once = True  # 한 번 실행했음을 기록
            return False
        
        
    def wait_for_edm_file(self, timeout=90):

        self.logger.log_info('Start checking EDM open or not')
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self._check_xls_open():
                try:
                    self.logger.log_info('EDM file loaded')
                    return True
                except Exception as e:
                    self.logger.log_info(f'Error Checking OpticLabDB file : {e}')
                    self.wb1 = None
                
                         
            time.sleep(1)
        return False

        

    def update(self, all_data, fno):
        
        if self.wait_for_edm_file():
            self.fno = fno
            try:    
                title = 'Change Here'
                self._continue_update(all_data, title)
            except Exception as e:
                print('EDM update failed')
                

    def _continue_update(self, all_data, title):

        self.sheet = self.wb1.sheets['Lens']
        
        efl = all_data['efl']
        date, freq = all_data['date'], all_data['freq']
        if all_data['aa_mtf'] is not None:
            mtf = all_data['aa_mtf']
        else:
            mtf = all_data['mtf']
        date = all_data['date']
        fno = self.fno     
        sort = 'Lens'
        row_idx = 3
        cra = all_data['cra_report']
        ri = all_data['ri_report']
        dist = all_data['dist_report']
        lsa = all_data['lsa']
        lateral = all_data['lateral']

        while self.sheet.cells(row_idx, 1).value is not None:
            # ex_data = self.sheet.cells(row_idx, 5).value + self.sheet.cells(row_idx, 6).value
            # new_data = efl + self.freq
            # if ex_data == new_data:
            #     print('duplicate data')
            #     return False
            row_idx += 1

        self._write_data(row_idx, sort, title, date, fno, efl, freq, mtf)
        self._write_mtf_data(row_idx, mtf)
        self._write_cra_ri_distortion(row_idx, cra, ri, dist)
        self._write_lsa_lateral(row_idx, lsa, lateral)

        self.wb1.save()
        # self.wb1.close()
        return True

    def _write_data(self, row_idx, sort, title, date_form, fno, efl, freq, mtf):

        self.sheet.cells(row_idx, 1).value = sort
        self.sheet.cells(row_idx, 2).value = title
        self.sheet.cells(row_idx, 3).value = date_form
        self.sheet.cells(row_idx, 4).value = fno
        self.sheet.cells(row_idx, 5).value = efl
        self.sheet.cells(row_idx, 6).value = freq

    def _write_mtf_data(self, row_idx, mtf):

        self.sheet.cells(row_idx, 7).value = round(mtf.loc['Sag'].iloc[9], 3)
        self.sheet.cells(row_idx, 17).value = round(mtf.loc['Tan'].iloc[9], 3)
        for i in range(9):
            self.sheet.cells(row_idx, 8 + i).value = round((mtf.loc['Sag'].iloc[10 + i] + mtf.loc['Sag'].iloc[8 - i]) / 2, 3)
            self.sheet.cells(row_idx, 18 + i).value = round((mtf.loc['Tan'].iloc[10 + i] + mtf.loc['Tan'].iloc[8 - i]) / 2, 3)

    def _write_cra_ri_distortion(self, row_idx, cra, ri, dist):
        
        for i in range(11):
            self.sheet.cells(row_idx, 27 + i).value = cra.iloc[i, 0]
            self.sheet.cells(row_idx, 38 + i).value = ri.iloc[i, 0]
            self.sheet.cells(row_idx, 49 + i).value = dist.iloc[i, 0]

    def _write_lsa_lateral(self, row_idx, lsa, lateral):
        
        wavelength = sorted(lateral.columns)
        for idx, k in enumerate(wavelength):
            self.sheet.cells(row_idx, 60 + idx).value = float(lsa[lsa['Wavelength'] == k]['Focal Shift'].iloc[0])
            self.sheet.cells(row_idx, 65 + idx * 10).value = float(lateral[k].iloc[10])
            for i in range(1, 10):
                u = float(lateral[k].iloc[10 + i])
                d = float(lateral[k].iloc[10 - i])
                self.sheet.cells(row_idx, 65 + idx * 10 + i).value = round((u + d), 3)



if __name__ == "__main__":
    pass
