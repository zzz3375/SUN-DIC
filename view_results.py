"""
SUN-DIC 交互式结果查看器
使用 matplotlib 替代 PyQt6 GUI，加载 results.bin 并查看位移/应变/相关系数。
"""

import sys
import os
sys.path.insert(0, r"C:\Users\13694\SUN-DIC")

from sundic import post_process as pp
from sundic.util import datafile
import numpy as np
import matplotlib
matplotlib.use("qt5agg")  # Python 自带，无需额外安装
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
results_file = r"C:\Users\13694\SUN-DIC\canon_results.bin"

# Load settings
df = datafile.DataFile.openReader(results_file)
_, _, setDict = df.readHeading()
df.close()

nPairs = datafile.DataFile.openReader(results_file).getNumImagePairs()
print(f"Results file: {results_file}")
print(f"Number of image pairs: {nPairs}")

# ---------------------------------------------------------------------------
# Default settings
img_pair = nPairs - 1
disp_comp = pp.DispComp.DISP_MAG
strain_comp = pp.StrainComp.VM_STRAIN
show_image = True
alpha = 0.7

# ---------------------------------------------------------------------------
def plot_displacement():
    """Plot displacement contour."""
    plt.close("all")
    comp_name = disp_comp.display_name
    print(f"\nPlotting: Image pair {img_pair} - {comp_name}")
    
    fig, ax = plt.subplots(figsize=(8, 10))
    
    pp.plotDispContour(
        results_file, imgPair=img_pair,
        dispComp=disp_comp,
        alpha=alpha,
        plotImage=show_image,
        showPlot=False
    )
    
    plt.title(f"{comp_name} (Image pair {img_pair}/{nPairs-1})")
    plt.tight_layout()
    plt.draw()
    plt.show(block=False)


def plot_strain():
    """Plot strain contour."""
    plt.close("all")
    comp_name = strain_comp.display_name
    print(f"\nPlotting: Image pair {img_pair} - {comp_name}")
    
    fig, ax = plt.subplots(figsize=(8, 10))
    
    pp.plotStrainContour(
        results_file, imgPair=img_pair,
        strainComp=strain_comp,
        alpha=alpha,
        plotImage=show_image,
        showPlot=False
    )
    
    plt.title(f"{comp_name} (Image pair {img_pair}/{nPairs-1})")
    plt.tight_layout()
    plt.draw()
    plt.show(block=False)


def plot_zncc():
    """Plot ZNCC correlation contour."""
    plt.close("all")
    print(f"\nPlotting: Image pair {img_pair} - ZNCC Correlation")
    
    fig, ax = plt.subplots(figsize=(8, 10))
    
    pp.plotZNCCContour(
        results_file, imgPair=img_pair,
        alpha=alpha,
        plotImage=show_image,
        showPlot=False
    )
    
    plt.title(f"ZNCC Correlation (Image pair {img_pair}/{nPairs-1})")
    plt.tight_layout()
    plt.draw()
    plt.show(block=False)


def stats():
    """Print statistics for current image pair."""
    disp, nRows, nCols = pp.getDisplacements(results_file, imgPair=img_pair, smoothWindow=0)
    valid = np.count_nonzero(~np.isnan(disp[:, pp.DispComp.DISP_MAG]))
    total = nRows * nCols
    
    print(f"\n=== Statistics for Image Pair {img_pair} ===")
    print(f"  Grid: {nRows} rows x {nCols} cols = {total} subsets")
    print(f"  Valid: {valid} / {total} ({100*valid/total:.1f}%)")
    
    if valid > 0:
        mask = ~np.isnan(disp[:, pp.DispComp.DISP_MAG])
        x_disp = disp[mask, pp.DispComp.X_DISP]
        y_disp = disp[mask, pp.DispComp.Y_DISP]
        mag = disp[mask, pp.DispComp.DISP_MAG]
        print(f"  X disp:  [{x_disp.min():.2f}, {x_disp.max():.2f}]  mean={x_disp.mean():.2f}")
        print(f"  Y disp:  [{y_disp.min():.2f}, {y_disp.max():.2f}]  mean={y_disp.mean():.2f}")
        print(f"  Mag:     [{mag.min():.2f}, {mag.max():.2f}]  mean={mag.mean():.2f}")


# ---------------------------------------------------------------------------
# Interactive menu
def menu():
    global img_pair, disp_comp, strain_comp, show_image, alpha
    
    while True:
        print("\n" + "=" * 50)
        print(f"  Current pair: [{img_pair}/{nPairs-1}]  |  Image overlay: {show_image}  |  Alpha: {alpha}")
        print("=" * 50)
        print("  1. Displacement Magnitude          5. X Displacement")
        print("  2. Von Mises Strain                6. Y Displacement")
        print("  3. ZNCC Correlation                7. Sheer Strain")
        print("  4. Statistics                      8. X / Y Strain")
        print()
        print("  n / p   Next / Previous image pair")
        print("  j N     Jump to pair N")
        print("  i       Toggle image overlay")
        print("  a       Set alpha (0.0-1.0)")
        print("  q       Quit")
        print("-" * 50)
        
        cmd = input("> ").strip().lower()
        
        if cmd == "q":
            break
        elif cmd == "1":
            disp_comp = pp.DispComp.DISP_MAG
            plot_displacement()
        elif cmd == "2":
            strain_comp = pp.StrainComp.VM_STRAIN
            plot_strain()
        elif cmd == "3":
            plot_zncc()
        elif cmd == "4":
            stats()
        elif cmd == "5":
            disp_comp = pp.DispComp.X_DISP
            plot_displacement()
        elif cmd == "6":
            disp_comp = pp.DispComp.Y_DISP
            plot_displacement()
        elif cmd == "7":
            strain_comp = pp.StrainComp.SHEAR_STRAIN
            plot_strain()
        elif cmd == "8":
            strain_comp = pp.StrainComp.X_STRAIN
            plot_strain()
        elif cmd == "n":
            img_pair = min(nPairs - 1, img_pair + 1)
            print(f"  → Image pair: {img_pair}")
        elif cmd == "p":
            img_pair = max(0, img_pair - 1)
            print(f"  → Image pair: {img_pair}")
        elif cmd.startswith("j"):
            try:
                val = int(cmd.split()[1])
                img_pair = max(0, min(nPairs - 1, val))
                print(f"  → Image pair: {img_pair}")
            except:
                print("  Usage: j <number>")
        elif cmd == "i":
            show_image = not show_image
            print(f"  → Image overlay: {show_image}")
        elif cmd == "a":
            try:
                val = float(input("  Alpha (0.0-1.0): "))
                alpha = max(0.0, min(1.0, val))
            except:
                pass
        else:
            print("  Unknown command.")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  SUN-DIC Interactive Result Viewer")
    print("=" * 50)
    stats()
    menu()
    print("\nGoodbye!")
