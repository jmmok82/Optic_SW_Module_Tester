import time
from datetime import datetime

import numpy as np
import xlwings as xw

from Common.connect_EDM import EdgeDriver
from Module.Module_Analyzer import ModuleAnalyzer


class UpdateModuleDB:
    def __init__(self, logger):

        self.logger = logger
        self.app = None
        self.wb1 = None
        self.edge_run_once = False
        self.module_analyzer = ModuleAnalyzer(logger=self.logger)

    def _check_xls_open(self):  # 엑셀이 열렸는지 확인하는 함수, 안열려 있으면 Edge_driver Run 해서 EDM 실행

        try:
            self.app = xw.apps.active
            self.wb1 = [book for book in self.app.books if book.name.startswith("OpticLab")][0]
            self.run_once = False
            return True
        except Exception:
            if not self.edge_run_once:
                self.edge_driver = EdgeDriver()
                self.edge_driver.run()
                self.edge_run_once = True  # 한 번 실행했음을 기록
            return False

    def wait_for_edm_file(self, timeout=30):  # EDM 이 안열려 있으면 열고 기다리는 함수 열려 있으면 True 반환

        self.logger.log_info("Start checking EDM open or not")
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._check_xls_open():
                try:
                    self.logger.log_info("EDM file loaded")
                    return True
                except Exception as e:
                    self.logger.log_info(f"Error Checking OpticLabDB file : {e}")
                    self.wb1 = None
            time.sleep(1)
        return False

    def update_edm(self, SFR_dict, shading_dfs, pixel_x, pixel_y, pixel_size):

        sort = "Module"
        if SFR_dict or shading_dfs:
            if self.wait_for_edm_file():
                self.sheet = self.wb1.sheets["Module"]
                self.sheet.select()
                if SFR_dict:
                    for file in SFR_dict:
                        for idx in SFR_dict[file]:
                            freq = SFR_dict[file][idx]["freq"]
                            date = SFR_dict[file][idx]["date"]
                            title = file + "_" + str(idx)

                            row_idx = 3
                            while self.sheet.cells(row_idx, 1).value is not None:
                                row_idx += 1
                            self.sheet.cells(row_idx, 1).value = sort
                            self.sheet.cells(row_idx, 2).value = title
                            self.sheet.cells(row_idx, 3).value = date
                            self.sheet.cells(row_idx, 4).value = freq

                            SFR_result = self.module_analyzer.get_SFR_result(SFR_dict[file][idx])

                            for sfr_idx, value in enumerate(SFR_result["SFR"]):
                                self.sheet.cells(row_idx, 11 + sfr_idx).value = round(float(value), 1)
                if shading_dfs:
                    for file in shading_dfs:
                        row_idx = 3
                        title = file
                        date = datetime.today().strftime("%Y-%m-%d")
                        while self.sheet.cells(row_idx, 1).value is not None:
                            row_idx += 1
                        self.sheet.cells(row_idx, 1).value = sort
                        self.sheet.cells(row_idx, 2).value = title
                        self.sheet.cells(row_idx, 3).value = date
                        self.sheet.cells(row_idx, 4).value = "-"
                        shading_result = self.module_analyzer.get_oc(
                            shading_dfs[file], file, pixel_x, pixel_y, pixel_size
                        )
                        oc_df = np.round(shading_result["shading_result"], 3)
                        self.sheet.range((row_idx, 5)).value = oc_df.values.tolist()

            # self.wb1.save()


if __name__ == "__main__":

    class CustomLogger:
        def log_info(self, msg):
            print(f"[INFO] {msg}")

        def log_error(self, msg):
            print(f"[ERROR] {msg}")

    logger = CustomLogger()
    updatedb = UpdateModuleDB(logger)
    # updatedb.update_multi_sfr(SFR_result)
