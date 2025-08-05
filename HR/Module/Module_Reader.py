import csv
import os
import re
from datetime import datetime

import pandas as pd
from PyQt5.QtWidgets import QDialog, QFileDialog

# from Common.seoncondwindow import SecondWindow


class SecondWindow(QDialog):
    def __init__(self):
        super().__init__()

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileNames(
            None, "Select a CSV file", "", "CSV Files (*.csv);;All Files (*.*)"
        )
        return file_path


class ModuleReader:
    def __init__(self, logger):

        self.secondwindow = SecondWindow()
        self.logger = logger

    def load_file(self):

        self.file_path = self.secondwindow.load_file()
        if not self.file_path:
            self.logger.log_error("No file selected.")
        return self.file_path

    def _get_raw(self, file_path):

        filename = os.path.splitext(os.path.basename(file_path))[0]

        with open(file_path, "r") as file:
            reader = csv.reader(file)
            raw = list(reader)

        def safe(val):  # Shaing 선택시 raw[1][0] 이 에러가 나서..
            try:
                return val()
            except Exception:
                return None

        if safe(lambda: str(raw[1][0])) == "cpp":  # 데이터 유효성 검증 방법 (TF MTF 일때)

            fmt = "format_SFR"
        elif safe(lambda: str(raw[2][1])) == "Num":  # 데이터 유효성 검증 방법 (Shading 일때)

            fmt = "format_shading"
        else:
            self.logger.log_error(f"{filename} is invalid Data")
            return None, None

        return raw, fmt

    def _SFR_parse(self, raw):

        parsing_info = self._define_header_index(raw)
        data_dict = {}
        for idx, _ in enumerate(parsing_info["header_index"]):
            data_dict[idx + 1] = self._parsing_sfr_raw(raw, parsing_info, idx + 1)

        return data_dict

    def _define_header_index(self, raw):  # 한 파일안에 측정 갯수가 몇개인지 확인

        header = [i.replace(",", "").replace(" ", "").replace(" ROI 1", "ROI 1") for i in raw[1]]
        roi_num = [roi_num for roi_num in header if "ROI" in roi_num]
        roi_num = [item.replace("ROI", "") for item in roi_num]

        roi_name = []
        for name in header:
            if "ROI" in name:
                name_index = header[header.index(name) + 1]
                roi_name.append(name_index)
        final_roi_num = int(re.findall("\d+", roi_num[-1])[0])
        header_index = [i for i, x in enumerate(raw) if x == raw[1]]

        parsing_info = {"header_index": header_index, "final_roi_num": final_roi_num, "roi_name": roi_name}

        return parsing_info

    def _parsing_sfr_raw(self, raw, parsing_info, data_selected):

        header_index = parsing_info["header_index"]
        final_roi_num = parsing_info["final_roi_num"]
        roi_name = parsing_info["roi_name"]

        if len(header_index) == data_selected:
            sorted_raw = raw[header_index[data_selected - 1] : -1]
        else:
            sorted_raw = raw[header_index[data_selected - 1] : header_index[data_selected] - 2]

        # 날짜 정리
        date = str(raw[header_index[data_selected - 1] - 1])
        date = date.strip("[]'").split("_")[0]
        date = date.rstrip(".")
        date = datetime.strptime(date, "%Y.%m.%d")

        raw_array = pd.DataFrame(sorted_raw)
        freq = raw_array[0][1]

        af_step_index = int(raw_array.iloc[0].index[raw_array.iloc[0] == "AF Step"][0])
        sfr_df = pd.DataFrame()
        x_df = pd.DataFrame()
        y_df = pd.DataFrame()
        for i in range(final_roi_num):
            column_name = roi_name[i]
            sfr_df[column_name] = raw_array.iloc[2:][10 + i * 3].astype(float)
            x_df[column_name] = raw_array.iloc[2:][11 + i * 3].astype(int)
            y_df[column_name] = raw_array.iloc[2:][12 + i * 3].astype(int)
        x_df.index = y_df.index = sfr_df.index = raw_array.iloc[2:, af_step_index]
        x_df.index.name = y_df.index.name = sfr_df.index.name = "DAC"

        SFR_dfs = {"SFR": sfr_df, "x": x_df, "y": y_df, "freq": freq, "date": date}

        return SFR_dfs

    def _remove_invalid_tf(self, SFR_dict, peak_min):

        for file in SFR_dict:
            for idx in list(SFR_dict[file]):
                SFR_df = SFR_dict[file][idx]["SFR"]
                Center_ROI = [0, 1, 2, 3]  # Center ROI 가 바뀔 경우 대비..
                max_SFR_index = SFR_df.iloc[:, Center_ROI].astype(float).mean(axis=1)

                if max(max_SFR_index) < peak_min:  # Peak 찾는 알고리즘 추가 필요
                    self.logger.log_error(f"{file} {idx} data has no peak, skipped")
                    del SFR_dict[file][idx]
                else:
                    continue

        return SFR_dict

    def run_reader(self, peak_min=50):

        SFR_dict = {}
        shading_dfs = {}

        if not self.file_path:
            self.logger.log_error("No file selected.")
            SFR_dict, shading_dfs = None, None
            return SFR_dict, shading_dfs

        for file_idx, file in enumerate(self.file_path):

            filename = os.path.splitext(os.path.basename(file))[0]
            raw, fmt = self._get_raw(file)
            if fmt == "format_SFR":
                # SFR_dict = {}
                SFR_dict[filename] = self._SFR_parse(raw)
                self.logger.log_info(f"{filename} has {len(SFR_dict[filename])} sets SFR Through Focus Data")

            elif fmt == "format_shading":
                shading_df = pd.DataFrame(raw).iloc[3:, 2:-1].apply(pd.to_numeric, errors="coerce").astype(float)
                shading_dfs[filename] = shading_df
                self.logger.log_info(f"{filename} is shading data")

        if SFR_dict is not None:
            SFR_dict = self._remove_invalid_tf(SFR_dict, peak_min)

        if not shading_dfs:
            shading_dfs = None
        if not SFR_dict:
            SFR_dict = None

        return SFR_dict, shading_dfs


if __name__ == "__main__":
    logger = None

    class DummyLogger:
        def log_info(self, msg):
            print(f"[INFO] {msg}")

        def log_debug(self, msg):
            print(f"[DEBUG] {msg}")

        def log_error(self, msg):
            print(f"[ERROR] {msg}")

        def log_warning(self, msg):
            print(f"[WARNING] {msg}")

    logger = DummyLogger()

    module_reader = ModuleReader(logger)

    file_path = module_reader.load_file()
    SFR_dict, shading_dfs = module_reader.run_reader(50)
