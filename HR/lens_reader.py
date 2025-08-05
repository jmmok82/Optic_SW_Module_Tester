import re
import tkinter as tk
from tkinter import filedialog

import numpy as np
import pandas as pd

# from openpyxl.utils.dataframe import dataframe_to_rows
from sklearn.linear_model import RANSACRegressor


class LensReader:

    def __init__(self):

        self.lens_index_checks = {
            "freq": "Optimize Freq.",
            "date": "Time/Date",
            "EFL": "Measurement Table: EFL / Magnification",
            "LSA": "Measurement Table: Longitudinal Chromatic Aberration ( Tangential )",
            "Lateral": "Measurement Table: Lateral Chromatic Aberration ( Lateral Shift (=B5m) )",
            "Distortion": "Measurement Table: Rel. Distortion vs. Image Height",
            "MTF": "Measurement Table: MTF vs. Image Height",
            "TFvsField": "Measurement Table: Field Focus 2D (Tangential)",
            "RI": "Measurement Table: Relative Illumination ( Image Plane )",
            "CRA": "Measurement Table: Chief Ray Angle",
        }

    def read_file(self):
        root = tk.Tk()
        root.withdraw()
        self.filepath = filedialog.askopenfilename(title="MHT 파일 불러오기", filetypes=[("MHT 파일", "*.mht")])
        try:
            # filepath = self.select_file()
            if not self.filepath:
                return []
            with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
                mht_raw = f.read()
                raw = mht_raw.splitlines()

            checked = set()
            raw_index = []
            for j, line in enumerate(raw):
                for i, check in enumerate(self.lens_index_checks):
                    if self.lens_index_checks[check] in line and check not in checked:
                        raw_index.append([check, j])
                        checked.add(check)
            raw_index = np.array(raw_index)

        except Exception:
            raw, raw_index = None

        return raw, raw_index


