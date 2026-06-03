#!/usr/bin/env python3
import argparse
import csv
import io
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib-cache")

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
from PIL import Image


# Adjustable physics / geometry assumptions for derived dose quantities.
density_g_cm3 = 1.0
beam_area_mm2 = 100.0
depth_bin_width_mm = 1.0
gif_depth_step_mm = 2.0
transverse_bin_width_mm = 1.0
beam_half_width_mm = 10.0
tumor_depth_min_mm = 80.0
tumor_depth_max_mm = 100.0

mass_cancer_kg = 6.0e-7
mass_normal_kg = 15.6
MeV_to_J = 1.602176634e-13

STRING_COLUMNS = {"Region", "VolumeName", "ParticleName", "IncidentParticle"}
INT_COLUMNS = {"EventID", "TrackID", "ParentID", "PDGEncoding"}


def read_geant_csv(path):
    with path.open(newline="") as handle:
        first_line = handle.readline()

    if first_line.startswith("#"):
        return read_legacy_geant_csv(path)

    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = reader.fieldnames or []

    data = {name: [] for name in columns}
    for row in rows:
        for name in columns:
            data[name].append(row.get(name, ""))
    return convert_columns(data, columns)


def read_legacy_geant_csv(path):
    columns = []
    rows = []
    with path.open(newline="") as handle:
        for line in handle:
            if line.startswith("#column"):
                columns.append(line.strip().split()[-1])
            elif line.strip() and not line.startswith("#"):
                rows.append(next(csv.reader([line])))

    data = {name: [] for name in columns}
    for row in rows:
        for name, value in zip(columns, row):
            data[name].append(value)
    return convert_columns(data, columns)


def convert_columns(data, columns):
    converted = {}
    for name in columns:
        values = data[name]
        if name in STRING_COLUMNS:
            converted[name] = np.array(values, dtype=str)
        elif name in INT_COLUMNS:
            converted[name] = np.array([safe_int(value) for value in values], dtype=int)
        else:
            converted[name] = np.array([safe_float(value) for value in values], dtype=float)
    return converted


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def concatenate(datasets):
    keys = datasets[0].keys()
    return {key: np.concatenate([data[key] for data in datasets]) for key in keys}


def base_filter(data):
    required = ["EnergyDeposit_MeV", "StepLength_mm", "LET_MeV_per_mm", "Depth_mm"]
    mask = np.ones(len(data["EnergyDeposit_MeV"]), dtype=bool)
    for name in required:
        mask &= np.isfinite(data[name])
    mask &= data["EnergyDeposit_MeV"] > 0
    mask &= data["StepLength_mm"] > 0
    mask &= data["LET_MeV_per_mm"] > 0
    return mask


def subset(data, mask):
    return {key: values[mask] for key, values in data.items()}


def positive_log_bins(values, n_bins=100):
    values = values[np.isfinite(values) & (values > 0)]
    if values.size == 0:
        return np.logspace(-12, 0, n_bins)
    vmin = max(values.min(), np.finfo(float).tiny)
    vmax = values.max()
    if np.isclose(vmin, vmax):
        vmin *= 0.8
        vmax *= 1.2
    return np.logspace(np.log10(vmin), np.log10(vmax), n_bins)


