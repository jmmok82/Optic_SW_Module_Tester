import os
import tempfile

import pandas as pd
import xlwings as xw
from PyQt5.QtWidgets import QDialog, QFileDialog, QWidget

from Module.Module_Analyzer import ModuleAnalyzer
from Module.Module_Plotter import ModulePlotter


class SecondWindow(QDialog):
    def __init__(self):
        super().__init__()

    def save_file(self, default_path):

        file_path, _ = QFileDialog.getSaveFileName(
            None, "Save Report", f"{default_path}/module_tester_result.xlsx", "Excel Files (*.xlsx);;All Files (*)"
        )
        if file_path:
            if not file_path.endswith(".xlsx"):
                file_path += ".xlsx"

        return file_path


class ModuleWriter(QWidget):
    def __init__(self, logger):

        self.logger = logger
        self.module_analyzer = ModuleAnalyzer(logger=self.logger)
        self.module_plotter = ModulePlotter()
        self.second_window = SecondWindow()

    def check_param(self, pixel_size, sensitivity, pixel_x, pixel_y):

        self.pixel_size = pixel_size
        self.sensitivity = sensitivity
        self.pixel_x = pixel_x
        self.pixel_y = pixel_y

    def _build_SFR_dataframe(self, SFR_dict):

        SFR_results = []

        # 측정 데이터의 ROI 가 변경되지 않았음을 가정함

        for file in SFR_dict:
            for idx in SFR_dict[file]:
                freq = SFR_dict[file][idx]["freq"]
                SFR_result = self.module_analyzer.get_SFR_result(SFR_dict[file][idx])
                try:
                    SFR_dfs_mm, _, _, _, _ = self.module_analyzer.convert_DAC_to_mm(
                        SFR_dict[file][idx], self.pixel_size, self.sensitivity
                    )
                    _, _, _, angle, phi_angle, _ = self.module_analyzer.fitting_plane(SFR_dfs_mm)
                    angle = round(angle, 2)
                    phi_angle = round(phi_angle, 2)
                except Exception:
                    angle, phi_angle = "Nan", "Nan"

                SFR_results.append(
                    {
                        "file": file,
                        "idx": idx,
                        "freq": freq,
                        "angle": angle,
                        "phi_angle": phi_angle,
                        "SFR": SFR_result["SFR"],
                    }
                )

        # Data processing to DataFrame

        SFR_df = pd.DataFrame(SFR_results)
        SFR_expanded = pd.DataFrame(SFR_df["SFR"].tolist())
        SFR_expanded.columns = SFR_dict[file][idx]["SFR"].columns
        SFR_final = pd.concat([SFR_df.drop(columns=["SFR"]), SFR_expanded], axis=1)

        return SFR_final

    def save_result(self, load_filename, SFR_dict, shading_dfs, graph=False):

        app = xw.App(visible=False)
        wb = app.books.add()

        if shading_dfs is not None:
            self._insert_shading_data(wb, shading_dfs)

        if graph:
            self._insert_graph(wb, SFR_dict)

        sht = wb.sheets.add("Result")
        SFR_df = self._build_SFR_dataframe(SFR_dict)
        sht.range("A1").value = [SFR_df.columns.tolist()] + SFR_df.values.tolist()
        file_path = self.second_window.save_file(os.path.split(load_filename)[0])

        wb.save(file_path)
        wb.close()

        return file_path

    def _insert_shading_data(self, wb, shading_dfs):

        shading_idx = 0
        for file in shading_dfs:
            shading_idx += 1
            sht = wb.sheets.add("Shading " + str(shading_idx))
            shading_result = self.module_analyzer.get_oc(
                shading_dfs[file], file, self.pixel_x, self.pixel_y, self.pixel_size
            )
            sht.range("A1").value = shading_result["shading_result"]

            canvas = self.module_plotter.shading_plotter(shading_result, False)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                # canvas에서 figure 추출 후 저장
                canvas.figure.savefig(tmpfile, format="png")
                tmpfile_path = tmpfile.name
            sht.pictures.add(
                tmpfile_path, name="Shading", update=True, left=sht.range("A4").left, top=sht.range("A3").top, scale=1
            )

    def _insert_graph(self, wb, SFR_dict):
        sht_idx = 0

        for file in SFR_dict.keys():
            measure_idx = 0

            for idx in SFR_dict[file]:
                sht_idx += 1
                measure_idx += 1
                filename = os.path.splitext(os.path.basename(file))[0]
                freq = SFR_dict[file][idx]["freq"]
                self.module_plotter.check_param(freq, self.sensitivity)
                sht = wb.sheets.add("#" + str(sht_idx))
                sht.range("A1").value = str(filename)
                sht.range("A2").value = "#" + str(measure_idx)

                SFR_data, AA_SFR_data = self.module_analyzer.run_analyzer(
                    SFR_dict[file][idx], self.pixel_size, self.sensitivity
                )
                if AA_SFR_data is None:  # Tilt Correction 실패 시 TF, 와 FocusPlane 만 그리기
                    self.logger.log_error(f"Tilt Correction Failed!!...{file} _ {idx}")
                    canvas_tf = self.module_plotter.TF_plotter(SFR_data["SFR_df"], None, False)
                    canvas_fp = self.module_plotter.focus_plane_plotter(
                        SFR_data["SFR_df_mm"], SFR_data["angle"], None, False
                    )

                    canvas_list = [canvas_tf, canvas_fp]

                    for i, canvas_value in enumerate(canvas_list):

                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                            canvas_value.figure.savefig(tmpfile, format="png")
                            tmpfile_path = tmpfile.name
                        if i == 0:
                            sht.pictures.add(
                                tmpfile_path,
                                name=f"MyPlot{i+1}",
                                update=True,
                                left=sht.range("A3").left,
                                top=sht.range("A3").top,
                            )
                        else:
                            sht.pictures.add(
                                tmpfile_path,
                                name=f"MyPlot{i+1}",
                                update=True,
                                left=sht.range("J3").left,
                                top=sht.range("J3").top,
                            )
                else:
                    canvas_report = self.module_plotter.make_report(
                        SFR_data, AA_SFR_data, False
                    )  # False 일 시 그래프를 안그리고 canvas 를 반환
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                        # canvas에서 figure 추출 후 저장
                        canvas_report.figure.savefig(tmpfile, format="png")
                        tmpfile_path = tmpfile.name

                    sht.pictures.add(
                        tmpfile_path,
                        name="Report",
                        update=True,
                        left=sht.range("A3").left,
                        top=sht.range("A3").top,
                        scale=0.5,
                    )
