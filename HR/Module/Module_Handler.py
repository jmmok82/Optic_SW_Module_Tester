from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import QComboBox, QDialog, QPushButton, QVBoxLayout

from Module.Module_Analyzer import ModuleAnalyzer
from Module.Module_Plotter import ModulePlotter
from Module.Module_Reader import ModuleReader
from Module.Module_updateDB import UpdateModuleDB
from Module.Module_Writer import ModuleWriter


class SecondWindow(QDialog):
    def __init__(self, data_list, parent=None):
        super().__init__(parent)

        self.data_list = data_list
        self.selected_file = None
        self.selected_idx = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.combo = QComboBox()
        for file, idx in self.data_list:
            self.combo.addItem(f"{file} / {idx}", (file, idx))
        layout.addWidget(self.combo)

        btn = QPushButton("선택")
        btn.clicked.connect(self.select_item)
        layout.addWidget(btn)

        self.setLayout(layout)
        self.setWindowTitle("파일/인덱스 선택")

    def select_item(self):
        file, idx = self.combo.currentData()
        self.selected_file = file
        self.selected_idx = idx
        self.accept()  # 다이얼로그 종료, exec_()에 Accepted 반환

    def get_selection(self):
        return self.selected_file, self.selected_idx


class ModuleWidget:
    def __init__(self, main_window, logger):

        self.logger = logger
        self.updateDB = UpdateModuleDB(logger=self.logger)
        self.module_reader = ModuleReader(logger=self.logger)
        self.module_analyzer = ModuleAnalyzer(logger=self.logger)
        self.module_plotter = ModulePlotter()
        self.module_writer = ModuleWriter(logger=self.logger)
        self.main = main_window

        # Set ModuleTester User Input Variable

        self.setup_line_edit(self.main.pixel_x_line, "pixel_x", 1, 50000, 0, is_int=True)
        self.setup_line_edit(self.main.pixel_y_line, "pixel_y", 1, 50000, 0, is_int=True)
        self.setup_line_edit(self.main.pixelsize_line, "pixel_size", 0.1, 10, 2, is_int=False)
        self.setup_line_edit(self.main.sensitivity_line, "sensitivity", 0, 10, 10, is_int=False)
        self.setup_line_edit(self.main.peakmin_SFR_line, "peak_min_guide", 0, 100, 0, is_int=True)
        self.main.include_graph_check.stateChanged.connect(self.on_graph_check)

        # Define variables

        self.SFR_dict = self.shading_dfs = None
        self.sfr_file_idx_pairs = self.shading_file_idx_pairs = None
        self.file_idx_pairs = None
        self.include_graph_check = False
        self.pixel_size = 1  # Pre-defined value
        self.sensitivity = 0.000125
        self.pixel_x = 4096
        self.pixel_y = 3072
        self.peak_min_guide = 30

        # button 과 함수 연결

        self.main.module_load_file_btn.clicked.connect(self.on_module_load_btn)
        self.main.module_save_btn.clicked.connect(self.on_module_save_btn)
        self.main.SFR_plot_btn.clicked.connect(self.on_SFR_plot_btn)
        self.main.TF_plot_btn.clicked.connect(self.on_TF_plot_btn)
        self.main.FP_plot_btn.clicked.connect(self.on_FP_plot_btn)
        self.main.shading_plot_btn.clicked.connect(self.on_oc_plot_btn)
        self.main.module_update_btn.clicked.connect(self.on_update_btn)

    def on_update_btn(self):

        if self.SFR_dict or self.shading_dfs:
            self.updateDB.update_edm(self.SFR_dict, self.shading_dfs, self.pixel_x, self.pixel_y, self.pixel_size)
        else:
            self.logger.log_error("No Data to update")

    def on_oc_plot_btn(self):

        if self.shading_file_idx_pairs is not None:
            selector = SecondWindow(self.shading_file_idx_pairs)
            if selector.exec():
                file, idx = selector.get_selection()
                shading_result = self.module_analyzer.get_oc(
                    self.shading_dfs[file], file, self.pixel_x, self.pixel_y, self.pixel_size
                )
                self.module_plotter.shading_plotter(shading_result, True)
                self.module_plotter.show()

            else:
                self.logger.log_error("Canceled")
        else:
            self.logger.log_error("NO Shading Data")

    def on_FP_plot_btn(self):

        if self.sfr_file_idx_pairs is not None:
            selector = SecondWindow(self.sfr_file_idx_pairs)
            if selector.exec():
                file, idx = selector.get_selection()
                SFR_data, _ = self.module_analyzer.run_analyzer(
                    self.SFR_dict[file][idx], self.pixel_size, self.sensitivity
                )
                self.module_plotter.check_param(SFR_data["SFR_df"]["freq"], self.sensitivity)
                self.module_plotter.focus_plane_plotter(SFR_data["SFR_df_mm"], SFR_data["angle"], None, True)
                self.module_plotter.show()

            else:
                self.logger.log_error("Canceled")
        else:
            self.logger.log_error("NO SFR data")

    def on_TF_plot_btn(self):

        if self.sfr_file_idx_pairs is not None:
            selector = SecondWindow(self.sfr_file_idx_pairs)
            if selector.exec():
                file, idx = selector.get_selection()
                SFR_data, _ = self.module_analyzer.run_analyzer(
                    self.SFR_dict[file][idx], self.pixel_size, self.sensitivity
                )
                self.module_plotter.check_param(SFR_data["SFR_df"]["freq"], self.sensitivity)
                self.module_plotter.TF_plotter(SFR_data["SFR_df"], None, True)
                self.module_plotter.show()

            else:
                self.logger.log_error("Canceled")
        else:
            self.logger.log_error("NO SFR data")

    def on_SFR_plot_btn(self):

        if self.sfr_file_idx_pairs is not None:
            selector = SecondWindow(self.sfr_file_idx_pairs)
            if selector.exec():
                file, idx = selector.get_selection()
                SFR_data, _ = self.module_analyzer.run_analyzer(
                    self.SFR_dict[file][idx], self.pixel_size, self.sensitivity
                )
                self.module_plotter.check_param(SFR_data["SFR_df"]["freq"], self.sensitivity)
                self.module_plotter.result_plotter(SFR_data["SFR_result"], None, True)
                self.module_plotter.show()

            else:
                self.logger.log_error("Canceled")

    def on_graph_check(self, state):

        if state == Qt.Checked:
            self.include_graph_check = True
            self.main.event_info("Save SFR result including graph")
        else:
            self.include_graph_check = False
            self.main.event_info("Save SFR result only")

    def on_module_save_btn(self):

        self.module_writer.check_param(self.pixel_size, self.sensitivity, self.pixel_x, self.pixel_y)
        file_path = self.module_writer.save_result(
            self.filenames[0], self.SFR_dict, self.shading_dfs, self.include_graph_check
        )  # False 일 시 graph 저장 안함
        if not file_path:
            self.logger.log_error("Chooose directory")
        else:
            self.main.event_info("Result saved at {}".format(file_path))

    def on_module_load_btn(self):

        self.SFR_dict = self.shading_dfs = None
        self.sfr_file_idx_pairs = self.shading_file_idx_pairs = None

        self.filenames = self.module_reader.load_file()
        self.SFR_dict, self.shading_dfs = self.module_reader.run_reader(self.peak_min_guide)
        self.main.module_save_btn.setEnabled(True)
        self.main.module_update_btn.setEnabled(True)

        if self.SFR_dict is not None:  # 하나씩 Plot 을 하기 위한 측정 index 변수 선언
            self.sfr_file_idx_pairs = []
            for file in self.SFR_dict:
                for idx in self.SFR_dict[file]:
                    self.sfr_file_idx_pairs.append([file, idx])

        if self.shading_dfs is not None:
            self.shading_file_idx_pairs = []
            for file in self.shading_dfs:
                self.shading_file_idx_pairs.append([file, 1])

    def setup_line_edit(
        self, line_edit, varname, min_val, max_val, decimals, is_int=False  # 반복되는 Text Editer 설정을 깔끔하게
    ):
        if is_int:
            line_edit.setValidator(QIntValidator(int(min_val), int(max_val), self.main))
        else:
            line_edit.setValidator(QDoubleValidator(min_val, max_val, decimals, self.main))

        text = line_edit.text()
        try:
            value = int(text) if int else float(text)
        except ValueError:
            value = 0
        setattr(self, varname, value)
        line_edit.setProperty("varname", varname)
        line_edit.textChanged.connect(lambda text: self.main.on_value_changed(text, handler=self))
