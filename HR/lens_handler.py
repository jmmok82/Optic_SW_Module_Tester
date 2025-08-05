from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator

from HR.lens_reader import LensData, LensReader
from HR.lens_script import ScriptGenerator
from HR.lens_updateDB import UpdateLensDB
from HR.lens_writer import LensWriter

# import hr_class


class HRWidget:
    def __init__(self, main_window, logger):

        self.main = main_window
        self.logger = logger
        self.lensreader = LensReader()
        self.lensdata = LensData()
        self.lenswriter = LensWriter()
        self.update_db = UpdateLensDB(self.logger)

        # Pre-define main variable
        self.raw = None
        self.raw_index = None
        self.all_data = None
        self.fno = None
        self.IH = None
        self.operator = None
        self.sensor = None
        self.script_freq = None
        self.posfile = False
        self.isposfile = False
        self.posfile_text = "posfile.fld"

        self.main.lens_analyze_btn.setEnabled(False)

        self.main.Fno_line.setValidator(QDoubleValidator(0, 100.00, 2, self.main))
        self.fno = float(self.main.Fno_line.text())
        self.main.Fno_line.setProperty("varname", "fno")
        self.main.Fno_line.textChanged.connect(lambda text: self.main.on_value_changed(text, handler=self))

        # Script Generator Vaiable

        self.main.script_ih_line.setValidator(QDoubleValidator(0, 100.00, 2, self.main))
        self.IH = float(self.main.script_ih_line.text())
        self.main.script_ih_line.setProperty("varname", "IH")
        self.main.script_ih_line.textChanged.connect(lambda text: self.main.on_value_changed(text, handler=self))

        # self.main.script_operator_line.setValidator(QDoubleValidator(0, 100.00, 2, self.main))
        self.operator = str(self.main.script_operator_line.text())
        self.main.script_operator_line.setProperty("varname", "operator")
        self.main.script_operator_line.textChanged.connect(lambda text: self.main.on_value_changed(text, handler=self))

        self.sensor = str(self.main.script_sensor_line.text())
        self.main.script_sensor_line.setProperty("varname", "sensor")
        self.main.script_sensor_line.textChanged.connect(lambda text: self.main.on_value_changed(text, handler=self))

        self.main.script_freq_line.setValidator(QIntValidator(0, 1000, self.main))
        self.script_freq = int(self.main.script_freq_line.text())
        self.main.script_freq_line.setProperty("varname", "script_freq")
        self.main.script_freq_line.textChanged.connect(lambda text: self.main.on_value_changed(text, handler=self))

        self.posfile_text = str(self.main.posfile_line.text())
        self.main.posfile_line.setProperty("varname", "posfile_text")
        self.main.posfile_line.textChanged.connect(lambda text: self.main.on_value_changed(text, handler=self))

        # Connect HR Button
        self.main.lens_load_btn.clicked.connect(self.on_load_lens)
        self.main.lens_analyze_btn.clicked.connect(self.on_lens_analyze)
        self.main.lens_save_report_btn.clicked.connect(self.on_lens_save_report)
        self.main.script_make_btn.clicked.connect(self.on_make_script)
        self.main.lens_update_db_btn.clicked.connect(self.on_lens_update)

        self.main.posfile_check.stateChanged.connect(self.on_posfile_check)

    def on_posfile_check(self, state):

        if state == Qt.Checked:
            self.main.posfile_line.setEnabled(True)
            self.logger.log_info("Make Script using postiion file")
            self.logger.log_info("Save position file at -d:/ before start script")
            self.isposfile = True
        else:
            self.main.posfile_line.setEnabled(False)
            self.logger.log_info("Make script without using position file")
            self.isposfile = False

    def on_lens_update(self):

        self.update_db.update(self.all_data, self.fno)

    def on_value_changed(self, text):
        sender = self.sender()
        varname = sender.property("varname")
        if varname is None:
            self.logger.log_error("Invalid input: varname is None")
            return
        try:
            value = float(text)
            setattr(self, varname, value)
            # self.event_info('set '+str(varname) + ' to ' + str(value))

        except Exception as e:
            self.logger.log_error("Invalid input: %s" % e)
            return

    def on_make_script(self):

        if self.isposfile:
            self.posfile = self.posfile_text
            self.logger.log_info(f"Make script using postiion file {self.posfile}")
        else:
            self.posfile = False

        checkboxes = {
            "mtf": self.main.script_MTF_check,
            "tf": self.main.script_TF_check,
            "cra": self.main.script_CRA_check,
            "ri": self.main.script_RI_check,
            "dist": self.main.script_dist_check,
            "lateral": self.main.script_lateral_check,
            "lsa": self.main.script_LSA_check,
            "efl": self.main.script_EFL_check,
        }

        checksum_vars = {key: 1 if cb.isChecked() else 0 for key, cb in checkboxes.items()}
        script_generator = ScriptGenerator(checksum_vars)
        script_generator.save_script(self.IH, self.operator, self.sensor, self.script_freq, self.posfile)
        self.logger.log_info("Script Saved")

    def on_lens_save_report(self):
        # try:
        if self.all_data is not None:

            self.lenswriter.run(self.all_data, self.fno)
            self.logger.log_info("Lens Report Saved")

    # except AttributeError:
    #     self.logger.log_error('Lens Data is not ready')

    def on_lens_analyze(self):
        try:
            if self.raw and self.raw_index is not None:
                self.all_data = self.lensdata.get_all(self.raw, self.raw_index)

                checkboxes = {
                    "mtf": self.main.lens_MTF_check,
                    "tf": self.main.lens_TF_check,
                    "cra": self.main.lens_CRA_check,
                    "ri": self.main.lens_RI_check,
                    "dist": self.main.lens_dist_check,
                    "lateral": self.main.lens_lateral_check,
                    "lsa": self.main.lens_LSA_check,
                    "efl": self.main.lens_EFL_check,
                }
                for key, value in self.all_data.items():
                    if key in checkboxes and value is not None:
                        checkboxes[key].setChecked(True)
                        self.logger.log_info(str(key) + " measurement found")
                    elif key not in checkboxes:
                        continue
                    else:
                        checkboxes[key].setChecked(False)
                        self.logger.log_error(str(key) + " measurement not found")
        except Exception as e:
            self.logger.log_error(e)

    def on_load_lens(self):
        try:
            self.raw, self.raw_index = self.lensreader.read_file()  # PYQT 로 바꿔야함 현재 TKinter

            if self.raw and self.raw_index is not None:
                self.main.lens_analyze_btn.setEnabled(True)
                self.logger.log_info("Lens data loaded")
            else:
                self.main.lens_analyze_btn.setEnabled(False)
        except Exception as e:
            self.main.lens_analyze_btn.setEnabled(False)
            self.logger.log_error(e)


# if __name__ == "__main__":
# app = QApplication(sys.argv)
# widget = HRWidget()
# widget.resize(800, 600)  # Set the window size
# widget.show()
# sys.exit(app.exec_())