def plot_spectrum(data, field, xlabel, output_path, title):
    bins = positive_log_bins(data[field], 120)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)

    for ax, region in zip(axes, ["Cancer", "Normal"]):
        for particle, color in [("gamma", "tab:blue"), ("proton", "tab:red")]:
            mask = (data["Region"] == region) & (data["IncidentParticle"] == particle)
            values = data[field][mask]
            values = values[np.isfinite(values) & (values > 0)]
            if values.size == 0:
                continue
            ax.hist(values, bins=bins, histtype="step", density=True,
                    linewidth=1.6, label=particle, color=color)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("normalized counts")
        ax.set_title(region)
        ax.grid(True, which="both", alpha=0.25)
        ax.legend()

    fig.suptitle(title)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_depth_dose_curve(data, output_path):
    depth = data["Depth_mm"]
    max_depth = max(np.nanmax(depth), tumor_depth_max_mm + 40.0)
    bins = np.arange(0, max_depth + depth_bin_width_mm, depth_bin_width_mm)
    if bins.size < 2:
        bins = np.array([0.0, depth_bin_width_mm])

    bin_volume_mm3 = beam_area_mm2 * depth_bin_width_mm
    bin_volume_cm3 = bin_volume_mm3 * 1e-3
    mass_bin_kg = density_g_cm3 * bin_volume_cm3 * 1e-3

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), constrained_layout=True)
    for ax, (particle, color) in zip(axes, [("gamma", "tab:blue"), ("proton", "tab:red")]):
        mask = data["IncidentParticle"] == particle
        edep_sum, edges = np.histogram(depth[mask], bins=bins,
                                       weights=data["EnergyDeposit_MeV"][mask])
        dose = edep_sum * MeV_to_J / mass_bin_kg
        centers = 0.5 * (edges[:-1] + edges[1:])
        ax.plot(centers, dose, color=color, linewidth=1.8, label=particle)
        ax.axvspan(tumor_depth_min_mm, tumor_depth_max_mm, alpha=0.18,
                   color="tab:red", label="tumor depth")
        ax.set_xlabel("Depth_mm")
        ax.set_ylabel("Dose per depth bin (Gy)")
        ax.set_title(particle)
        ax.grid(True, which="both", alpha=0.25)
        ax.legend()

    axes[1].yaxis.set_label_position("right")
    axes[1].yaxis.tick_right()
    fig.suptitle("Depth-dose curve from summed energy deposition")
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_depth_let_curve(data, output_path):
    depth = data["Depth_mm"]
    max_depth = max(np.nanmax(depth), tumor_depth_max_mm + 40.0)
    bins = np.arange(0, max_depth + depth_bin_width_mm, depth_bin_width_mm)
    if bins.size < 2:
        bins = np.array([0.0, depth_bin_width_mm])

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), constrained_layout=True)
    for ax, (particle, color) in zip(axes, [("gamma", "tab:blue"), ("proton", "tab:red")]):
        mask = data["IncidentParticle"] == particle
        let_sum, edges = np.histogram(depth[mask], bins=bins,
                                      weights=data["LET_MeV_per_mm"][mask])
        counts, _ = np.histogram(depth[mask], bins=bins)
        mean_let = np.divide(let_sum, counts, out=np.zeros_like(let_sum), where=counts > 0)
        centers = 0.5 * (edges[:-1] + edges[1:])

        ax.plot(centers, mean_let, color=color, linewidth=1.8, label=particle)
        ax.axvspan(tumor_depth_min_mm, tumor_depth_max_mm, alpha=0.18,
                   color="tab:red", label="tumor depth")
        ax.set_xlabel("Depth_mm")
        ax.set_ylabel("Mean LET per depth bin (MeV/mm)")
        ax.set_title(particle)
        ax.grid(True, alpha=0.25)
        ax.legend()

    axes[1].yaxis.set_label_position("right")
    axes[1].yaxis.tick_right()
    fig.suptitle("Depth-LET curve")
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_spatial_dose_evolution_gif(data, output_path):
    if "Y_mm" not in data or "Z_mm" not in data:
        print("Skipping spatial dose GIF: Y_mm or Z_mm is missing.")
        return

    spatial_mask = (
        np.isfinite(data["Y_mm"]) &
        np.isfinite(data["Z_mm"]) &
        np.isfinite(data["Depth_mm"])
    )
    spatial = subset(data, spatial_mask)
    if len(spatial["Depth_mm"]) == 0:
        print("Skipping spatial dose GIF: no rows with finite Y_mm/Z_mm/Depth_mm.")
        return

    max_depth = max(np.nanmax(spatial["Depth_mm"]), tumor_depth_max_mm + 40.0)
    depth_starts = np.arange(0.0, max_depth + gif_depth_step_mm, gif_depth_step_mm)

    y_edges = np.arange(-beam_half_width_mm, beam_half_width_mm + transverse_bin_width_mm,
                        transverse_bin_width_mm)
    z_edges = np.arange(-beam_half_width_mm, beam_half_width_mm + transverse_bin_width_mm,
                        transverse_bin_width_mm)

    voxel_volume_mm3 = transverse_bin_width_mm * transverse_bin_width_mm * gif_depth_step_mm
    voxel_volume_cm3 = voxel_volume_mm3 * 1e-3
    voxel_mass_kg = density_g_cm3 * voxel_volume_cm3 * 1e-3

    frame_maps = []
    positive_values = []
    for depth_start in depth_starts:
        depth_stop = depth_start + gif_depth_step_mm
        maps = []
        for particle in ["gamma", "proton"]:
            mask = (
                (spatial["IncidentParticle"] == particle) &
                (spatial["Depth_mm"] >= depth_start) &
                (spatial["Depth_mm"] < depth_stop)
            )
            edep_sum, _, _ = np.histogram2d(
                spatial["Y_mm"][mask],
                spatial["Z_mm"][mask],
                bins=[y_edges, z_edges],
                weights=spatial["EnergyDeposit_MeV"][mask],
            )
            dose = edep_sum * MeV_to_J / voxel_mass_kg
            maps.append(dose.T)
            positive_values.extend(dose[dose > 0])
        frame_maps.append((depth_start, depth_stop, maps))

    if len(positive_values) == 0:
        print("Skipping spatial dose GIF: no positive dose in 2D bins.")
        return

    norm = LogNorm(vmin=np.nanmin(positive_values), vmax=np.nanmax(positive_values))
    frames = []
    for depth_start, depth_stop, maps in frame_maps:
        fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8), constrained_layout=True)
        last_mesh = None
        in_tumor_depth = depth_start < tumor_depth_max_mm and depth_stop > tumor_depth_min_mm

        for ax, particle, dose_map in zip(axes, ["gamma", "proton"], maps):
            masked = np.ma.masked_where(dose_map <= 0, dose_map)
            last_mesh = ax.pcolormesh(y_edges, z_edges, masked, norm=norm, shading="auto")
            if in_tumor_depth:
                tumor_rect = plt.Rectangle((-5.0, -15.0), 10.0, 30.0,
                                           fill=False, edgecolor="red", linewidth=1.4)
                ax.add_patch(tumor_rect)
            ax.set_xlabel("Y_mm")
            ax.set_ylabel("Z_mm")
            ax.set_title(particle)
            ax.set_xlim(-beam_half_width_mm, beam_half_width_mm)
            ax.set_ylim(-beam_half_width_mm, beam_half_width_mm)
            ax.set_aspect("equal", adjustable="box")
            ax.grid(False)

        fig.suptitle(f"Cross-section dose evolution: depth {depth_start:.0f}-{depth_stop:.0f} mm")
        fig.colorbar(last_mesh, ax=axes, label="Dose per voxel (Gy)")

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=120)
        plt.close(fig)
        buffer.seek(0)
        frames.append(Image.open(buffer).convert("P", palette=Image.ADAPTIVE))

    frames[0].save(output_path, save_all=True, append_images=frames[1:],
                   duration=120, loop=0, optimize=True)


