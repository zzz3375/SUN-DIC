"""
SUN-DIC 分析脚本 — Canon 数据集

基于 DICpy case_study.py 中的 ROI 定义:
  ROI: (2430, 2200) → (2524, 7339)  [94 × 5139 像素]

使用方法:
  1. 修改 settings.ini 中的 TargetImage 控制图像数量
  2. 运行: python run_canon_dic.py
"""

import sys
import os

# Ensure the local SUN-DIC source is on the path
sys.path.insert(0, r"C:\Users\13694\SUN-DIC")

from sundic.settings import Settings
from sundic import sundic
from sundic import post_process as pp
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# 1. Load settings
# ---------------------------------------------------------------------------
settings_file = r"C:\Users\13694\SUN-DIC\run_canon_settings.ini"
print(f"Loading settings from: {settings_file}")
settings = Settings.fromSettingsFile(settings_file)
print(settings)

# ---------------------------------------------------------------------------
# 2. Run the DIC analysis
# ---------------------------------------------------------------------------
results_file = r"C:\Users\13694\SUN-DIC\canon_results.bin"

print("\n" + "=" * 60)
print("Starting DIC analysis...")
print("=" * 60)

returnData = sundic.planarDICLocal(settings, results_file)

print(f"\nAnalysis complete! {len(returnData)} image pairs processed.")
print(f"Results saved to: {results_file}")

# ---------------------------------------------------------------------------
# 3. Post-process and plot the last image pair
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("Post-processing results...")
print("=" * 60)

# Displacement contour (last image pair)
print("\n--- Displacement Magnitude ---")
disp, nRows, nCols = pp.getDisplacements(results_file, imgPair=-1)
print(f"  Grid: {nRows} rows × {nCols} cols = {nRows*nCols} subsets")
print(f"  Valid displacement points: {np.count_nonzero(~np.isnan(disp[:, pp.DispComp.DISP_MAG]))}")

# Strain (last image pair)
print("\n--- Strain ---")
strains, nRows, nCols = pp.getStrains(results_file, imgPair=-1, smoothWindow=9, smoothOrder=2)
print(f"  Strain grid: {nRows} rows × {nCols} cols")

# Plot results
print("\nGenerating plots...")

# Displacement magnitude contour
fig1 = pp.plotDispContour(
    results_file, imgPair=-1,
    dispComp=pp.DispComp.DISP_MAG,
    alpha=0.7,
    plotImage=True,
    showPlot=False,
    return_fig=True
)
fig1.savefig(r"C:\Users\13694\SUN-DIC\canon_disp_mag.png", dpi=150)
print("  Saved: canon_disp_mag.png")

# X displacement contour
fig2 = pp.plotDispContour(
    results_file, imgPair=-1,
    dispComp=pp.DispComp.X_DISP,
    alpha=0.7,
    plotImage=True,
    showPlot=False,
    return_fig=True
)
fig2.savefig(r"C:\Users\13694\SUN-DIC\canon_disp_x.png", dpi=150)
print("  Saved: canon_disp_x.png")

# Y displacement contour
fig3 = pp.plotDispContour(
    results_file, imgPair=-1,
    dispComp=pp.DispComp.Y_DISP,
    alpha=0.7,
    plotImage=True,
    showPlot=False,
    return_fig=True
)
fig3.savefig(r"C:\Users\13694\SUN-DIC\canon_disp_y.png", dpi=150)
print("  Saved: canon_disp_y.png")

# Von Mises strain contour
fig4 = pp.plotStrainContour(
    results_file, imgPair=-1,
    strainComp=pp.StrainComp.VM_STRAIN,
    alpha=0.7,
    plotImage=True,
    showPlot=False,
    return_fig=True
)
fig4.savefig(r"C:\Users\13694\SUN-DIC\canon_strain_vm.png", dpi=150)
print("  Saved: canon_strain_vm.png")

# Correlation (ZNCC) contour
fig5 = pp.plotZNCCContour(
    results_file, imgPair=-1,
    alpha=0.7,
    plotImage=True,
    showPlot=False,
    return_fig=True
)
fig5.savefig(r"C:\Users\13694\SUN-DIC\canon_zncc.png", dpi=150)
print("  Saved: canon_zncc.png")

print("\nDone! All results saved.")
plt.close('all')
