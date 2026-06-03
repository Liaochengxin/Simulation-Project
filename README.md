# Geant4 放疗模拟项目

本项目用于完成 Geant4 放疗模拟作业的第一问：比较 `gamma` 和 `proton` 射线在癌症区域与正常组织区域中的能量沉积、LET、空间演化和治疗选择性。

## 当前模型

几何模型是一个简化人体 phantom：

- `Torso`：躯干，软组织材料
- `Head`：头部，软组织材料
- `Neck`：颈部，软组织材料
- `LegL` / `LegR`：双腿，软组织材料
- `Tumor`：肿瘤区域，位于躯干内部

统计时区域被分为：

- `Cancer`：`Tumor`
- `Normal`：`Torso`、`Head`、`Neck`、`LegL`、`LegR`

## 束流设置

当前质子束从人体右侧，即 `+X` 方向入射：

```text
/gps/pos/centre 160 0 0 mm
/gps/direction -1 0 0
```

质子能量设置为：

```text
90 MeV
```

该能量使质子 Bragg peak 落在肿瘤深度附近。当前分析脚本使用的肿瘤深度区间为：

```text
80 mm - 100 mm
```

## 编译和运行

推荐直接运行：

```bash
scripts/run_first_question.sh
```

脚本会自动：

1. 配置 CMake
2. 编译 `BNCT_Simulation`
3. 运行 `run_gamma.mac`
4. 运行 `run_proton.mac`

生成的 CSV 位于：

```text
build/gamma_results_nt_DoseData.csv
build/proton_results_nt_DoseData.csv
```

CSV 是标准格式，第一行是列名，没有 Geant4 默认的 `#column` 元数据头。

## CSV 列说明

主要输出列包括：

```text
Region
VolumeName
ParticleName
IncidentParticle
EnergyDeposit_MeV
StepLength_mm
LET_MeV_per_mm
Dose_Gy
X_mm
Y_mm
Z_mm
Depth_mm
EventID
TrackID
ParentID
PDGEncoding
```

注意：`Dose_Gy` 是 step contribution 的记录量，不作为主要物理结论依据。主要分析使用 `EnergyDeposit_MeV` 重新计算深度剂量和区域平均剂量。

## 画图和分析

运行：

```bash
python3 scripts/plot_first_question.py
```

输出保存到：

```text
figures/
```

当前生成：

```text
figures/edep_spectra.png
figures/let_spectra.png
figures/depth_dose_curve.png
figures/depth_let_curve.png
figures/region_dose_summary.png
figures/spatial_dose_evolution.gif
figures/summary_results.csv
```

其中：

- `edep_spectra.png`：每个 step 的能量沉积谱
- `let_spectra.png`：LET 谱
- `depth_dose_curve.png`：随深度变化的剂量曲线
- `depth_let_curve.png`：随深度变化的 LET 曲线
- `region_dose_summary.png`：癌区/正常区平均剂量和选择性比值
- `spatial_dose_evolution.gif`：束流截面上的剂量随深度演化
- `summary_results.csv`：gamma/proton 的区域总能量沉积、重算剂量和 Cancer/Normal 比值

## 可视化

交互式 Geant4 可视化：

```bash
cd build
./BNCT_Simulation
```

当前 `vis.mac` 会显示人体几何、肿瘤位置和少量质子轨迹。

## Git 忽略规则

`.gitignore` 会忽略：

- `build/`
- `figures/`
- 运行生成的 CSV、ROOT、HDF5 文件
- Python cache
- macOS / 编辑器临时文件

因此 GitHub 上主要保存源码、宏文件和分析脚本；模拟结果可以通过脚本重新生成。

