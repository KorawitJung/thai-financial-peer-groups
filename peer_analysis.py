"""Group companies by financial profile, flag unusual ones, and export PNGs plus an HTML dashboard."""

from __future__ import annotations

import argparse
import base64
import html
import webbrowser
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Writes files without needing a display.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import RobustScaler

SEED = 42
MIN_COMPANIES = 8
MAX_CLUSTERS = 3
FEATURES = {
    "roe": "ROE",
    "roa": "ROA",
    "equity_to_assets": "Equity / assets",
    "credit_cost": "Credit cost / assets",
    "asset_cagr": "Asset growth (CAGR)",
    "roa_volatility": "ROA volatility",
}
PERCENT_FEATURES = list(FEATURES)
SECTORS = {"BANK": "Banks", "FIN": "Other financials", "INSUR": "Insurance"}
SECTOR_MARKERS = {"BANK": "o", "FIN": "s", "INSUR": "^"}
# Only three colors pass the color-blind check together, so the model stops at three clusters.
CLUSTER_COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]
INK = "#0b0b0b"
MUTED = "#6f6d68"
SURFACE = "#fcfcfb"
GRID = "#e6e5e0"


def load_panel(csv_path: str | Path) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def build_features(panel: pd.DataFrame) -> pd.DataFrame:
    """Reduce each company's five years to one row of profile measures."""

    def summarize(company: pd.DataFrame) -> pd.Series:
        company = company.sort_values("fiscal_year")
        assets = company["total_assets"].to_numpy(dtype=float)
        years = company["fiscal_year"].iloc[-1] - company["fiscal_year"].iloc[0]
        return pd.Series(
            {
                "sector": company["sector"].iloc[0],
                "roe": company["roe"].median(),
                "roa": company["roa"].median(),
                "equity_to_assets": company["equity_to_assets"].median(),
                "credit_cost": company["credit_cost"].median(),
                "asset_cagr": (assets[-1] / assets[0]) ** (1 / years) - 1,
                "roa_volatility": company["roa"].std(),
            }
        )

    rows = [summarize(group).rename(ticker) for ticker, group in panel.groupby("ticker")]
    features = pd.DataFrame(rows)
    features.index.name = "ticker"
    features[list(FEATURES)] = features[list(FEATURES)].astype(float)
    return features


def scale_features(features: pd.DataFrame) -> np.ndarray:
    """Fill gaps, cap extremes at the 5th and 95th percentiles, and scale robustly."""
    values = SimpleImputer(strategy="median").fit_transform(features[list(FEATURES)])
    low, high = np.percentile(values, [5, 95], axis=0)
    return RobustScaler().fit_transform(np.clip(values, low, high))


def choose_k(scaled: np.ndarray, candidates: range = range(2, 4)) -> pd.DataFrame:
    """Score each cluster count on separation and on stability under bootstrap resampling."""
    rng = np.random.default_rng(SEED)
    rows = []
    for k in candidates:
        base = KMeans(n_clusters=k, n_init=20, random_state=SEED).fit(scaled)
        agreement = []
        for _ in range(100):
            sample = scaled[rng.integers(0, len(scaled), len(scaled))]
            if len(np.unique(sample, axis=0)) < k:
                continue
            model = KMeans(n_clusters=k, n_init=5, random_state=SEED).fit(sample)
            agreement.append(adjusted_rand_score(base.labels_, model.predict(scaled)))
        rows.append(
            {
                "k": k,
                "silhouette": silhouette_score(scaled, base.labels_),
                "stability": float(np.mean(agreement)),
            }
        )
    return pd.DataFrame(rows)


