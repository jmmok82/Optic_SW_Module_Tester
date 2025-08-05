import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

# 이 파일에서 SFR_dfs, SFR_dfs_mm, AA_SFR_dfs, Shading_dfs 를 Return 함
# SFR_dfs : 각각의 SFR 결과를 저장한 DataFrame
# SFR_dfs_mm : 각각의 SFR 결과를 저장한 DataFrame (mm 단위)
# AA_SFR_dfs : AA 이후 SFR 결과를 저장한 DataFrame
# Shading_dfs : Shading 결과를 저장한 DataFrame
# get_oc -> Shading_dfs 를 받아서 RI, Vignetting 을 계산하는 함수
# get_SFR_result : SFR 관련 데이터 프레임을 넣으면 Center Best 의 Result 를 Return 함
# 최종적으로 Analyzer 에서는 SFR_DF 와 AA_SFR_Df 만 남도록 하는것이 목표

# 250718 중복되는 과정 및 불필요한 피팅 과정 없애고 바로 translation 시키는 방향으로 퀵하게 수정(목진명)


class ModuleAnalyzer:
    def __init__(self, logger):

        self.logger = logger

    def get_oc(self, shading_df, file, x=4072, y=3096, pixel_size=1):

        shading_df.columns = list(range(len(shading_df.columns)))
        shading_df.index = list(range(len(shading_df.index)))

        log_x = len(shading_df.columns)
        log_y = len(shading_df.index)

        scale_x = int(x) / log_x
        scale_y = int(y) / log_y

        # Get Max Value & Position
        max_value = shading_df.values.flatten()
        max_value = pd.Series(max_value).quantile(0.999)
        locations = np.where(shading_df.values > max_value)

        # Get x,y axis
        rows, columns = locations
        oc_x, oc_y = (-log_x / 2 + columns.mean()), (log_y / 2 - rows.mean())
        oc_x_um = round(oc_x * scale_x * pixel_size, 1)
        oc_y_um = round(oc_y * scale_y * pixel_size, 1)

        # Get RI

        vig_size = 0.02  # Vignetting ROI 크기
        vig_x = int(log_x * vig_size)
        vig_y = int(log_y * vig_size)

        vig_lu = float(round(np.mean(shading_df.iloc[0:vig_y, 0:vig_x]), 4)) / max_value
        vig_ru = float(round(np.mean(shading_df.iloc[0:vig_y, -vig_x:]), 4)) / max_value
        vig_ld = float(round(np.mean(shading_df.iloc[-vig_y:, 0:vig_x]), 4)) / max_value
        vig_rd = float(round(np.mean(shading_df.iloc[-vig_y:, -vig_x:]), 4)) / max_value

        shading_list = [oc_x_um, oc_y_um, vig_lu, vig_ru, vig_ld, vig_rd]
        shading_column = ["OC_X(um)", "OC_Y(um)", "Vig_LU(%)", "Vig_RU(%)", "Vig_LD(%)", "Vig_RD(%)"]

        oc_df = pd.DataFrame(shading_list).T
        oc_df.columns = shading_column
        oc_df.index = pd.Index([str(file)] * len(oc_df))
        shading_result_dfs = {
            "shading": shading_df,
            "shading_result": oc_df,
            "shading_plot": [columns, rows, log_x, log_y],
        }

        return shading_result_dfs

    def fitting_plane(self, SFR_dfs_mm, aa_process=False):
        if not aa_process:
            # SFR_df = SFR_dfs_mm["SFR"]
            # # dac 최대/최소 -> SFR max가 dac_max / min일 경우는 fitting에서 제외할 예정
            # dac_max = SFR_df.index.astype(float).max() * sensitivity
            # dac_min = SFR_df.index.astype(float).min() * sensitivity

            x = np.array(SFR_dfs_mm["x"])
            y = np.array(SFR_dfs_mm["y"])
            z = SFR_dfs_mm["z"]

            A = np.c_[x, y, np.ones(x.shape)]
            coeffs, _, _, _ = np.linalg.lstsq(A, z, rcond=None)
            a, b, c = coeffs

            x_range = np.linspace(x.min(), x.max(), 10)
            y_range = np.linspace(y.min(), y.max(), 10)
            X, Y = np.meshgrid(x_range, y_range)
            Z = a * X + b * Y + c

            norm_vec = np.array([a, b, -1])
            ref_vec = np.array([0, 0, -1])

            # gradient_magnitude = np.sqrt(a**2 + b**2)
            # angle = np.arctan(gradient_magnitude) * 180 / np.pi

            # return X, Y, Z, angle

            polar_angle = (
                np.arccos(np.dot(norm_vec, ref_vec) / (np.linalg.norm(norm_vec) * np.linalg.norm(ref_vec)))
                * 180
                / np.pi
            )

            # 방위각 계산
            phi_degrees = np.degrees(np.arctan2(-b, -a))
        else:
            x = SFR_dfs_mm["x"]
            y = SFR_dfs_mm["y"]
            z = SFR_dfs_mm["z"]

            x_range = np.linspace(x.min(), x.max(), 10)
            y_range = np.linspace(y.min(), y.max(), 10)
            X, Y = np.meshgrid(x_range, y_range)
            Z = np.zeros(X.shape)

            polar_angle, phi_degrees, a, b, c = 0, 0, 0, 0, 0

        return X, Y, Z, polar_angle, phi_degrees, (a, b, c)

    def get_SFR_result(self, SFR_dfs, aa_process=False):

        SFR_df = SFR_dfs["SFR"]
        x_df = SFR_dfs["x"]
        y_df = SFR_dfs["y"]
        Center_ROI = [0, 1, 2, 3]  # Center ROI 가 바뀔 경우 대비..
        max_SFR_index = SFR_df.iloc[:, Center_ROI].astype(float).mean(axis=1)
        center_best_dac = max_SFR_index.idxmax()
        max_index = max_SFR_index.argmax()
        SFR_result = np.array(SFR_df.loc[center_best_dac])

        if not aa_process:
            if max_index > len(x_df) - 1:
                max_index = int(len(x_df) / 2)
            x_result = np.array(x_df.iloc[max_index])
            y_result = np.array(y_df.iloc[max_index])
        else:
            x_result = x_df
            y_result = y_df

        SFR_result_df = {"SFR": SFR_result, "x": x_result, "y": y_result}

        return SFR_result_df

    def convert_DAC_to_mm(self, SFR_dfs, pixel_size, sensitivity):

        if pixel_size and sensitivity is not None:
            SFR_df = SFR_dfs["SFR"]
            x_df = SFR_dfs["x"]
            y_df = SFR_dfs["y"]

            # DAC to mm

            max_dac_roi = [
                SFR_df.iloc[:, i].astype(float).idxmax() for i in range(len(SFR_df.columns))
            ]  # 각 ROI의 SFR 값이 최대가 되는 인덱스(DAC) 값
            max_dac_roi = [int(value.replace(".000", "")) for value in max_dac_roi]
            Center_ROI = [0, 1, 2, 3]  # 하드코딩함 (1,2,3,4 는 무조건 센터!)
            max_SFR_index = SFR_df.iloc[:, Center_ROI].astype(float).mean(axis=1)
            center_best_dac = float(max_SFR_index.idxmax().strip())  # 중심 ROI의 SRF이 최대가 되는 DAC값

            # focus_plane = (np.array([max_dac_roi]) - center_best_dac) * sensitivity

            x_mm = x_df * pixel_size / 1000
            x_mm.index = x_mm.index.astype(float)
            x_mm = x_mm.loc[float(center_best_dac)]
            x_dac_center = np.mean(x_mm.iloc[0:4])
            x_mm = x_mm - x_dac_center

            y_mm = y_df * pixel_size / 1000
            y_mm.index = y_mm.index.astype(float)
            y_mm = y_mm.loc[float(center_best_dac)]
            y_dac_center = np.mean(y_mm.iloc[0:4])
            y_mm = y_mm - y_dac_center

            z_mm = (np.array(max_dac_roi) - center_best_dac) * sensitivity
            z_mm = z_mm - np.mean(z_mm[0:4])

            # _, _, _, angle = self.fitting_plane(x_mm,y_mm,z_mm)

            SFR_dfs_mm = {"SFR": SFR_df, "x": x_mm, "y": y_mm, "z": z_mm}

            return SFR_dfs_mm, max_dac_roi, center_best_dac, x_dac_center, y_dac_center

        else:
            self.logger.log_error("Pixel_size, sensitivity is None. Please input the value.")
            return {"SFR": [], "x": np.nan, "y": np.nan, "z": np.nan}, np.nan, np.nan, np.nan, np.nan

    def tilt_correction(self, SFR_dfs, pixel_size, sensitivity):

        SFR_dfs_mm, _, center_best_dac, _, _ = self.convert_DAC_to_mm(SFR_dfs, pixel_size, sensitivity)
        _, _, _, _, _, (a, b, c) = self.fitting_plane(SFR_dfs_mm)

        SFR_df = SFR_dfs["SFR"]  # 각 ROI의 DAC 값 별 Through Focus MTF

        # focus plane 에서 각 ROI의 x, y 값 (mm) -> convert_DAC_to_mm 과정에서 center best로 이미 이동된 량
        fp_x = SFR_dfs_mm["x"]
        fp_y = SFR_dfs_mm["y"]
        fp_z = SFR_dfs_mm["z"]

        # focus plane으로 보낸 후의 z 값(mm, tilt correction 전)?
        # focus_plane = (np.array([max_dac_roi]) - center_best_dac) * sensitivity

        # 각 roi의 z 값과 tilt 된 평면 사이의 거리 차이 -> 이만큼을 이동시키나?
        focus_gap = a * fp_x + b * fp_y + c

        z_shifted_arr = []
        SRFs_shifted_arr = []
        fp_z_shifted = []
        for i in range(len(fp_x)):
            z_shifted_arr.append((SFR_df.index.astype(float) - center_best_dac) * sensitivity - focus_gap.iloc[i])
            SRFs_shifted_arr.append(SFR_df.iloc[:, i].values)
            fp_z_shifted.append(fp_z[i] - focus_gap.iloc[i])
        z_shifted_arr = np.array(z_shifted_arr)

        AA_SFR_df_x = np.array((SFR_df.index.astype(float) - center_best_dac) * sensitivity)

        interpolated_y_values = []
        for x, y in zip(z_shifted_arr, SRFs_shifted_arr):
            # f = interp1d(x, y, kind="linear", fill_value=(np.nan, np.nan), bounds_error=False)
            f = interp1d(x, y, kind="linear", fill_value=np.nan, bounds_error=False)  # 잘 작동하면 윗 줄 삭제할 예정
            interpolated_y = f(AA_SFR_df_x)
            interpolated_y_values.append(interpolated_y)

        AA_SFR_df = pd.DataFrame(interpolated_y_values).T
        AA_SFR_df.index = pd.Index(AA_SFR_df_x)
        AA_SFR_df.columns = SFR_df.columns

        AA_SFR_dfs = {"SFR": AA_SFR_df, "x": fp_x, "y": fp_y, "z": fp_z_shifted}

        return AA_SFR_dfs

    def run_analyzer(self, SFR_dfs, pixel_size, sensitivity, tilt_correction=True):

        SFR_result = self.get_SFR_result(SFR_dfs)
        SFR_dfs_mm, _, _, _, _ = self.convert_DAC_to_mm(SFR_dfs, pixel_size, sensitivity)
        angle_org = self.fitting_plane(SFR_dfs_mm)
        SFR_data = {"SFR_df": SFR_dfs, "SFR_result": SFR_result, "angle": angle_org, "SFR_df_mm": SFR_dfs_mm}

        if tilt_correction:
            try:
                AA_SFR_dfs = self.tilt_correction(SFR_dfs, pixel_size, sensitivity)
                AA_SFR_result = self.get_SFR_result(AA_SFR_dfs, True)
                angle_aa = self.fitting_plane(AA_SFR_dfs, True)
                AA_SFR_data = {"SFR_df": AA_SFR_dfs, "SFR_result": AA_SFR_result, "angle": angle_aa}
            except Exception:
                AA_SFR_data = None
            # self.logger.log_error("Tilt Correction Failed!!...{}".format(file))
        # AA_SFR_data = None
        else:
            AA_SFR_data = None

        return SFR_data, AA_SFR_data
