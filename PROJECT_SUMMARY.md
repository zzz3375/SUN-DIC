# SUN-DIC 项目总结

---

## 1. 项目概览

**SUN-DIC**（**S**tellenbosch **U**niversity **N**-**D**igital **I**mage **C**orrelation）是斯泰伦博斯大学开发的开源 **2D 数字图像相关（Digital Image Correlation, DIC）** 软件包，当前版本 `0.0.30`。项目提供 **GUI 图形界面** 和 **Python API** 两种使用方式，用于从图像序列中分析位移场和应变场。

- **作者**: Gerhard Venter ([gventer@sun.ac.za](mailto:gventer@sun.ac.za))
- **许可证**: MIT License
- **Python 要求**: ≥ 3.11
- **PyPI 发布**: `pip install SUN-DIC`
- **GitHub**: https://github.com/gventer/SUN-DIC
- **状态**: 早期公开版本（功能稳定，接口和文档仍在持续演进）

---

## 2. 项目结构

```
SUN-DIC/
├── README.md                  # 项目说明文档
├── LICENSE                    # MIT 许可证
├── pyproject.toml             # 项目构建配置
├── requirements.txt           # 依赖列表
├── setup.py                   # setuptools 入口
├── MANIFEST.in                # 打包清单
├── presentations/             # 演示/报告材料
├── screenshots/               # 界面截图
└── sundic/                    # 主代码包
    ├── __init__.py
    ├── version.py             # 版本号 (0.0.30) + 变更日志
    ├── sundic.py              # ★ 核心 DIC 分析引擎 (~2000 行)
    ├── settings.py            # ★ 设置管理类
    ├── post_process.py        # ★ 后处理模块 (位移/应变提取、绘图)
    ├── copy_examples.py       # 示例拷贝工具
    ├── gui/                   # PyQt6 图形界面
    │   ├── mainWindow.py      #   主窗口框架
    │   ├── settingsWidget.py  #   设置面板
    │   ├── imageSetWidget.py  #   图像集面板
    │   ├── roiDefWidget.py    #   ROI 定义面板
    │   ├── analysisWidget.py  #   分析运行面板
    │   ├── resultsWidget.py   #   结果显示面板
    │   ├── buttonWidget.py    #   自定义按钮组件
    │   ├── aboutWidget.py     #   关于对话框
    │   ├── validators.py      #   输入校验器
    │   ├── icons/             #   图标资源
    │   └── Fonts/Figtree/     #   GUI 字体
    ├── util/                  # 工具库
    │   ├── fast_interp.py     #   快速插值 (Numba 加速, 来自 David Stein)
    │   ├── savitsky_golay.py  #   2D Savitzky-Golay 平滑 (来自 SciPy Cookbook)
    │   └── datafile.py        #   MsgPack 二进制结果文件读写
    ├── tools/                 # 辅助工具
    │   └── hdf5_to_tif.py     #   HDF5 转 TIFF
    ├── examples/              # 示例数据
    │   ├── settings.ini       #   配置文件模板
    │   ├── test_sundic.ipynb  #   Jupyter Notebook 示例
    │   └── planar_images/     #   示例图像
    └── docs/                  # 文档
        └── SUN-DIC_Manual.pdf # 用户手册
```

---

## 3. 核心依赖

| 依赖 | 用途 |
|------|------|
| `numpy` | 数组计算基础 |
| `opencv_python_headless` | 图像读取、高斯模糊、Sobel 梯度、AKAZE 特征检测 |
| `scikit-image` | RANSAC 仿射变换估计、形态学操作 |
| `numba` | fast_interp 的 JIT 编译加速 |
| `ray` | 多 CPU 并行计算 |
| `msgpack-numpy` | 二进制数据序列化（结果文件存储） |
| `matplotlib` | 位移/应变云图和截线图 |
| `pandas` | 数据处理 |
| `PyQt6` | GUI 图形界面 |
| `scipy` | NearestNDInterpolator、信号处理 |
| `natsort` | 图像文件自然排序 |

---

## 4. 核心算法详解

### 4.1 数字图像相关 (DIC) 基本原理

