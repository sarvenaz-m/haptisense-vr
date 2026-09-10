"""Generate a shareable numerical figure; requires optional matplotlib."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from haptisense.research import ResearchConfig, run_research


def main():
    destination = Path(__file__).resolve().parents[1] / "results" / "v0.3"
    destination.mkdir(exist_ok=True, parents=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.3))
    palette = {"elastic": "#7c66b2", "kelvin": "#ba812e", "sls": "#087f74"}
    labels = {"elastic": "Nonlinear elastic", "kelvin": "Kelvin: approach damping", "sls": "SLS memory branch"}
    for model in ("elastic", "kelvin", "sls"):
        result = run_research(ResearchConfig(model=model))
        rows = result["rows"]
        axes[0].plot([r["t_s"] for r in rows], [r["normal_n"] for r in rows],
                     color=palette[model], label=labels[model], linewidth=2)
        axes[1].plot([r["depth_m"]*1000 for r in rows], [r["normal_n"] for r in rows],
                     color=palette[model], linewidth=2)
    axes[0].axvspan(1.2, 2.6, color="#087f74", alpha=.06)
    axes[0].text(1.9, 6.7, "Stationary hold", ha="center", color="#37645f", fontsize=9)
    axes[0].set(xlabel="Model time [s]", ylabel="Raw normal force [N]", title="01 / Response to identical motion", ylim=(-.15, 7.1))
    axes[1].set(xlabel="Penetration [mm]", ylabel="Raw normal force [N]", title="02 / Loading and unloading", ylim=(-.15, 7.1))
    for ax in axes:
        ax.grid(alpha=.15)
        ax.title.set_fontsize(12)
        ax.title.set_weight("semibold")
    axes[0].legend(loc="lower center", bbox_to_anchor=(1.1, -.38), ncol=3, frameon=False)
    fig.suptitle("HaptiSense VR 0.3 | Controlled contact experiment", x=.065, y=.98, ha="left", fontsize=17, weight="bold", color="#19363d")
    fig.text(.065, .905, "Same 6 mm indentation, 35 mm/s scan speed and 2 ms model step. Only the contact law changes.", color="#53666b", fontsize=10)
    fig.text(.065, .018, "Synthetic computational output. Illustrative parameters; no measured tissue, device or participant data.", color="#53666b", fontsize=9)
    fig.subplots_adjust(top=.8, bottom=.26, left=.065, right=.98, wspace=.22)
    fig.savefig(destination / "model_comparison.png", dpi=160, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