def analyze(features: pd.DataFrame) -> dict:
    if len(features) < MIN_COMPANIES:
        raise ValueError(f"Need at least {MIN_COMPANIES} companies, found {len(features)}.")
    scaled = scale_features(features)
    scores = choose_k(scaled, range(2, 6))
    # Three is the limit: higher counts leave groups too small to describe.
    usable = scores[scores["k"] <= MAX_CLUSTERS]
    k = int(usable.loc[usable["silhouette"].idxmax(), "k"])
    model = KMeans(n_clusters=k, n_init=50, random_state=SEED).fit(scaled)

    # Name clusters by size so a rerun gives the same letter to the same group.
    order = pd.Series(model.labels_).value_counts().index.tolist()
    letters = {label: "ABC"[i] for i, label in enumerate(order)}

    pca = PCA(n_components=2, random_state=SEED)
    coords = pca.fit_transform(scaled)
    forest = IsolationForest(n_estimators=500, contamination=0.1, random_state=SEED).fit(scaled)

    result = features.copy()
    result["cluster"] = [letters[label] for label in model.labels_]
    result["pc1"], result["pc2"] = coords[:, 0], coords[:, 1]
    result["unusualness"] = -forest.score_samples(scaled)
    result["is_unusual"] = forest.predict(scaled) == -1
    names = list(FEATURES.values())
    result["most_distinct"] = [names[i] for i in np.abs(scaled).argmax(axis=1)]
    return {
        "table": result.sort_values(["cluster", "roa"], ascending=[True, False]),
        "scaled": pd.DataFrame(scaled, index=features.index, columns=names),
        "scores": scores,
        "k": k,
        "sector_agreement": adjusted_rand_score(result["sector"], result["cluster"]),
        "pca_share": pca.explained_variance_ratio_,
        "imputed": int(features[list(FEATURES)].isna().sum().sum()),
    }


def describe_clusters(table: pd.DataFrame) -> pd.DataFrame:
    """Describe each cluster by what separates it from all companies, using medians."""
    columns = list(FEATURES)
    overall = table[columns].median()
    spread = (table[columns].quantile(0.75) - table[columns].quantile(0.25)).replace(0, np.nan)
    rows = []
    for letter, group in table.groupby("cluster"):
        gaps = ((group[columns].median() - overall) / spread).dropna()
        top = gaps.reindex(gaps.abs().sort_values(ascending=False).index).head(2)
        traits = [f"{'higher' if v > 0 else 'lower'} {FEATURES[c]}" for c, v in top.items()]
        mix = group["sector"].map(SECTORS).value_counts()
        rows.append(
            {
                "cluster": letter,
                "companies": len(group),
                "traits": " and ".join(traits).replace("higher", "Higher", 1).replace("lower", "Lower", 1),
                "members": ", ".join(group.index),
                "sector_mix": ", ".join(f"{name} {n}" for name, n in mix.items()),
                **group[columns].median().to_dict(),
            }
        )
    return pd.DataFrame(rows)


def _style() -> None:
    sns.set_theme(
        style="white",
        rc={
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "text.color": INK,
            "axes.labelcolor": MUTED,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "font.family": "DejaVu Sans",
        },
    )


def _title(fig, title: str, subtitle: str) -> None:
    fig.text(0.04, 0.965, title, fontsize=19, fontweight="bold", va="top")
    fig.text(0.04, 0.915, subtitle, fontsize=11.5, color=MUTED, va="top")
    fig.text(0.04, 0.018, "27 selected Thai financial companies, 2021-2025. Not investment advice.",
             fontsize=9, color=MUTED)


def _save(fig, path: Path) -> Path:
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def spread_labels(points: np.ndarray, gap: tuple[float, float] = (0.62, 0.17)) -> np.ndarray:
    """Push label positions apart with NumPy so tickers in dense areas stay readable."""
    labels = points + np.array([0.0, 0.14])
    size = np.array(gap)
    for _ in range(600):
        for i in range(len(labels)):
            delta = labels[i] - np.delete(labels, i, axis=0)
            overlap = np.all(np.abs(delta) < size, axis=1)
            dots = labels[i] - points
            dots[i] = 1.0  # A label may sit near its own point.
            near_dot = np.all(np.abs(dots) < size * 0.6, axis=1)
            if overlap.any():
                push = delta[overlap].mean(axis=0) + np.array([0.01 * (i % 3 - 1), 0.01])
                labels[i] += 0.12 * push / (np.linalg.norm(push) + 1e-9)
            if near_dot.any():
                push = dots[near_dot].mean(axis=0) + np.array([0.0, 0.01])
                labels[i] += 0.06 * push / (np.linalg.norm(push) + 1e-9)
    return labels