DIC 的目的是通过比较参考图像与变形图像，计算出物体表面的位移场和应变场。SUN-DIC 实现了 **局部 (local subset-based) DIC** 方法：

1. 在参考图像上定义一组 **子区（subset）** 的网格；
2. 对每个子区，在变形图像中找到最佳匹配位置；
3. 从匹配结果推算位移梯度，进而计算应变。

### 4.2 相关准则: ZNSSD

SUN-DIC 使用 **零均值归一化灰度差平方和（Zero-Mean Normalized Sum of Squared Differences, ZNSSD）** 作为匹配优度度量。其数学定义为：

$$
C_{\text{ZNSSD}} = \sum \left[ \frac{f - \bar{f}}{\tilde{f}} - \frac{g - \bar{g}}{\tilde{g}} \right]^2
$$

其中：
- $f$、$g$ 分别为参考子区和变形子区的灰度值向量
- $\bar{f}$、$\bar{g}$ 为各自均值：$\bar{f} = \frac{1}{N}\sum f_i$
- $\tilde{f}$、$\tilde{g}$ 为各自 L2 范数：$\tilde{f} = \|f - \bar{f}\|_2$

ZNSSD 对光照的线性变化具有不变性（对偏移和比例缩放不敏感）。ZNSSD 越低，匹配越好。

同时还从 $C_{\text{ZNSSD}}$ 计算 ZNCC（零均值归一化互相关系数）用于收敛判断：

$$
C_{\text{ZNCC}} = 1 - \frac{1}{2} C_{\text{ZNSSD}}
$$

### 4.3 形状函数（Shape Functions）

SUN-DIC 支持两种变形模型来描述子区的变形：

#### 仿射变换（Affine）

12 个参数（x 和 y 方向各 6 个），但实际使用的一阶仿射映射为：

$$
\begin{aligned}
\xi' &= (1 + u_x)\xi + u_y\eta + u \\
\eta' &= v_x\xi + (1 + v_y)\eta + v
\end{aligned}
$$

其中 $\xi, \eta$ 为子区局部坐标，$u, v$ 为位移，$u_x, u_y, v_x, v_y$ 为一阶位移梯度。

#### 二次变换（Quadratic）

24 个参数（每个方向 12 个系数），包含二阶梯度项：

$$
\begin{aligned}
\xi' &= \frac{1}{2}u_{xx}\xi^2 + u_{xy}\xi\eta + \frac{1}{2}u_{yy}\eta^2 + (1+u_x)\xi + u_y\eta + u \\
\eta' &= \frac{1}{2}v_{xx}\xi^2 + v_{xy}\xi\eta + \frac{1}{2}v_{yy}\eta^2 + v_x\xi + (1+v_y)\eta + v
\end{aligned}
$$

### 4.4 优化算法

#### IC-GN（Inverse Compositional Gauss-Newton）

- 逆组合公式，Hessian 矩阵在整个优化过程中保持恒定，无需每次迭代重新计算
- 计算速度快，适合大多数场景
- 不进行图像数据归一化

**迭代更新公式：**

$$
\Delta\mathbf{p} = \mathbf{H}^{-1} \mathbf{b}
$$

其中 $\mathbf{H} = \mathbf{J}^T \mathbf{J}$ 为 Hessian 矩阵，$\mathbf{b} = -\mathbf{J}^T \mathbf{r}$，$\mathbf{r} = f - \bar{f} - \frac{\tilde{f}}{\tilde{g}}(g - \bar{g})$ 为残差。$\mathbf{J}$ 为 Jacobian 矩阵：

仿射模型下：
$$
\mathbf{J}_{\text{affine}} = \begin{bmatrix}
\nabla f_x & \nabla f_x \xi & \nabla f_x \eta & \nabla f_y & \nabla f_y \xi & \nabla f_y \eta
\end{bmatrix}
$$

二次模型下扩展至 12 列（含二阶项）。

#### IC-LM（Inverse Compositional Levenberg-Marquardt）

- 在 GN 基础上引入阻尼因子 $\lambda$，在处理病态问题时更稳定
- 使用归一化坐标提升数值稳定性
- 自适应调整 $\lambda$：如果 $C_{\text{ZNSSD}}$ 改善则 $\lambda \leftarrow 0.1\lambda$，否则 $\lambda \leftarrow 10\lambda$

