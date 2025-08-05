from io import BytesIO
from PIL import Image
import numpy as np
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
from scipy.interpolate import interp1d
import win32clipboard
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from matplotlib.figure import Figure

class LensPlotter(QWidget):

    def __init__(self):
        super(LensPlotter,self).__init__()
        self.layout = QVBoxLayout(self)
        
    def plot_cra(self,ax,cra):

        
        try:
            cra_field = cra.index/max(cra.index)
            cra_field =  [f"{-round(abs(num), 1)}F" if num < 0 else f"{round(num, 1)}F" for num in cra_field]
        except TypeError:
            cra_field = cra.index

        self.setup_subplot(ax, 'CRA (deg)', cra_field,y_data=cra.iloc[:,0], y_label='CRA (deg)', ylim_top=max(cra.iloc[:,0])+5)

    def plot_ri(self, ax, ri):
        
        try:
            ri_field = ri.index/max(ri.index)
            ri_field =  [f"{-round(abs(num), 1)}F" if num < 0 else f"{round(num, 1)}F" for num in ri_field]
        except TypeError:
            ri_field = ri.index

        
        self.setup_subplot(ax, 'RI (%)', ri_field ,y_data=ri.iloc[:,0], y_label='Relative Illumination (%)', ylim_top=max(ri.iloc[:,0]))

    def plot_dist(self, ax, dist):

        if dist is None:
            pass
        else:
            try:
                dist_field = dist.index/max(dist.index)
                dist_field =  [f"{-round(abs(num), 1)}F" if num < 0 else f"{round(num, 1)}F" for num in dist_field]
            except TypeError:
                dist_field = dist.index

            self.setup_subplot(ax, 'Distortion (%)', dist_field, y_data=dist.iloc[:,0], y_label='Distortion (%)', ylim_top=max(dist.iloc[:,0]))

    def plot_lateral_color(self, ax, lateral_df):

        
        ax.set_title('Lateral Color(um)')
        Lateral_field = lateral_df.index/max(lateral_df.index)
        Lateral_field =  [f"{-round(abs(num), 1)}F" if num < 0 else f"{round(num, 1)}F" for num in Lateral_field]
        ax.plot(Lateral_field, lateral_df.iloc[:,0], label='644nm', color='#e74c3c', linewidth=4)
        ax.plot(Lateral_field, lateral_df.iloc[:,1], label='560nm', color='#2ecc71', linewidth=4)
        ax.plot(Lateral_field, lateral_df.iloc[:,2], label='546nm', color='#3498db', linewidth=4)
        ax.plot(Lateral_field, lateral_df.iloc[:,3], label='480nm', color='#9b59b6', linewidth=4)
        ax.plot(Lateral_field, lateral_df.iloc[:,3], label='436nm', color='#f1c40f', linewidth=4)
        ax.set_ylim(-5, 5)
        ax.set_xticks(Lateral_field)
        ax.set_xticklabels([i for i in Lateral_field], rotation=90)
        ax.legend(loc='upper center')
        ax.set_xlabel('Field (deg)', fontsize=8)
        ax.set_ylabel('Lateral Color (um)', fontsize=8)

    def plot_lca(self, ax, LSA_df):
        ax.set_title('LCA (um)')
        
        f = interp1d(LSA_df['Wavelength'], LSA_df['Focal Shift'], kind='cubic')
        wavelengths_interp = np.linspace(LSA_df['Wavelength'].min(), LSA_df['Wavelength'].max(), 100)
        ax.plot(wavelengths_interp, f(wavelengths_interp), color='#3498db', linewidth=4)
        for i, row in LSA_df.iterrows():
            ax.scatter(row['Wavelength'], row['Focal Shift'], marker='o', color='#3498db')
            ax.annotate(f"{row['Focal Shift']:.3f}", (row['Wavelength'], row['Focal Shift']), textcoords="offset points", xytext=(0,10), ha='center', fontsize=10, fontweight='bold')
        ax.set_xlabel('Wavelength(nm)', fontsize=8)
        ax.set_ylabel('Focal Shift(um)', fontsize=8)

    def plot_mtf(self, ax, mtf_aa_df,freq):
        
        ax.set_title('MTF '+str(freq)+'lp/mm')
        ax.plot(mtf_aa_df.columns, mtf_aa_df.loc['Sag'], marker='o', color='#2ecc71', linewidth=4, label="Sag")
        ax.plot(mtf_aa_df.columns, mtf_aa_df.loc['Tan'], marker='o', color='#e74c3c', linewidth=4, label="Tan")
        ax.set_ylim(0,1)
        ax.legend(loc='upper right')
        for idx, data in enumerate(mtf_aa_df.values[0]):
            ax.annotate(f'{round(data, 2)}', xy=(idx, data), xytext=(0, 5),
                         textcoords='offset points', ha='center', va='bottom', fontsize=10, fontweight='bold', color='#2ecc71')
        for idx, data in enumerate(mtf_aa_df.values[1]):
            ax.annotate(f'{round(data, 2)}', xy=(idx, data), xytext=(0, -20),
                         textcoords='offset points', ha='center', va='bottom', fontsize=10, fontweight='bold', color='#e74c3c')

    def setup_subplot(self, ax, title, field,y_data=None, y_label='', ylim_top=None):

        ax.set_title(title)
        ax.tick_params(axis='both', which='major', labelsize=8)
        if y_data is not None:
            ax.plot(field, y_data, marker='o', linewidth=3)
        ax.set_ylabel(y_label, fontsize=8)
        if ylim_top is not None:
            ax.set_ylim(top=ylim_top)
        for x, y in zip(field, y_data):
            ax.annotate(f'{round(y, 2)}', xy=(x, y), xytext=(0, 5),
                        textcoords='offset points', ha='center', va='bottom', fontsize=10, fontweight='bold')
  

    def plot_graph(self, all_data):
            

        fig = Figure(figsize=(16, 8))
        
        fig.suptitle('Lens Measurement Result', fontsize=25)
        gs = gridspec.GridSpec(2, 4, figure=fig)
        self.canvas = FigureCanvas(fig)
        self.layout.addWidget(self.canvas)

        axs1 = fig.add_subplot(gs[0, 0])
        self.plot_cra(axs1, all_data['cra_report'])

        axs2 = fig.add_subplot(gs[0,1])
        self.plot_ri(axs2, all_data['ri_report'])

        axs3 = fig.add_subplot(gs[0,2])
        self.plot_dist(axs3, all_data['dist_report'])

        axs4 = fig.add_subplot(gs[:,3])
        self.plot_lateral_color(axs4, all_data['lateral'])

        axs5 = fig.add_subplot(gs[1,0])
        self.plot_lca(axs5, all_data['lsa'])

        axs6 = fig.add_subplot(gs[1,1:3])
        self.plot_mtf(axs6, all_data['aa_mtf'], all_data['freq'])
        fig.tight_layout(rect=[0,0,1,0.93])
        
        buf = BytesIO()
        fig.savefig(buf, bbox_inches='tight', format='png', dpi=150) 
        buf.seek(0)
        image = Image.open(buf)

        new_size = (int(image.width * 0.5), int(image.height * 0.5))
        image = image.resize(new_size, Image.LANCZOS)
        
        output = BytesIO()
        image.convert('RGB').save(output, 'BMP')
        data = output.getvalue()[14:]
        output.close

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()


        
        
        

# if __name__ == "__main__":

    # lensreader = LensReader()
    # raw, raw_index = lensreader.read_file()
    # lens_plotter = LensPlotter(raw, raw_index)
    # lens_plotter.plot_show()


