# script_generator.py

import tkinter as tk
from tkinter import filedialog

class ScriptGenerator:
    def __init__(self, checksum_vars=None):
        self.checksum_vars = checksum_vars if checksum_vars else {
            "mtf": 0,
            "tf": 0,
            "cra": 0,
            "ri": 0,
            "dist": 0,
            "lateral": 0,
            "longi": 0,
            "efl": 0 
        }
        self.scripts = {
            "mtf": self._mtf_script,
            "tf": self._tf_mtf_script,
            "cra": self._cra_script,
            "ri": self._ri_script,
            "dist": self._dist_script,
            "lateral": self._lateral_script,
            "lsa": self._longi_script,
        }

    def generate_script(self, ih, name: str, sensor: str, freq):
        """Generate a script based on the provided parameters."""
        script_init = self._script_init(ih, name, sensor, freq)
        script_end = self._script_end()
        script = script_init
        for key, value in self.checksum_vars.items():
            if value == 1 and key in self.scripts:
                script += self.scripts[key](ih, freq)
        script += script_end
        return script

    def _script_init(self, ih, name: str, sensor: str, freq):
        """Generate the initial part of the script."""
        return f"""
Proc Main
    SelectRange 3
    SelectFilter 1
    Report ClearAll
    MoveAbs "SampleRotation", 0, 100
    Rem MoveAbs "ImageHeight", 0, 100
    Rem MoveAbs "ObjectAngle", 0, 100
    SetParam "MainWnd|Company", "Samsung,S.LSI"
    SetParam "MainWnd|Operator", "{name}"
    SetParam "MainWnd|SampleID", "{sensor}"
    Rem ThrougFocus
    ThroughFocus 100, 0.1, {freq*2}, {freq}, {freq}, 20, 0.03, "both", 1
    Report AddResult, "Through Focus", 1, 1, 1
    SelectRange 2
    Rem EFL
    Loop 5
    EFLMagDs
    LoopEnd
    Report AddResult, "EFL / Magn. (DbSl)", 1, 1, 1
    SelectRange 3
"""

    def _script_end(self):
        """Generate the ending part of the script."""
        return rf"""
    Report Save, "d:\\", "Result", 2
ProcEnd None
"""

    def _mtf_script(self, ih, freq):
        """Generate the MTF script."""

        if not self.posfile:
            mtf = rf"""
    SelectRange 3
    Rem "MTFvsField"
    MtfvsField 100, 0.1, 390, 1, 20, {ih}, "Both", "Image Height"
    Report AddResult, "MTF vs. Field Image", 1, 1, 1
    Report AddResult, "MTF vs. Field Object", 1, 1, 1
"""
        else:
            mtf = rf"""
    SelectRange 3
    Rem "MTFvsField"
    MtfvsField 100, 0.1, 390, 1, 20, {ih}, "Both", "Image Height", "d:\fld_file\{self.posfile}"
    Report AddResult, "MTF vs. Field Image", 1, 1, 1
    Report AddResult, "MTF vs. Field Object", 1, 1, 1
"""
        
        return mtf

    def _tf_mtf_script(self, ih, freq):
        """Generate the TF MTF script."""
        if not self.posfile:
            tf = rf"""
    SelectRange 3
    Rem MTFvsFieldvsFocus
    MTFvsFldvsFoc 20, {ih}, 20, -0.04, 0.04, {freq}, 0.3, "Both", "Image Height"
    Report AddResult, "Field Focus 3D (Tan)" , 1, 1, 1
    Report AddResult, "Field Focus 3D (Sag)" , 1, 1, 1
    Report AddResult, "Field Focus 2D (Tan)" , 1, 1, 1
    Report AddResult, "Field Focus 2D (Sag)" , 1, 1, 1
"""
        else:
            tf =rf"""
    SelectRange 3
    Rem MTFvsFieldvsFocus
    MTFvsFldvsFoc ::SetPositionFile, "d:\fld_file\{self.posfile}"
    MTFvsFldvsFoc 20, {ih}, 20, -0.04, 0.04, {freq}, 0.3, "Both", "Image Height"
    Report AddResult, "Field Focus 3D (Tan)" , 1, 1, 1
    Report AddResult, "Field Focus 3D (Sag)" , 1, 1, 1
    Report AddResult, "Field Focus 2D (Tan)" , 1, 1, 1
    Report AddResult, "Field Focus 2D (Sag)" , 1, 1, 1
"""
        return tf

    def _cra_script(self, ih, freq):
        """Generate the CRA script."""
        if not self.posfile:
            cra = rf"""
    SelectRange 4
    Rem CRA
    CRA 20, {ih}, 10, 0.03, "Image Height"
    Report AddResult, "Chief Ray Angle", 1, 1, 1
"""
        else:
            cra = rf"""
    SelectRange 4
    Rem CRA
    CRA ::SetPositionFile, "d:\fld_file\{self.posfile}"
    CRA 20, {ih}, 10, 0.03, "Image Height"
    Report AddResult, "Chief Ray Angle", 1, 1, 1
"""
        return cra

    def _ri_script(self, ih, freq):
        """Generate the RI script."""
        if not self.posfile:
            ri = rf"""
    Rem RI
    SelectRange 6
    Relillum 20, {ih}, "Image Height"
    Report AddResult, "Relative Illumination vs. Image", 1, 1, 1
"""
        else:
            ri = rf"""
    Rem RI
    SelectRange 6
    Relillum ::SetPositionFile, "d:\fld_file\{self.posfile}",1
    Relillum 20, {ih}, "Image Height"
    Report AddResult, "Relative Illumination vs. Image", 1, 1, 1
"""

        return ri

    def _dist_script(self, ih, freq):
        """Generate the Distortion script."""
        if not self.posfile:
            dist = rf"""
    Rem Distortion
    SelectRange 3
    Distortion 100, 0.1, 20, {ih}, "Image Height"
    Report AddResult, "Dist. Rel. vs. Image", 1, 1, 1
    Report AddResult, "Dist. Rel. vs. Object", 1, 1, 1
"""
        else:
            dist = rf"""
    Rem Distortion
    SelectRange 3
    Distortion ::SetPositionFile, "d:\fld_file\{self.posfile}", 0
    Distortion 100, 0.1, 20, {ih}, "Image Height"
    Report AddResult, "Dist. Rel. vs. Image", 1, 1, 1
    Report AddResult, "Dist. Rel. vs. Object", 1, 1, 1
"""
            
        return dist

    def _lateral_script(self, ih, freq):
        """Generate the Lateral Color script."""
        if not self.posfile:
            lateral =  rf"""
    Rem LateralColor
    SelectRange 3
    LatChrAb 100, 0.1, 20, {ih}, "Image Height"
    Report AddResult, "Lateral Chromatic Aberration", 1, 1, 1
"""
        else:
            lateral =  rf"""
    Rem LateralColor
    SelectRange 3
    LatChrAb 100, 0.1, 20, {ih}, "Image Height","","d:\fld_file\{self.posfile}"
    Report AddResult, "Lateral Chromatic Aberration", 1, 1, 1
"""

        return lateral

    def _longi_script(self, ih, freq):
        
        """Generate the Longitudinal Chromatic Aberration script."""
        return f"""
    Rem LongitudinalChromaticAberration
    SelectRange 3
    LongChrAb 100, 0.1, {freq}, 30, -0.06, 0.06, "Both"
    Report AddResult, "Longitudinal Chromatic Aberration", 1, 1, 1
"""

    def save_script(self, ih, name: str, sensor: str, freq, posfile, file_path=None):
        """Save the generated script to a file."""
        self.posfile = posfile
        script = self.generate_script(ih, name, sensor, freq)
        if not file_path:
            root = tk.Tk()
            root.withdraw()  
            file_path = filedialog.asksaveasfilename(
                defaultextension=".spt",
                filetypes=[("Script files", "*.spt")],
                title="Save Script"
            )
        if file_path:
            with open(file_path, "w") as f:
                f.write(script)
            # print(f"Script saved to: {file_path}")

# Example usage:
if __name__ == "__main__":
    checksum_vars = {
        "mtf": 1,
        "tf_mtf": 1,
        "cra": 1,
        "ri": 1,
        "dist": 1,
        "lateral": 1,
        "longi": 1,
        "efl": 1  # 'efl' 항목 추가
        }

    generator = ScriptGenerator(checksum_vars)
    ih = 5.625
    freq = 102  
    name = "CYS"
    sensor = "IMX874"