**迭代更新公式：**

$$
\Delta\mathbf{p} = (\mathbf{H} + \lambda \mathbf{I})^{-1} \mathbf{b}
$$

初值 $\lambda_0 = 100^{C_{\text{ZNSSD}}/4} - 1$。

#### Fast-IC-LM

- 与 IC-LM 相同，但减少了一次每迭代的插值运算
- 速度更快，精度基本不变

### 4.5 初始猜测策略：AKAZE

SUN-DIC 使用 Gauss-Legendre 积分点作为种子点，在每种子点周围进行 **AKAZE（Accelerated KAZE）** 特征检测和匹配：

1. 将参考图像和变形图像归一化到 `[0, 255]`；
2. 对每个种子点子区，使用 AKAZE 检测器提取关键点和描述符；
3. 使用 Brute-Force 匹配器（Hamming 距离）匹配关键点；
4. 通过 **RANSAC** 估计仿射变换矩阵；
5. 从仿射矩阵提取初始模型系数；
6. 选择 $C_{\text{ZNSSD}}$ 最小的点作为优化起点。

### 4.6 子区传播策略（Reliability-Guided）

优化按照可靠性引导的顺序进行：
1. 从种子点开始，优化当前子区；
2. 对当前点的四邻域（最多 8 邻域），用当前点的变形模型来估计它们的 $C_{\text{ZNSSD}}$；
3. 选择 $C_{\text{ZNSSD}}$ 最小且未分析的点作为下一个点；
4. 重复直到所有子区处理完毕。

这一策略对变形过大的区域有良好的容错性。

### 4.7 参考策略

- **Absolute（绝对）**: 每个变形图像始终与同一张基准图像对比，计算的是 **总位移**；
- **Relative（相对/增量）**: 每一对图像与前一帧对比，位移逐帧累加得到 **总位移**。适合大变形问题。

### 4.8 图像预处理

- **Sobel 梯度**: 在基准图像上先做 Sobel 边缘检测（`ksize` ≥ 3 的奇数），再做高斯模糊；
- **Gaussian Blur**: 可选的高斯模糊（可配尺寸和标准差）；
- **5 阶插值**: 使用 `fast_interp`（Numba JIT 编译的 B 样条插值）进行亚像素插值，默认 5 阶。

### 4.9 并行计算

使用 **Ray** 将子区网格按行列分块，各块并行优化。子块划分算法自动匹配图像纵横比以平衡负载。

---

## 5. 后处理

### 5.1 位移提取

从模型系数中提取 $u$（X 位移）和 $v$（Y 位移）分量，计算位移幅值：

$$
u_{\text{mag}} = \sqrt{u^2 + v^2}
$$

可选 Savitzky-Golay 平滑和 NaN 膨胀（dilation）处理。

### 5.2 应变计算

从位移场的 Savitzky-Golay 平滑梯度计算工程应变：

$$
\begin{aligned}
\varepsilon_x &= \frac{\partial u}{\partial x} \\
\varepsilon_y &= \frac{\partial v}{\partial y} \\
\gamma_{xy} &= \frac{1}{2}\left(\frac{\partial u}{\partial y} + \frac{\partial v}{\partial x}\right)
\end{aligned}
$$

Von Mises 应变（用于塑性变形表征）：

$$
\varepsilon_{\text{VM}} = \sqrt{\varepsilon_x^2 + \varepsilon_y^2 - \varepsilon_x \varepsilon_y + 3\gamma_{xy}^2}
$$

### 5.3 可视化

- **云图（Contour）**: 位移/应变/相关系数叠加在变形图像上
- **截线图（Cut Line）**: 沿 X 或 Y 方向的剖面线图
- 所有绘图使用 Matplotlib，支持透明叠加和保存到文件

---

## 6. GUI 界面

基于 **PyQt6** 的五步工作流：