def plot_map(result: dict, path: Path) -> Path:
    table = result["table"]
    fig, ax = plt.subplots(figsize=(8, 8))
    fig.subplots_adjust(left=0.08, right=0.96, top=0.84, bottom=0.11)
    for i, letter in enumerate(sorted(table["cluster"].unique())):
        for sector, marker in SECTOR_MARKERS.items():
            rows = table[(table["cluster"] == letter) & (table["sector"] == sector)]
            ax.scatter(rows["pc1"], rows["pc2"], s=80, marker=marker, color=CLUSTER_COLORS[i],
                       edgecolor=SURFACE, linewidth=1.5, zorder=3)
    points = table[["pc1", "pc2"]].to_numpy()
    for ticker, point, label in zip(table.index, points, spread_labels(points), strict=True):
        ax.annotate(ticker, point, xytext=label, textcoords="data", fontsize=8.5, color=INK,
                    ha="center", va="center",
                    arrowprops={"arrowstyle": "-", "color": "#b5b3ac", "linewidth": 0.7,
                                "shrinkA": 0, "shrinkB": 4})
    ax.grid(color=GRID, linewidth=0.8)
    sns.despine(ax=ax, left=True, bottom=True)
    share = result["pca_share"]
    ax.set_xlabel(f"Profile axis 1 ({share[0]:.0%} of variation)")
    ax.set_ylabel(f"Profile axis 2 ({share[1]:.0%} of variation)")
    handles = [plt.Line2D([], [], marker="o", ls="", color=CLUSTER_COLORS[i], label=f"Cluster {c}")
               for i, c in enumerate(sorted(table["cluster"].unique()))]
    handles += [plt.Line2D([], [], marker=m, ls="", color=MUTED, label=SECTORS[s])
                for s, m in SECTOR_MARKERS.items()]
    ax.legend(handles=handles, frameon=False, ncol=4, loc="upper center",
              bbox_to_anchor=(0.5, 1.07), fontsize=9.5, handletextpad=0.2, columnspacing=1)
    _title(fig, "Financial profiles cross sector lines" if result["sector_agreement"] < 0.5
           else "Financial profiles mostly follow sector lines",
           f"Closer companies have more similar statements. Agreement with sector: "
           f"{result['sector_agreement']:.2f} (1 = identical).")
    return _save(fig, path)


def plot_heatmap(result: dict, path: Path) -> Path:
    table = result["table"]
    data = result["scaled"].loc[table.index]
    fig, ax = plt.subplots(figsize=(8, 10))
    fig.subplots_adjust(left=0.13, right=0.98, top=0.87, bottom=0.14)
    sns.heatmap(data, cmap=sns.diverging_palette(35, 250, s=80, l=55, as_cmap=True), center=0,
                vmin=-2.5, vmax=2.5, linewidths=1.5, linecolor=SURFACE, ax=ax,
                cbar_kws={"label": "Below typical  <->  above typical", "shrink": 0.5})
    ax.set_yticklabels(
        [f"{c} · {t}" for c, t in zip(table["cluster"], table.index, strict=True)],
        rotation=0, fontsize=9,
    )
    ax.set_ylabel("")
    ax.tick_params(axis="x", labelrotation=30, labelsize=9.5, length=0)
    ax.tick_params(axis="y", length=0)
    _title(fig, "What makes each company different",
           "Each measure is scaled, so color shows distance from the typical company.")
    return _save(fig, path)


