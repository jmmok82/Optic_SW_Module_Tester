from tkinter import filedialog
import pandas as pd
import openpyxl
import xlwings as xw 
from HR.lens_plotter import LensPlotter
from PIL import Image as PILImage

class LensWriter:
    def __init__(self):

        self.plotter = LensPlotter()


    def _make_wb(self):
        
        app = xw.App(visible=False)
        self.wb =  app.books.add()
        self.sht = self.wb.sheets[0]
        

    def _cell_style(self, cell, text, fill_color='C9E4CA', bold=True):
        def hex_to_rgb(hex_color):
            hex_color = hex_color.strip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        if isinstance(text, str):
            fill_color = '808080'
            bold = True
        else:
            fill_color = 'FFFFFF'
            bold = False

        cell.value = text
        cell.color = hex_to_rgb(fill_color)
        cell.api.Font.Bold = bold

        borders = cell.api.Borders
        for idx in [7, 8, 9, 10]:
            border = borders.Item(idx)
            border.LineStyle = 1  # xlContinuous
            border.Weight = 2     # xlThin

    # def _cell_style(self,cell,text,fill_color='C9E4CA', bold=True):

    #     border = Border(
    #         left=Side(style='thin'),
    #         right=Side(style='thin'),
    #         top=Side(style='thin'),
    #         bottom=Side(style='thin')
    #     )
        
    #     if isinstance(text, str):
    #         fill_color = '808080'
    #         bold = True
    #     else :
    #         fill_color = 'FFFFFF'
    #         bold = False

    #     fill = PatternFill(fgColor=fill_color, fill_type='solid')
    #     font = Font(bold=bold)
    #     cell.fill = fill
    #     cell.font = font
    #     cell.value = text
    #     cell.border = border

    def _lensinfo_to_excel(self, fno, efl):

        self._cell_style(self.sht.range((2,2)), 'Fno')
        self._cell_style(self.sht.range((3,2)), 'EFL')

        self._cell_style(self.sht.range((2,3)), fno)
        self._cell_style(self.sht.range((3,3)), efl)

    def _ri_to_excel(self,ri_df):



        if ri_df is not None:
            

            self._cell_style(self.sht.range((5,5)), 'Field')
            self._cell_style(self.sht.range((5,6)), 'RI(%)')

            for idx, value in enumerate(ri_df.index):
                self._cell_style(self.sht.range((6+idx,5)), str(ri_df.index[idx]))
                self._cell_style(self.sht.range((6+idx,6)), ri_df.loc[value,0])
            

    def _cra_to_excel(self,cra_df):

        
        if cra_df is not None:
            
            self._cell_style(self.sht.range((5,2)), 'Field')
            self._cell_style(self.sht.range((5,3)), 'CRA(deg)')

            for idx, value in enumerate(cra_df.index):            
                self._cell_style(self.sht.range((6+idx,2)), str(cra_df.index[idx]))
                self._cell_style(self.sht.range((6+idx,3)), cra_df.loc[value,0])

    def _plot_to_excel(self, all_data):

        self.plotter.plot_graph(all_data)

        # for col in 'KLMNOPQRST':
        #     self.ws1.column_dimensions[col].width = 10
        # for row in range(2, 17):
        #     self.ws1.row_dimensions[row].height = 15
        # width = sum(self.ws1.column_dimensions[col].width for col in 'KLMNOPQRST') * 1.333 * 6.5
        # height = sum(self.ws1.row_dimensions[row].height for row in range(2, 17)) * 1.333 * 2

        self.sht.range('k3').select()
        self.sht.api.Paste()
        # img = Image('plot_resized.png')
        # self.ws1.add_image(img, 'K2')


    def _dist_to_excel(self, dist_df):

        
        if dist_df is not None:
            
            self._cell_style(self.sht.range((5,8)), 'Field')
            self._cell_style(self.sht.range((5,9)), 'Distortion(%)')

            for idx, value in enumerate(dist_df.index):            
                self._cell_style(self.sht.range((6+idx,8)), str(dist_df.index[idx]))
                self._cell_style(self.sht.range((6+idx,9)), dist_df.loc[value,0])


    def _mtf_to_excel(self, mtf_df, freq):
                
        self._cell_style(self.sht.range((18,2)), 'MTF(%)')
        self._cell_style(self.sht.range((19,2)), 'Sag')
        self._cell_style(self.sht.range((20,2)), 'Tan')
        self.sht.range((21,2)).value = 'Freq'
        self.sht.range((21,3)).value = str(freq)+'lp/mm'

        for i in range(len(mtf_df.columns)):
            
            self._cell_style(self.sht.range((18,3+i)), mtf_df.columns[i])
            self._cell_style(self.sht.range((19,3+i)), round(mtf_df.loc['Sag'].values[i],3))
            self._cell_style(self.sht.range((20,3+i)), round(mtf_df.loc['Tan'].values[i],3))
        
        
    def _lsa_to_excel(self, lsa_df):

        if lsa_df is not None:
            
            self._cell_style(self.sht.range((23,2)), 'LSA')
            self._cell_style(self.sht.range((24,2)), 'Wavelength(nm)')
            self._cell_style(self.sht.range((24,3)), 'Focal Shift(um)')
           
            for i in range(len(lsa_df.index)):
                self._cell_style(self.sht.range((25+i,2)), lsa_df.values[i,0])
                self._cell_style(self.sht.range((25+i,3)), lsa_df.values[i,1])


    def _lateral_to_excel(self, lateral_df):

        
        
        if lateral_df is not None:
            
            self._cell_style(self.sht.range((23,5)), 'LateralColor(um)')
            self._cell_style(self.sht.range((24,5)), 'Field')
            
            field = (lateral_df.index.astype(float) / lateral_df.index.astype(float).max()).round(1).astype(str) + 'F'
            
            for i in range(len(lateral_df.columns)):
                self._cell_style(self.sht.range((24,6+i)), str(lateral_df.columns[i])+'nm')
            
            for j, idx in enumerate(lateral_df.index):
                self._cell_style(self.sht.range((25+j,5)), field[j])
                for i in range(len(lateral_df.columns)):
                    self._cell_style(self.sht.range((25+j,6+i)), lateral_df.loc[idx].iloc[i])
                    



    def run(self,all_data, fno):

        self.all_data = all_data      
        self.fno = float(fno)
                

        self._make_wb()
        self._lensinfo_to_excel(fno, all_data['efl']) ## fno / efl
        self._cra_to_excel(all_data['cra_report'])
        self._ri_to_excel(all_data['ri_report'])
        self._dist_to_excel(all_data['dist_report'])
        if all_data['aa_mtf'] is not None:
            self._mtf_to_excel(all_data['aa_mtf'], all_data['freq'])
        else :
            self._mtf_to_excel(all_data['mtf'], all_data['freq'])
        self._lsa_to_excel(all_data['lsa'])
        self._lateral_to_excel(all_data['lateral'])
        self._plot_to_excel(all_data)
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel 파일", "*.xlsx")])
        if filepath:
            self.wb.save(filepath)

        self.wb.close()

