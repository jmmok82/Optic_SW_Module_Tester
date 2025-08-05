from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt
import sys
from Common.eventlog import LogEvents
from Module.Module_analyzer_function import SFRAnalyzer, SFRPlotter, ShadingAnalyzer,SFR_Multi_Analyzer
from Module.Module_updateDB import UpdateLModuleDB
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from HR.lens_handler import HRWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.module_tester = SFRAnalyzer()
        self.module_plotter = SFRPlotter()
        self.shading_analyzer = ShadingAnalyzer()
        self.logger = LogEvents(callback = self.log_event)
        self.module_multi = SFR_Multi_Analyzer(logger = self.logger)
        self.update_db = UpdateLModuleDB(self.logger)

        uic.loadUi("opticlab_ui.ui", self) 
        self.resize(2000, 1000)
        ## Load HR Handler

        self.hr_handler = HRWidget(self, self.logger)
        
        ### Set ModuleTester Variable
        
        self.SFR_dfs = None
        self.AA_SFR_dfs = None
        self.shading_dfs = None
        self.pixel_size = None
        self.sensitivity = None
        self.pixel_x = None
        self.pixel_y = None
        self.freq = None
        self.graph_check = False
        self.SFR_multi_result = None

        ### Set ModuleTester UI
           
        self.pixel_x_line.setValidator(QIntValidator(1, 99999, self))
        self.pixel_x = int(self.pixel_x_line.text())
        self.pixel_x_line.setProperty('varname', 'pixel_x')
        self.pixel_x_line.textChanged.connect(self.on_value_changed)

        
        self.pixel_y_line.setValidator(QIntValidator(1, 99999, self))
        self.pixel_y = int(self.pixel_y_line.text())
        self.pixel_y_line.setProperty('varname', 'pixel_y')
        self.pixel_y_line.textChanged.connect(self.on_value_changed)

        self.pixelsize_line.setValidator(QDoubleValidator(0.1, 10, 2, self))
        self.pixel_size = float(self.pixelsize_line.text())
        self.pixelsize_line.setProperty('varname', 'pixel_size')
        self.pixelsize_line.textChanged.connect(self.on_value_changed)
        
        self.sensitivity_line.setValidator(QDoubleValidator(0, 10, 10, self))
        self.sensitivity = float(self.sensitivity_line.text())
        self.sensitivity_line.textChanged.connect(self.on_value_changed)
        self.sensitivity_line.setProperty('varname', 'sensitivity')              
        
        self.peakmin_SFR_line.setValidator(QIntValidator(0, 100, self))
        self.peak_min_guide = int(self.peakmin_SFR_line.text())
        self.peakmin_SFR_line.textChanged.connect(self.on_value_changed)
        self.peakmin_SFR_line.setProperty('varname', 'peak_min_guide')


        self.sfr_checkboxes = [
            self.convertDAC_check,
            self.tilt_correction_check,
            self.SFR_plot_btn,
            self.TF_plot_btn,
            self.fp_plot_btn,
            self.report_plot_btn,
            self.module_update_btn,
        ]
        self.SFR_checksum = [0, 0, 0]

        ## Connect Button to ModuleTester function

        self.loadSFR_check.stateChanged.connect(self.load_SFR)
        self.convertDAC_check.stateChanged.connect(self.DAC_check)
        self.tilt_correction_check.stateChanged.connect(self.tilt_correction)
        self.SFR_plot_btn.clicked.connect(self.on_plot_SFR)
        self.TF_plot_btn.clicked.connect(self.on_plot_TF)
        self.fp_plot_btn.clicked.connect(self.on_plot_FP)
        self.report_plot_btn.clicked.connect(self.on_report_plot)
        self.module_update_btn.clicked.connect(self.on_update_module_db)

        self.loadshading_check.stateChanged.connect(self.load_shading)
        self.shading_plot_btn.clicked.connect(self.on_shading_plot)

        self.multi_file_load_btn.clicked.connect(self.on_multi_file_load)
        self.multi_file_save_btn.clicked.connect(self.on_multi_file_save)
        self.multi_file_update_btn.clicked.connect(self.on_multi_file_update)
        self.include_graph_check.stateChanged.connect(self.multi_graph_check)

    def on_multi_file_update(self):
        try:
            if self.SFR_multi_result is not None :
                
                self.update_db.update_multi_sfr(self.SFR_multi_result)
                self.event_info('SFR from multi file are updated')
            else :
                self.event_error('SFR data is not defined')
        except Exception as e:
            
            self.event_error(e)

    def on_multi_file_save(self):
        # try:
            if self.SFR_multi_result is not None :
                if self.graph_check == True:
                    
                    self.event_info('Check Pixel Size & Sensitivity first!')
                    self.module_multi.save_multi_sfr_including_graph(self.filepaths,self.pixel_size,self.sensitivity,self.peak_min_guide)

                else:
                    self.module_multi.save_multi_sfr(self.SFR_multi_result)
                    self.event_info('SFR from multi file are saved')
            else:
                self.event_error('SFR data is not defined')
        # except Exception as e:
        #     self.event_error(e)

    def on_multi_file_load(self):
        try:
            self.filepaths=None
            self.SFR_multi_result = None
            self.filepaths = self.module_multi.load_files()
            self.SFR_multi_result = self.module_multi.get_multi_sfr(self.filepaths, self.peak_min_guide)
            self.event_info('SFR from multi file are defined')
        except Exception as e:
            self.event_error(e)

    def dummy(self):
        pass

    def on_shading_plot(self):
        try:
            self.shading_analyzer.shading_plotter(self.shading_result_dfs)
            self.shading_analyzer.show()
        except Exception as e:
            self.event_error(e)
    
    def load_shading(self,state):
        
        if state == Qt.Checked:

            try:          
                shading_df = self.shading_analyzer.open_shading()

            except:
                self.event_error('load file failed')

            if shading_df is None:
                state = Qt.Unchecked
                self.event_error('load file failed')
                
            else:
                x = self.pixel_x
                y = self.pixel_y
                pixel_size = self.pixel_size
                self.shading_result_dfs = self.shading_analyzer.get_oc(shading_df, x,y, pixel_size)
                self.event_info('Shading Result defined')
                  
                self.shading_plot_btn.setEnabled(True)

        elif state == Qt.Unchecked:

            self.shading_result_dfs = None
            self.event_info('Shading data is removed')
            self.shading_plot_btn.setEnabled(False)


    def on_update_module_db(self):
        try:
            shading_result = None 
            

            try:
                shading_result =  self.shading_result_dfs['shading_result']
            except:
                pass

            SFR_result_df = self.module_tester.SFR_preprocessing(self.SFR_dfs)
            self.update_db.update(SFR_result_df, shading_result, self.freq)
        except Exception as e:
            self.event_error(e)


    def on_report_plot(self):
        try:
            if self.SFR_checksum == [1,1,1]:
                self.module_plotter.check_param(self.freq, self.sensitivity)      
                self.module_plotter.make_report(self.SFR_dfs, self.AA_SFR_dfs)
                self.module_plotter.show()
            else:
                self.event_error('Check all the buttons before make report')
        except Exception as e:
            self.event_error(e)


    
    def on_plot_FP(self):

        try:
        
            self.module_plotter.check_param(self.freq, self.sensitivity)        
            if self.SFR_checksum == [1,1,1]:
                self.module_plotter.focus_plane_plotter(self.AA_SFR_dfs, self.AA_SFR_dfs['corrected_fp'][0])                
                self.module_plotter.show()
                self.event_info('Focus Plane Tilt correction')
            else:
                
                self.module_plotter.focus_plane_plotter(self.SFR_dfs,self.SFR_dfs['focus_plane'][0])
                self.module_plotter.show()
                self.event_info('Focus Plane Before Tilt correction')
      
        except Exception as e:
           self.event_error(e)

    def on_plot_TF(self):

        try:
            self.module_plotter.check_param(self.freq, self.sensitivity)        
            
            if self.SFR_checksum == [1,1,1]:
                self.module_plotter.TF_plotter(self.AA_SFR_dfs)
                self.module_plotter.show()
                self.event_info('Through Focus After Tilt correction')
            else:
                self.module_plotter.TF_plotter(self.SFR_dfs)
                self.module_plotter.show()
                self.event_info('Through Focus Before Tilt correction')
        except Exception as e:
            self.event_error(e)


    def on_plot_SFR(self):
        try:
            
            self.module_plotter.check_param(self.freq, self.sensitivity)    
            
            if self.SFR_checksum == [1,1,1]:
                self.module_plotter.result_plotter(self.AA_SFR_dfs)
                self.module_plotter.show()
                self.event_info('Plotting SFR Result After Tilt correction')
            else:
                self.module_plotter.result_plotter(self.SFR_dfs)
                self.module_plotter.show()
                self.event_info('Plotting SFR Result Before Tilt correction')
        except Exception as e:
            self.event_error(e)



    def tilt_correction(self, state):
        try:
            if state == Qt.Checked:                    
                if self.SFR_checksum[1] == 1:
                    
                    self.AA_SFR_dfs = self.module_tester.aa_run(self.SFR_dfs,self.pixel_size,self.sensitivity)
                    self.event_info('Tilt Correction Finished')
                    self.SFR_checksum[2] = 1 ## Update Checksum

                else :
                    self.event_error('Tilt Correction can be done after converting DAC to mm')
                    self.SFR_checksum[2] = 0 ## Update Checksum
            else:
                self.SFR_checksum[2] = 0 ## Update Checksum
                self.AA_SFR_dfs = None
        except Exception as e:
            self.event_error(e)

    def multi_graph_check(self,state):

        if state==Qt.Checked:
            self.graph_check = True
        else:
            self.graph_check = False

    def DAC_check(self,state):

        
        if state == Qt.Checked:                    
            self.SFR_checksum[1] = 1 ## Checksum 기능을 넣었는데.. 머리아프다..            
            self.event_info("Calculate Focus plane after converting units to mm")
        else:
            self.SFR_checksum[1] = 0
            self.sensitivity = 1
            self.pixel_size = 1000
            self.event_info("Calculate Focus plane with DAC & pixel")
            self.event_info("Set pixel size 1000, sensitivity 1")

    
    def on_value_changed(self, text):
        sender = self.sender()
        varname = sender.property("varname")

        if not text or text.strip() == "":
            return
        
        if varname is None:
            self.event_error("Invalid input: %s" % e)
            return
        try:
            value = float(text)
            setattr(self, varname, value)
            # self.event_info('set '+str(varname) + ' to ' + str(value))

        except Exception as e:
            self.event_error("Invalid input: %s" % e)
            return
        

    def load_SFR(self,state):
        try:
            if state == Qt.Checked:
                self.SFR_dfs, self.freq = self.module_tester.get_sfr_from_file()
                self.SFR_dfs = self.module_tester.get_focus_plane(self.SFR_dfs, self.sensitivity, self.pixel_size)
                
                self.event_info("SFR DataFrame has been defined")
                for bt in self.sfr_checkboxes:
                    bt.setEnabled(True)
                self.SFR_checksum[0] = 1
            else:
                SFR_dfs = None
                self.SFR_checksum[0] = 0
                for bt in self.sfr_checkboxes:
                    bt.setEnabled(False)
                self.event_error("Select SFR File")

        except Exception as e:
            for bt in self.sfr_checkboxes:
                    bt.setEnabled(False)
            self.event_error(e)

    def log_event(self, msg):
        self.text_event.append(msg)
    
    def event_info(self, message):
        self.logger.log_info(message)

    def event_error(self, message):
        self.logger.log_error(message)

if __name__ == "__main__":
    
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
