| 步骤 | 面板 | 功能 |
|------|------|------|
| 1 | **Settings** | 导入/导出/编辑 `settings.ini` |
| 2 | **Image Set** | 加载图像文件夹、预览 |
| 3 | **ROI** | 在参考图像上定义感兴趣区域 |
| 4 | **Analysis** | 运行 DIC 分析，实时进度显示 |
| 5 | **Results** | 交互式位移/应变/相关系数云图查看 |

包含自定义图标、Fusion 风格统一外观、Figtree 字体。

---

## 7. API 使用示例

### 运行分析

```python
from sundic.settings import Settings
from sundic import sundic

# 加载设置
settings = Settings.fromSettingsFile('settings.ini')

# 运行 2D 平面 DIC
returnData = sundic.planarDICLocal(settings, 'results.bin')
```

### 获取位移

```python
from sundic import post_process as pp

disp, nRows, nCols = pp.getDisplacements(
    'results.bin', imgPair=-1, smoothWindow=0)

# disp 列: [x, y, z, u, v, z_disp, u_mag]
# 使用 -1 获取最后一对图像的结果
```

### 获取应变

```python
strains, nRows, nCols = pp.getStrains(
    'results.bin', imgPair=-1, smoothWindow=9, smoothOrder=2)

# strains 列: [x, y, z, εx, εy, γxy, εVM]
```

### 绘图

```python
# 位移云图
pp.plotDispContour('results.bin', imgPair=-1, 
                   dispComp=pp.DispComp.DISP_MAG, 
                   plotImage=True, showPlot=True)

# 应变云图
pp.plotStrainContour('results.bin', imgPair=-1,
                     strainComp=pp.StrainComp.VM_STRAIN,
                     plotImage=True, showPlot=True)

# 截线图
pp.plotDispCutLine('results.bin', imgPair=-1,
                   cutValues=[100, 200], cutComp=pp.CompID.YCoordID)
```

---

## 8. 关键可配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `SubSetSize` | 33 | 子区大小（必须为奇数） |
| `StepSize` | 5 | 子区间距（像素） |
| `ShapeFunctions` | `Affine` | 形状函数：`Affine` 或 `Quadratic` |
| `ReferenceStrategy` | `Relative` | 参考策略：`Relative` 或 `Absolute` |
| `OptimizationAlgorithm` | `IC-GN` | 优化器：`IC-GN` / `IC-LM` / `Fast-IC-LM` |
| `MaxIterations` | 50 | 每子区最大迭代次数 |
| `ConvergenceThreshold` | 0.0001 | 位移收敛容差 |
| `NZCCThreshold` | 0.999 | ZNCC 收敛阈值 |
| `InterpolationOrder` | 5 | 亚像素插值阶数（3 或 5） |
| `StartingPoints` | 4 | AKAZE 种子点数量 |
| `GaussianBlurSize` | 5 | 高斯模糊核尺寸 |
| `CPUCount` | 1 | 并行 CPU 数量（也可设为 `auto`） |
| `ROI` | `[0, 0, 0, 0]` | ROI（0 表示全图） |
| `MaskFile` | `""` | 黑白掩码文件路径 |

---

## 9. 数据存储

分析结果以 **MsgPack** 二进制格式存储（`results.bin`），包含：
- 程序版本号和时间戳
- Settings 对象的完整序列化
- 每个图像对的子区数据（中心坐标、模型系数、$C_{\text{ZNSSD}}$）

---

## 10. 已知限制

- 仅支持 **2D 平面 DIC**（3D/立体 DIC 正在开发中）
- Windows 上过新的 Python 版本可能导致 `ray` 安装问题

---

## 11. 致谢与引用

- **核心分析代码**: 基于 Ed Brisley 的 MEng 学位论文 (斯泰伦博斯大学)
- **快速插值器**: David Stein 的 `fast_interp` (Apache 2.0)
- **平滑算法**: SciPy Cookbook 的 2D Savitzky-Golay 实现
- **GUI 开发**: Elijah Stockhall
- **图形设计**: Dr. Melody Neaves

如用于学术研究，请引用：

> Venter, G. and Neaves, M., *SUN-DIC: A Python-Based Open-Source Software Tool for Digital Image Correlation*, Advances in Engineering Software, Volume 211, 2025.

---

*本文档由代码分析生成，日期：2025-06-25*