def plot_model_check(result: dict, path: Path) -> Path:
    scores = result["scores"]
    fig, axes = plt.subplots(1, 2, figsize=(9, 5.6), sharex=True)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.73, bottom=0.2, wspace=0.25)
    for ax, column, name in zip(
        axes, ["silhouette", "stability"], ["Separation (silhouette)", "Stability (bootstrap)"],
        strict=True,
    ):
        ax.plot(scores["k"], scores[column], color=MUTED, linewidth=2)
        ax.scatter(scores["k"], scores[column], color=MUTED, s=60, zorder=3)
        chosen = scores[scores["k"] == result["k"]]
        ax.scatter(chosen["k"], chosen[column], color=CLUSTER_COLORS[0], s=110, zorder=4)
        ax.set_title(name, fontsize=11.5, loc="left")
        ax.set_xlabel("Number of clusters")
        ax.set_xticks(scores["k"])
        ax.set_ylim(0, 1)
        ax.grid(axis="y", color=GRID)
        sns.despine(ax=ax, left=True)
    chosen = scores[scores["k"] == result["k"]].iloc[0]
    _title(fig, f"Why {result['k']} clusters",
           f"Separation {chosen['silhouette']:.2f} and stability {chosen['stability']:.2f}. "
           f"Capped at {MAX_CLUSTERS}, as more clusters leave very small groups.")
    return _save(fig, path)


def plot_unusual(result: dict, path: Path) -> Path:
    table = result["table"].sort_values("unusualness", ascending=False)
    colors = [CLUSTER_COLORS[1] if flag else "#c9c7c0" for flag in table["is_unusual"]]
    fig, ax = plt.subplots(figsize=(8, 9.5))
    fig.subplots_adjust(left=0.12, right=0.95, top=0.86, bottom=0.1)
    sns.barplot(x=table["unusualness"], y=table.index, hue=table.index, palette=colors,
                legend=False, ax=ax, width=0.6)
    ax.set_xlim(left=0)
    ax.set_xlabel("Unusualness score")
    ax.set_ylabel("")
    ax.tick_params(axis="y", labelsize=9, length=0)
    ax.grid(axis="x", color=GRID)
    ax.set_axisbelow(True)
    sns.despine(ax=ax, left=True, bottom=True)
    flagged = ", ".join(table.index[table["is_unusual"]])
    _title(fig, "Companies least like the others",
           f"Orange: {flagged}. Unusual means different, not good or bad.")
    return _save(fig, path)


def _percent_table(frame: pd.DataFrame, percent_columns: list[str]) -> str:
    view = frame.copy()
    for column in percent_columns:
        view[column] = view[column].map(lambda v: "n/a" if pd.isna(v) else f"{v:.1%}")
    return view.to_html(index=False, border=0, escape=True)


def write_dashboard(result: dict, summary: pd.DataFrame, images: dict[str, Path], path: Path) -> None:
    def embed(key: str, alt: str) -> str:
        data = base64.b64encode(images[key].read_bytes()).decode()
        return f'<img src="data:image/png;base64,{data}" alt="{html.escape(alt)}">'

    names = {**FEATURES, "cluster": "Cluster", "sector": "Group", "most_distinct": "Most distinct"}
    company = result["table"].reset_index().rename(columns={"ticker": "Company", **names})
    company["Group"] = company["Group"].map(SECTORS)
    company["Unusual"] = company["is_unusual"].map({True: "Yes", False: ""})
    columns = ["Company", "Cluster", "Group", *FEATURES.values(), "Most distinct", "Unusual"]
    company_html = _percent_table(company[columns], list(FEATURES.values()))

    cards = "".join(
        f"<div class='card'><h3>Cluster {html.escape(row.cluster)} · {row.companies} companies</h3>"
        f"<p>{html.escape(row.traits)}.</p><p class='muted'>{html.escape(row.members)}</p>"
        f"<p class='muted'>{html.escape(row.sector_mix)}</p></div>"
        for row in summary.itertuples()
    )
    flagged = ", ".join(result["table"].index[result["table"]["is_unusual"]])
    chosen = result["scores"].set_index("k").loc[result["k"]]
    tiles = [
        ("Companies", len(result["table"])),
        ("Clusters", result["k"]),
        ("Agreement with sector", f"{result['sector_agreement']:.2f}"),
        ("Cluster stability", f"{chosen['stability']:.2f}"),
    ]
    tile_html = "".join(f"<div class='tile'><span>{a}</span><b>{b}</b></div>" for a, b in tiles)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Financial Peer Groups</title><style>
