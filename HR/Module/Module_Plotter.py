from io import BytesIO

import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QVBoxLayout, QWidget

# Plot 은 Analyzer 를 통해 전처리 된 상태에서 그릴 수 있음
# Plot 버튼은 1개 파일만 선택했을떄만 사용 가능하도록 구현
# Report Save 시에는 Handler 에서 file, idx 로 For 구문을 통해 Plotter 인스턴스를 연결

# SFR_result_dfs --> ResultPlotter : SFR Center Best 값을 그려주는 Plot
# SFR_dfs, SFR_dfs_mm, AA_SFR_dfs --> TF_Plotter, Focus_Plane Plotter
# SFR_dfs_mm --> AA_SFR_dfs --> Report Plotter
# Shading_dfs --> shading plotter


class ModulePlotter(QWidget):

    def __init__(self):

        super(ModulePlotter, self).__init__()
        self.layout = QVBoxLayout(self)
        self.buf = BytesIO()

    def clear_layout(self):
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def shading_plotter(self, shading_result_dfs, draw_only=False):

        fig = Figure()
        canvas = FigureCanvas(fig)

        columns, rows, log_x, log_y = shading_result_dfs["shading_plot"][:4]
        oc_x_um, oc_y_um, vig_lu, vig_ru, vig_ld, vig_rd = shading_result_dfs["shading_result"].iloc[0]
        shading_df = shading_result_dfs["shading"]

        if hasattr(self, "canvas"):
            self.layout.removeWidget(canvas)
            canvas.setParent(None)
        self.setWindowTitle("OC/RI")
        self.resize(800, 600)
        self.clear_layout()
        self.layout.addWidget(canvas)
        ax = fig.add_subplot(111)

        # plt.close()

        ax.imshow(shading_df, cmap="Greys_r", interpolation="auto")
        ax.axis("off")
        # plt.colorbar()
        ax.scatter(int(columns.mean()), int(rows.mean()), c="r", s=50)
        ax.text(
            int(columns.mean()),
            int(rows.mean() - len(shading_df.columns) / 25),
            "OC X : " + str(oc_x_um) + " / OC Y : " + str(oc_y_um) + " [um]",
            ha="center",
            va="center",
            color="b",
            size=15,
        )

        ax.text(0, 0, str(int(round(vig_lu, 2) * 100)) + "%", ha="left", va="top", color="w", size=20)
        ax.text(log_x, 0, str(int(round(vig_ru, 2) * 100)) + "%", ha="right", va="top", color="w", size=20)
        ax.text(0, log_y, str(int(round(vig_ld, 2) * 100)) + "%", ha="left", va="bottom", color="w", size=20)
        ax.text(log_x, log_y, str(int(round(vig_rd, 2) * 100)) + "%", ha="right", va="bottom", color="w", size=20)

        if draw_only:
            canvas.draw()
        else:
            return canvas

    def check_param(self, freq, sensitivity):

        self.freq = freq
        self.sensitivity = sensitivity

    def TF_plotter(self, SFR_dfs, ax=None, draw_only=True):

        show_plot = False
        if ax is None:
            self.setWindowTitle("Through Focus SFR")
            self.resize(800, 600)
            self.clear_layout()

            fig = Figure()
            canvas = FigureCanvas(fig)
            self.layout.addWidget(canvas)
            ax = fig.add_subplot(111)
            show_plot = True

        SFR_df = SFR_dfs["SFR"]

        if SFR_df.index.dtype == "object":
            x = SFR_df.index.str.replace(".000", "").astype(int)
            xlabel = "DAC"
        elif SFR_df.index.dtype == "float64":
            x = SFR_df.index
            xlabel = "um"

        ax.set_xlabel(xlabel)
        ax.set_ylabel("SFR")
        ax.text(0.3, 0.9, "Freq :" + str(self.freq) + "cycle/pixel", ha="center", va="center", transform=ax.transAxes)
        for _, label in enumerate(SFR_df.columns):
            y = SFR_df[label]
            ax.plot(x, y)  # label 범례 라벨
            # ax.legend(loc='lower center',ncol=int(len(SFR_df.columns)/6))

        if not show_plot and draw_only:  # Report 그리고 (Show_plot = True), Draw_Only 가 False 일때
            pass
        elif show_plot and not draw_only:  # Report 안그리고 Draw_Only 가 False 일때 (데이터만 필요할때)
            return canvas
        else:
            canvas.draw()  # Report 안그리고, Draw_Only 가 True 일때 (TF Plotter 의 그래프만 그릴때)

    def result_plotter(self, SFR_result_dfs, ax=None, draw_only=True):

        show_plot = False
        if ax is None:
            self.setWindowTitle("SFR Result")
            self.resize(800, 600)
            self.clear_layout()
            fig = Figure()
            canvas = FigureCanvas(fig)
            self.layout.addWidget(canvas)
            ax = fig.add_subplot(111)
            show_plot = True

        x_result = SFR_result_dfs["x"]
        y_result = SFR_result_dfs["y"]
        SFR_result = SFR_result_dfs["SFR"]

        # 250718 Nan 데이터 처리할 수 있도록 바꿈
        scatter_df = pd.DataFrame({"x": x_result, "y": y_result, "z": SFR_result})

        # Nan이 들어오면 nan은 포함 안하고 산점도를 그려서 강제 영역 설정
        xmin, xmax = scatter_df["x"].min(), scatter_df["x"].max()
        xmin -= (xmax - xmin) * 0.05
        xmax += (xmax - xmin) * 0.05
        ymin, ymax = scatter_df["y"].min(), scatter_df["y"].max()
        ymin -= (ymax - ymin) * 0.05
        ymax += (ymax - ymin) * 0.05
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

        sns.scatterplot(data=scatter_df, x="x", y="y", hue="z", palette="coolwarm", ax=ax)
        ax.legend().set_visible(False)
        ax.set_xlabel("x(pixel)")
        ax.set_ylabel("y(pixel)")
        fig = ax.get_figure()

        ax.text(0.3, 0.9, "Freq :" + str(self.freq) + "cycle/pixel", ha="center", va="center", transform=ax.transAxes)
        # # 각 점 위에 z 값을 표시
        fontsize = ax.get_window_extent().height / len(scatter_df) * 2

        text_position = np.max(x_result) / 190  # Row['y'] 의 값을 상대적으로 만들어야함

        for i, row in scatter_df.iterrows():
            txt_val = str(int(row["z"])) if ~np.isnan(row["z"]) else "nan"
            ax.text(
                row["x"],
                row["y"] + text_position,
                txt_val,
                ha="center",
                va="center",
                size=fontsize,
                weight="bold",
            )

        if not show_plot and draw_only:  # Report 그리고 (Show_plot = True), Draw_Only 가 False 일때
            pass
        elif show_plot and not draw_only:  # Report 안그리고 Draw_Only 가 False 일때 (데이터만 필요할때)
            return canvas
        else:
            canvas.draw()  # Report 안그리고, Draw_Only 가 True 일때 (TF Plotter 의 그래프만 그릴때

    def focus_plane_plotter(self, AA_SFR_dfs, angles, ax=None, draw_only=True):

        show_plot = False  # Make Report 할때는 Ax 를 그리면 안됨
        if ax is None:
            self.setWindowTitle("Focus Plane")
            self.resize(800, 600)
            self.clear_layout()
            fig = Figure()
            canvas = FigureCanvas(fig)
            self.layout.addWidget(canvas)
            ax = fig.add_subplot(111, projection="3d")
            show_plot = True

        x = AA_SFR_dfs["x"]
        y = AA_SFR_dfs["y"]
        z = AA_SFR_dfs["z"]

        X, Y, Z, angle, phi, _ = angles

        ax.scatter(x, y, z, color="Orange", label="Peak Position")
        ax.plot_surface(X, Y, Z, color="orange", alpha=0.5)
        ax.set_zlim(np.min(z), np.max(z))
        ax.set_title(f"Tilt angle : {'θ'} = {angle:.2f}°\n Tilt direction : {'φ'} = {phi:.2f}°")
        # ax.text2D(0.25,0.45, f'Slope of Surface : {angle1:.2f}°', fontsize=20, ha='center', transform=ax.transAxes)

        if not show_plot and draw_only:  # Report 그리고 (Show_plot = True), Draw_Only 가 False 일때
            pass
        elif (
            show_plot and not draw_only
        ):  # Report 합치는게 아니라 개별 그래프 Draw_Only 가 False 일때 (데이터만 필요할때)
            return canvas
        else:
            canvas.draw()  # Report 안그리고, Draw_Only 가 True 일때 (TF Plotter 의 그래프만 그릴때

    def _make_report_form(self):

        self.setWindowTitle("Report")
        self.resize(1600, 1200)
        self.clear_layout()

        # fig = plt.figure(figsize=(24,12), facecolor='linen')
        fig = Figure(figsize=(24, 12), facecolor="linen")
        gs = gridspec.GridSpec(2, 2, width_ratios=[1, 1], height_ratios=[2, 1], figure=fig)
        canvas = FigureCanvas(fig)
        self.layout.addWidget(canvas)

        ax1 = fig.add_subplot(gs[0, 0])  # SFR_result_org
        ax2 = fig.add_subplot(gs[0, 1])  # SFR_result_fitted

        gs_bottom = gridspec.GridSpecFromSubplotSpec(1, 4, subplot_spec=gs[1, :])

        ax3 = fig.add_subplot(gs_bottom[0, 0], projection="3d")
        ax4 = fig.add_subplot(gs_bottom[0, 1])
        ax5 = fig.add_subplot(gs_bottom[0, 2], projection="3d")
        ax6 = fig.add_subplot(gs_bottom[0, 3])

        ax1.set_title("SFR_result", fontsize=20)
        ax2.set_title("Tilt Corrected SFR_result", fontsize=20)
        # ax3.set_title("Focus_Plane")
        ax4.set_title("Through Focus")
        # ax5.set_title("Focus_Plane")
        ax6.set_title("Through Focus")

        ax1.set_xlabel("x")
        ax1.set_ylabel("y")

        ax2.set_xlabel("x")
        ax2.set_ylabel("y")

        ax3.set_xlabel("x")
        ax3.set_ylabel("y")
        ax3.set_zlabel("z")

        ax5.set_xlabel("x")
        ax5.set_ylabel("y")
        ax5.set_zlabel("z")

        axs = canvas, fig, ax1, ax2, ax3, ax4, ax5, ax6

        return axs

    def make_report(self, SFR_data, AA_SFR_data, draw_only=True):

        axs = self._make_report_form()
        canvas, fig, ax1, ax2, ax3, ax4, ax5, ax6 = axs
        # print(canvas)

        self.result_plotter(SFR_data["SFR_result"], ax1, draw_only=True)
        self.focus_plane_plotter(SFR_data["SFR_df_mm"], SFR_data["angle"], ax3, draw_only=True)
        self.TF_plotter(SFR_data["SFR_df"], ax4, draw_only=True)

        # AA 후 데이터

        self.result_plotter(AA_SFR_data["SFR_result"], ax2, draw_only=True)
        self.focus_plane_plotter(AA_SFR_data["SFR_df"], AA_SFR_data["angle"], ax5, draw_only=True)
        self.TF_plotter(AA_SFR_data["SFR_df"], ax6, draw_only=True)

        # plt.show()
        if draw_only:
            fig.tight_layout()
            canvas.draw()
        else:
            return canvas