class LensData:

    def __init__(self):
        pass

    def remove09(self, data):
        try:
            new_data = float(str(data).split("=")[0])
        except ValueError:
            new_data = [float(x.replace("=09", "")) for x in data if x != ""]

        return new_data

    def measure_info(self):
        date_index = int(self.raw_index[self.raw_index[:, 0] == "date"][0][1])
        date = str(self.raw[date_index]).split("  ")[-1].strip()

        freq_index = int(self.raw_index[self.raw_index[:, 0] == "freq"][0][1])
        freq = int(float((re.search(r"\d+(?:\.\d+)?", str(self.raw[freq_index])).group())))

        return date, freq

    def get_efl(self):
        try:
            efl_index = int(self.raw_index[self.raw_index[:, 0] == "EFL"][0][1])

            for i, line in enumerate(self.raw[efl_index : efl_index + 200]):
                if line == "Average:=09":
                    efl_index2 = i + 1 + int(self.raw_index[2][1])
                    break
            efl = float(str(self.raw[efl_index2]).split("=")[0])
        except Exception:
            efl = None
        return efl

    def get_lsa(self):
        try:
            LSA_wavelength = []
            LSA_focalshift = []
            LSA_index = int(self.raw_index[self.raw_index[:, 0] == "LSA"][0][1])
            for i in range(5):
                try:
                    LSA_wavelength.append(self.remove09(self.raw[LSA_index + 27 + i * 6]))
                    LSA_focalshift.append(self.remove09(self.raw[LSA_index + 27 + i * 6 + 1]))
                except ValueError:
                    break
            LSA_df = pd.DataFrame({"Wavelength": LSA_wavelength, "Focal Shift": LSA_focalshift})
        except Exception:
            LSA_df = None

        return LSA_df

    def get_lateral(self):

        try:
            Lateral_index = int(self.raw_index[self.raw_index[:, 0] == "Lateral"][0][1])
            Lateral_wavelength = self.raw[Lateral_index + 21 : Lateral_index + 26]
            Lateral_wavelength = [int(x.replace(" nm=09", "")) for x in Lateral_wavelength]

            Lateral_IH = []
            Lateral_focalshift = []

            for i in range(21):
                try:
                    Lateral_IH.append(self.remove09(self.raw[Lateral_index + 31 + i * 8]))
                    Lateral_focalshift.append(
                        self.remove09(self.raw[Lateral_index + 32 + i * 8 : Lateral_index + 32 + i * 8 + 5])
                    )
                except ValueError:
                    break
            Lateral_df = pd.DataFrame(Lateral_focalshift, index=Lateral_IH, columns=Lateral_wavelength)
        except Exception:
            Lateral_df = None

        return Lateral_df

    def get_dist(self):

        try:
            dist_IH = []
            dist = []
            dist_index = int(self.raw_index[self.raw_index[:, 0] == "Distortion"][0][1])

            for i in range(21):
                if self.raw[dist_index + 27 + i * 9] == "":
                    break
                dist_IH.append(self.remove09(self.raw[dist_index + 27 + i * 9]))
                dist.append(self.remove09(self.raw[dist_index + 29 + i * 9]))

            dist_df = pd.DataFrame(dist, index=dist_IH)
        except Exception:
            dist_df = None

        return dist_df

    def get_report_dist(self, dist):

        if dist is not None and len(dist) == 21:

            num_dist = int((len(dist) - 1) / 2)
            report_dist = []
            field = []
            for i in range(num_dist + 1):
                report_dist.append(
                    [round((dist.iloc[num_dist - i, 0] + dist.iloc[num_dist + i, 0]) / 2, 3)]
                    if i != 0
                    else [dist.iloc[num_dist, 0]]
                )
                field.append(
                    str(round((-dist.index[num_dist + i] + dist.index[num_dist - i]) / 2 / (dist.index).max(), 2))
                    + "F"
                    if i != 0
                    else "0.0F"
                )

            dist_df_report = pd.DataFrame(report_dist, index=field)

        else:
            dist_df_report = None
        return dist_df_report

    def get_mtf(self):

        mtf_IH = []
        mtfvsfield_tan = []
        mtfvsfield_sag = []

        freq_index = int(self.raw_index[self.raw_index[:, 0] == "freq"][0][1])
        freq = int(float((re.search(r"\d+(?:\.\d+)?", str(self.raw[freq_index])).group())))

        mtf_index = int(self.raw_index[self.raw_index[:, 0] == "MTF"][0][1])
        tan_index_str = "Tan " + str(freq) + "(lp/mm)=09"
        sag_index_str = "Sag " + str(freq) + "(lp/mm)=09"

        mtf_IH = self.remove09(self.raw[mtf_index + 14 : mtf_index + 35])

        for i, line in enumerate(self.raw[mtf_index : mtf_index + 40000]):
            if line == tan_index_str:
                tan_index = mtf_index + i
            elif line == sag_index_str:
                sag_index = mtf_index + i
                break

        for i in range(21):
            mtfvsfield_tan.append(self.remove09(self.raw[tan_index + 1 + i]))
            mtfvsfield_sag.append(self.remove09(self.raw[sag_index + 1 + i]))

        mtfvsfield_df = pd.DataFrame({"Tan": mtfvsfield_tan, "Sag": mtfvsfield_sag}, index=mtf_IH)

        return mtfvsfield_df

    def get_tf(self):
        try:

            tf_index = int(self.raw_index[self.raw_index[:, 0] == "TFvsField"][0][1])
            tf_IH = self.remove09(self.raw[tf_index + 37 : tf_index + 58])

            for i in range(1000):
                if self.raw[tf_index + i + 60 : tf_index + 60 + i + 5] == ["", "", "", "", ""]:
                    tf_tan_index_end = i + tf_index + 60
                    break
            tf_tan_raw = self.remove09(self.raw[tf_index + 63 : tf_tan_index_end])
            count_tf_raw = tf_tan_index_end - tf_index - 63
            tf_tan_focus = [x for x in tf_tan_raw if x > 1]
            tf_tan_value = [x for x in tf_tan_raw if x <= 1]
            tf_tan_df = pd.DataFrame(
                {
                    axis: tf_tan_value[
                        i * int(len(tf_tan_value) / len(tf_tan_focus)) : i * int(len(tf_tan_value) / len(tf_tan_focus))
                        + len(tf_tan_focus)
                    ]
                    for i, axis in enumerate(tf_tan_focus)
                }
            ).T
            tf_tan_df.columns = tf_IH

            for i in range(1000):
                if self.raw[tf_tan_index_end + i] == self.raw[tf_index + 63]:
                    tf_sag_index_start = tf_tan_index_end + i
                    break

            tf_sag_raw = self.remove09(self.raw[tf_sag_index_start : tf_sag_index_start + count_tf_raw])
            tf_sag_focus = tf_tan_focus
            tf_sag_value = [x for x in tf_sag_raw if x <= 1]
            tf_sag_df = pd.DataFrame(
                {
                    axis: tf_sag_value[
                        i * int(len(tf_sag_value) / len(tf_sag_focus)) : i * int(len(tf_sag_value) / len(tf_sag_focus))
                        + len(tf_sag_focus)
                    ]
                    for i, axis in enumerate(tf_sag_focus)
                }
            ).T
            tf_sag_df.columns = tf_IH

        except Exception:
            tf_sag_df = None
            tf_sag_df = None

        tf_dfs = {"tf_sag": tf_sag_df, "tf_tan": tf_tan_df, "tf_IH": tf_IH}

        return tf_dfs

    def get_cra(self):
        try:
            CRA_index = int(self.raw_index[self.raw_index[:, 0] == "CRA"][0][1])
            CRA_IH = []
            CRA = []
            for i in range(21):
                try:
                    CRA_IH.append(self.remove09(self.raw[CRA_index + 27 + i * 6]))
                    CRA.append(self.remove09(self.raw[CRA_index + 28 + i * 6]))
                except ValueError:
                    break

            CRA_df = pd.DataFrame(CRA, index=CRA_IH)
        except Exception:
            CRA_df = None
        return CRA_df

    def get_report_cra(self, cra):

        cra = cra - cra.abs().min()

        if len(cra) is not None and len(cra) == 21:
            num_cra = int((len(cra) - 1) / 2)
            report_cra = []
            field = []

            for i in range(num_cra + 1):
                report_cra.append(
                    [round(cra.iloc[num_cra - i, 0] - cra.iloc[num_cra + i, 0]) / 2, 1]
                    if i != 0
                    else [cra.iloc[num_cra, 0]]
                )
                field.append(
                    str(round((cra.index[num_cra + i] - cra.index[num_cra - i]) / 2 / (cra.index).max(), 2)) + "F"
                    if i != 0
                    else "0.0F"
                )

            cra_df_report = pd.DataFrame(report_cra, index=field)

        else:
            cra_df_report = None

        return cra_df_report

    def get_ri(self):
        try:
            RI_index = int(self.raw_index[self.raw_index[:, 0] == "RI"][0][1])
            RI_IH = []
            RI = []
            for i in range(21):
                try:
                    RI_IH.append(self.remove09(self.raw[RI_index + 27 + i * 6]))
                    RI.append(self.remove09(self.raw[RI_index + 28 + i * 6]))
                except ValueError:
                    break
            RI_df = pd.DataFrame(RI, index=RI_IH)
        except Exception:
            RI_df = None
        return RI_df

    def get_report_ri(self, ri):  # RI Data pre-procssing for report

        if ri is not None and len(ri) == 21:
            ri = ri / ri.max()
            num_ri = int((len(ri) - 1) / 2)
            report_ri = []
            field = []

            for i in range(num_ri + 1):
                report_ri.append(
                    [round((ri.iloc[num_ri - i, 0] + ri.iloc[num_ri + i, 0]) / 2, 3)]
                    if i != 0
                    else [ri.iloc[num_ri, 0]]
                )
                field.append(
                    str(round((-ri.index[num_ri + i] + ri.index[num_ri - i]) / 2 / (ri.index).max(), 2)) + "F"
                    if i != 0
                    else "0.0F"
                )

            ri_df_report = pd.DataFrame(report_ri, index=field)

        else:
            ri_df_report = None

        return ri_df_report

    def aa_mtf(self):

        aa_dfs = self.get_tf()

        tf_sag_df = aa_dfs["tf_sag"]
        tf_tan_df = aa_dfs["tf_tan"]
        tf_IH = aa_dfs["tf_IH"]

        aa_mtf = mtf_tilt_correction(tf_sag_df, tf_tan_df, tf_IH).run()

        return aa_mtf

    def get_all(self, raw, raw_index):

        self.raw = raw
        self.raw_index = raw_index
        date, freq = self.measure_info()

        cra = self.get_cra()
        dist = self.get_dist()
        ri = self.get_ri()

        all_data = {
            "mtf": self.get_mtf(),
            "tf": self.get_tf(),
            "cra": cra,
            "ri": ri,
            "dist": dist,
            "lateral": self.get_lateral(),
            "lsa": self.get_lsa(),
            "efl": self.get_efl(),
            "aa_mtf": self.aa_mtf(),
            "date": date,
            "freq": freq,
            "cra_report": self.get_report_cra(cra),
            "ri_report": self.get_report_ri(ri),
            "dist_report": self.get_report_dist(dist),
        }

        return all_data