body{{margin:0;background:{SURFACE};color:{INK};font:15px/1.5 system-ui,sans-serif}}
main{{max-width:1120px;margin:auto;padding:32px 16px}}h1{{margin:0;font-size:28px}}
.muted{{color:{MUTED};font-size:13px;margin:4px 0}}
.tiles,.cards,.charts{{display:grid;gap:12px;margin:20px 0}}
.tiles{{grid-template-columns:repeat(auto-fit,minmax(160px,1fr))}}
.cards{{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}}
.charts{{grid-template-columns:repeat(auto-fit,minmax(340px,1fr))}}
.tile,.card{{border:1px solid {GRID};border-radius:8px;padding:12px 14px}}
.tile span{{display:block;color:{MUTED};font-size:13px}}.tile b{{font-size:24px}}
.card h3{{margin:0 0 6px;font-size:15px}}.card p{{margin:4px 0}}
img{{width:100%;height:auto;border:1px solid {GRID};border-radius:8px}}
.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{padding:6px 8px;border-bottom:1px solid {GRID};text-align:right;white-space:nowrap}}
th:nth-child(-n+3),td:nth-child(-n+3){{text-align:left}}
</style></head><body><main>
<h1>Financial peer groups in Thai finance</h1>
<p class="muted">K-means on six statement measures for 2021-2025. Unusual companies: {html.escape(flagged)}.</p>
<div class="tiles">{tile_html}</div><div class="cards">{cards}</div>
<div class="charts">{embed("map", "Map of companies by financial profile")}
{embed("heatmap", "Heatmap of scaled measures by company")}
{embed("unusual", "Unusualness score by company")}
{embed("check", "Separation and stability by cluster count")}</div>
<h2>Company measures</h2><div class="scroll">{company_html}</div>
<p class="muted">{result["imputed"]} missing values were filled with the median. Medians use the years available.
Separation is moderate, so companies near a boundary could fall in another group. Some insurers report on the equity method, which affects comparison. Clusters describe similarity in reported figures. They are not a rating or investment advice.</p>
</main></body></html>"""
    path.write_text(page, encoding="utf-8")


def run(csv_path: str | Path, output_dir: str | Path) -> dict:
    """Run the analysis and overwrite the files in output_dir."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _style()
    result = analyze(build_features(load_panel(csv_path)))
    summary = describe_clusters(result["table"])
    images = {
        "map": plot_map(result, output / "01_company_map.png"),
        "heatmap": plot_heatmap(result, output / "02_profile_heatmap.png"),
        "unusual": plot_unusual(result, output / "03_unusual_companies.png"),
        "check": plot_model_check(result, output / "04_cluster_check.png"),
    }
    write_dashboard(result, summary, images, output / "dashboard.html")
    result["table"].to_csv(output / "companies.csv", encoding="utf-8-sig")
    result["summary"] = summary
    return result


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Create peer-group charts and a dashboard")
    parser.add_argument("--input", type=Path, default=here / "company_panel.csv")
    parser.add_argument("--output", type=Path, default=here / "output")
    parser.add_argument("--open", action="store_true", help="Open the dashboard in a browser")
    args = parser.parse_args()

    result = run(args.input, args.output)
    print(f"Clusters: {result['k']}, agreement with sector: {result['sector_agreement']:.2f}")
    print(result["scores"].round(2).to_string(index=False))
    for row in result["summary"].itertuples():
        print(f"{row.cluster} ({row.companies}): {row.traits}: {row.members}")
    print("Unusual:", ", ".join(result["table"].index[result["table"]["is_unusual"]]))
    print(f"Saved to {args.output.resolve()}")
    if args.open:
        webbrowser.open((args.output.resolve() / "dashboard.html").as_uri())


if __name__ == "__main__":
    main()