def region_summary(data):
    rows = []
    for particle in ["gamma", "proton"]:
        particle_mask = data["IncidentParticle"] == particle
        cancer_mask = particle_mask & (data["Region"] == "Cancer")
        normal_mask = particle_mask & (data["Region"] == "Normal")
        edep_cancer = float(np.sum(data["EnergyDeposit_MeV"][cancer_mask]))
        edep_normal = float(np.sum(data["EnergyDeposit_MeV"][normal_mask]))
        dose_cancer = edep_cancer * MeV_to_J / mass_cancer_kg
        dose_normal = edep_normal * MeV_to_J / mass_normal_kg
        ratio = dose_cancer / dose_normal if dose_normal > 0 else np.nan
        rows.append({
            "IncidentParticle": particle,
            "Edep_Cancer_MeV": edep_cancer,
            "Edep_Normal_MeV": edep_normal,
            "Dose_Cancer_Gy": dose_cancer,
            "Dose_Normal_Gy": dose_normal,
            "Cancer_Normal_Dose_Ratio": ratio,
        })
    return rows


def plot_region_dose_summary(rows, output_path):
    particles = [row["IncidentParticle"] for row in rows]
    cancer_dose = [row["Dose_Cancer_Gy"] for row in rows]
    normal_dose = [row["Dose_Normal_Gy"] for row in rows]
    ratios = [row["Cancer_Normal_Dose_Ratio"] for row in rows]

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6), constrained_layout=True)
    x = np.arange(len(particles))
    width = 0.35

    axes[0].bar(x - width / 2, cancer_dose, width, label="Cancer", color="tab:red")
    axes[0].bar(x + width / 2, normal_dose, width, label="Normal", color="tab:blue")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(particles)
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Region-averaged dose (Gy)")
    axes[0].set_title("Dose by region")
    axes[0].legend()
    axes[0].grid(True, axis="y", which="both", alpha=0.25)

    axes[1].bar(particles, ratios, color=["tab:blue", "tab:red"])
    axes[1].set_yscale("log")
    axes[1].set_ylabel("Cancer / Normal dose ratio")
    axes[1].set_title("Treatment selectivity")
    axes[1].grid(True, axis="y", which="both", alpha=0.25)

    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def write_summary(rows, output_path):
    columns = [
        "IncidentParticle",
        "Edep_Cancer_MeV",
        "Edep_Normal_MeV",
        "Dose_Cancer_Gy",
        "Dose_Normal_Gy",
        "Cancer_Normal_Dose_Ratio",
    ]
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows):
    columns = [
        "IncidentParticle",
        "Edep_Cancer_MeV",
        "Edep_Normal_MeV",
        "Dose_Cancer_Gy",
        "Dose_Normal_Gy",
        "Cancer_Normal_Dose_Ratio",
    ]
    print(",".join(columns))
    for row in rows:
        print(",".join([
            row["IncidentParticle"],
            f"{row['Edep_Cancer_MeV']:.6g}",
            f"{row['Edep_Normal_MeV']:.6g}",
            f"{row['Dose_Cancer_Gy']:.6g}",
            f"{row['Dose_Normal_Gy']:.6g}",
            f"{row['Cancer_Normal_Dose_Ratio']:.6g}",
        ]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", default="build")
    parser.add_argument("--out-dir", default="figures")
    args = parser.parse_args()

    build_dir = Path(args.build_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    gamma = read_geant_csv(build_dir / "gamma_results_nt_DoseData.csv")
    proton = read_geant_csv(build_dir / "proton_results_nt_DoseData.csv")
    data = concatenate([gamma, proton])
    data = subset(data, base_filter(data))

    plot_spectrum(data, "EnergyDeposit_MeV", "EnergyDeposit_MeV",
                  out_dir / "edep_spectra.png",
                  "Energy deposit spectrum")
    plot_spectrum(data, "LET_MeV_per_mm", "LET_MeV_per_mm",
                  out_dir / "let_spectra.png",
                  "LET spectra")
    plot_depth_dose_curve(data, out_dir / "depth_dose_curve.png")
    plot_depth_let_curve(data, out_dir / "depth_let_curve.png")
    plot_spatial_dose_evolution_gif(data, out_dir / "spatial_dose_evolution.gif")

    rows = region_summary(data)
    plot_region_dose_summary(rows, out_dir / "region_dose_summary.png")
    write_summary(rows, out_dir / "summary_results.csv")
    print_summary(rows)


if __name__ == "__main__":
    main()