class mtf_tilt_correction:

    def __init__(self, tf_sag_df, tf_tan_df, tf_IH):
        self.tf_sag_df = tf_sag_df
        self.tf_tan_df = tf_tan_df
        self.tf_IH = tf_IH

    def _prepare_data(self, df):
        return df.iloc[:, 1:-1]

    def _polyfit(self, x, y, degree=10):
        x_new = (x - x[int(len(x) / 2)]).astype(float)
        coeffs = np.polyfit(x_new, y, degree)
        x_values = np.linspace(x_new.min(), x_new.max(), 100)
        y_values = np.polyval(coeffs, x_values)
        # offset = np.max(y_values) - np.max(y)
        peak = x_values[np.argmax(y_values)]
        return coeffs, peak, x_values, y_values

    def _calculate_tilt(self, peak_values):
        x_data = np.array(self.tf_IH[1:-1]).reshape(-1, 1)
        ransac = RANSACRegressor(min_samples=3, residual_threshold=6)
        ransac.fit(x_data, peak_values)
        tilt_values = ransac.predict(x_data)
        tilt_values = tilt_values - tilt_values[int(len(tilt_values) / 2)]
        return tilt_values

    def _correct_mtf(self, df_sag, df_tan, coeffs_sag_list, coeffs_tan_list, tilt_values):
        aa_sag = []
        aa_tan = []
        aa_x_list = []
        for i in range(len(df_sag.columns)):
            x_org = df_sag.index
            # sag_org = pd.to_numeric(df_sag.iloc[:, i])
            # tan_org = pd.to_numeric(df_tan.iloc[:, i])
            x_new = (x_org - x_org[int(len(x_org) / 2)]).astype(float)
            x_values = np.linspace(x_new.min(), x_new.max(), 100)
            aa_x = x_values - tilt_values[i]
            sag_adj_tf = np.polyval(coeffs_sag_list[i], x_values)
            tan_adj_tf = np.polyval(coeffs_tan_list[i], x_values)
            center_best_index = self._get_index_of_min_abs_value(aa_x)
            center_best_tan = tan_adj_tf[center_best_index]
            center_best_sag = sag_adj_tf[center_best_index]
            aa_x_list.append(aa_x)
            aa_sag.append(center_best_sag)
            aa_tan.append(center_best_tan)
        return aa_sag, aa_tan, aa_x_list

    def _get_index_of_min_abs_value(self, array):
        return np.argmin(np.abs(array))

    def run(self):

        try:
            df_sag_temp = self._prepare_data(self.tf_sag_df)
            df_tan_temp = self._prepare_data(self.tf_tan_df)

            coeffs_sag_list = []
            peak_sag_list = []
            for cols in df_sag_temp.columns:
                y = pd.to_numeric(df_sag_temp[cols]).values
                x = df_sag_temp.index
                coeffs_sag, peak_sag, _, _ = self._polyfit(x, y)
                coeffs_sag_list.append(coeffs_sag)
                peak_sag_list.append(peak_sag)

            coeffs_tan_list = []
            peak_tan_list = []
            for cols in df_tan_temp.columns:
                y = pd.to_numeric(df_tan_temp[cols]).values
                x = df_tan_temp.index
                coeffs_tan, peak_tan, _, _ = self._polyfit(x, y)
                coeffs_tan_list.append(coeffs_tan)
                peak_tan_list.append(peak_tan)

            tan_tilt = self._calculate_tilt(peak_tan_list)
            sag_tilt = self._calculate_tilt(peak_sag_list)
            tilt = (sag_tilt + tan_tilt) / 2
            # tan_adj = tan_tilt - tilt
            # sag_adj = sag_tilt - tilt

            aa_sag, aa_tan, aa_x_list = self._correct_mtf(
                df_sag_temp, df_tan_temp, coeffs_sag_list, coeffs_tan_list, tilt
            )

            mtf_aa_df = pd.DataFrame({"Sag": aa_sag, "Tan": aa_tan}).T
            aa_field = np.around((self.tf_IH / np.max(self.tf_IH)), 2).astype(str) + "F"
            mtf_aa_df.columns = aa_field[1:-1]
        except Exception:
            mtf_aa_df = None
        return mtf_aa_df


# lensreader = LensReader()
# raw, raw_index = lensreader.read_file()

# lens_data = LensData(raw,raw_index)
# ri = lens_data.get_ri()
