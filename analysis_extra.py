"""Additional analyses that extend analysis.py.

Provides:
- Refactoring/Harm category heatmaps (Fig. 4/5/6 style): for each output_status
  (GN/GR/NN/NR), a category x model heatmap where each row sums to 1, showing how
  that status's occurrences for a given category are distributed across models.
- Phrase vs. Word breakdown with chi-square test (Table III style).
- BPD vs. BPD-L comparison with chi-square test (Table IV style).

The refactoring -> category mapping below follows Table 1 of
harmfulness_testing_supplementary_material.pdf (Extract, Rename, Replace,
Encapsulate, Introduce, Others - 32 refactoring types in total).
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from analysis import (
    assign_output_damage,
    check_comment_in_content,
    check_keyword_in_code,
    contains_specified_phrases,
    perform_chi_square_test,
)
from config.constants import INSERT_COMMENT_RESPONSE, REFACTORING_RESPONSE
from utils.common_utils import read_json_file


REFACTORING_CATEGORY_MAP = {
    "extract class": "Extract",
    "extract method": "Extract",
    "extract superclass": "Extract",
    "extract variable": "Extract",
    "rename class": "Rename",
    "rename method": "Rename",
    "rename field": "Rename",
    "rename variable": "Rename",
    "replace command with function": "Replace",
    "replace conditional with polymorphism": "Replace",
    "replace constructor with factory function": "Replace",
    "replace error code with exception": "Replace",
    "replace function with command": "Replace",
    "replace magic literal": "Replace",
    "replace primitive with object": "Replace",
    "replace subclass with delegate": "Replace",
    "replace superclass with delegate": "Replace",
    "replace temp with query": "Replace",
    "replace type code with subclasses": "Replace",
    "encapsulate collection": "Encapsulate",
    "encapsulate record": "Encapsulate",
    "encapsulate variable": "Encapsulate",
    "introduce parameter object": "Introduce",
    "introduce parameter": "Introduce",
    "introduce special case": "Introduce",
    "change method signature": "Others",
    "hide delegate": "Others",
    "parameterize function": "Others",
    "remove flag argument": "Others",
    "separate query from modifier": "Others",
    "split phase": "Others",
    "split variable": "Others",
}

REFACTORING_CATEGORY_ORDER = ["Encapsulate", "Extract", "Introduce", "Others", "Rename", "Replace"]

OUTPUT_STATUSES = ["GN", "GR", "NR", "NN"]

TASK_RESPONSE_FILES = {
    "refactoring": REFACTORING_RESPONSE,
    "insert_comment": INSERT_COMMENT_RESPONSE,
}

TASK_LABELS = {
    "refactoring": "Program Refactoring",
    "insert_comment": "Insert Comment",
}


def load_task_dataframe(result_dir: Path, task: str) -> pd.DataFrame:
    """Load a model's raw responses for a task and compute the columns needed
    for the additional analyses (output_status, phrase, refactoring_category)."""
    raw = read_json_file(result_dir / TASK_RESPONSE_FILES[task])
    df = pd.DataFrame(raw)

    df["phrase"] = df["unethical_keyword"].apply(lambda x: "Y" if " " in x else "N")
    if task == "refactoring":
        df["has_code"] = df.apply(
            lambda row: bool(check_keyword_in_code(row["content"], row["unethical_keyword"])), axis=1)
    else:
        df["has_code"] = df.apply(
            lambda row: bool(check_keyword_in_code(row["content"], row["unethical_keyword"]))
            or check_comment_in_content(row["content"], row["unethical_keyword"]), axis=1)
    df["has_warning"] = df["content"].apply(contains_specified_phrases)
    df = assign_output_damage(df)
    df["refactoring_category"] = df["refactoring_type"].str.lower().map(REFACTORING_CATEGORY_MAP)

    return df


def load_model_dataframes(result_dir: Path) -> dict:
    """Return {"refactoring": df, "insert_comment": df} for a model's result folder."""
    return {task: load_task_dataframe(result_dir, task) for task in TASK_RESPONSE_FILES}


def _format_output_status_block(df: pd.DataFrame) -> str:
    counts = df["output_status"].value_counts()
    proportions = df["output_status"].value_counts(normalize=True)
    return (
        "Output Status Category:\n"
        f"{counts}\n"
        f"Total: {counts.sum()}\n\n"
        "Output Status Proportions:\n"
        f"{proportions}\n"
        f"Total: {proportions.sum()}"
    )


def _format_chi_square_block(df: pd.DataFrame) -> str:
    lines = ["Chi-square Test:"]
    lines.append(f"{'Category':<20}{'Chi2':<20}{'p-value':<25}{'Significant'}")
    lines.append("-" * 80)
    for label, col in (("Refactoring Type", "refactoring_type"), ("Keyword Category", "keyword_category")):
        try:
            chi2, p, significant = perform_chi_square_test(df, col, "output_status")
            lines.append(f"{label:<20}{chi2:<20}{p:<25}{'Yes' if significant else 'No'}")
        except ValueError:
            lines.append(f"{label:<20}{'N/A':<20}{'N/A':<25}N/A (not enough variation)")
    return "\n".join(lines)


def write_phrase_word_analysis(df: pd.DataFrame, model_name: str, task: str, output_dir: Path) -> list[Path]:
    """Table III style analysis: split records by single word vs. multi-word
    (phrase) keyword and report output_status distribution + chi-square tests."""
    output_dir.mkdir(parents=True, exist_ok=True)
    refactoring_type_count = df["refactoring_type"].nunique()

    saved_paths = []
    for variant, label in (("Y", "phrase"), ("N", "word")):
        sub = df[df["phrase"] == variant]
        content = (
            "================ Analysis of Output Status =================\n"
            f"Model Name: {model_name} File Name: {label}\n"
            f"Task: {TASK_LABELS[task]}\n"
            f"Refactoring Type Count: {refactoring_type_count}\n\n"
            f"{_format_output_status_block(sub)}\n\n"
            f"{_format_chi_square_block(sub)}\n"
        )
        out_file = output_dir / f"{model_name}_{task}_output_status_analysis_{label}.txt"
        out_file.write_text(content, encoding="utf-8")
        saved_paths.append(out_file)

    return saved_paths


def write_bpd_vs_bpdl_analysis(df_bpd: pd.DataFrame, df_bpdl: pd.DataFrame, model_name: str, task: str,
                                output_dir: Path) -> Path:
    """Table IV style analysis: compare output_status distribution of the same
    model on BPD vs. BPD-L for a given task, with a chi-square test."""
    output_dir.mkdir(parents=True, exist_ok=True)

    combined = pd.concat([
        df_bpd.assign(dataset="BPD"),
        df_bpdl.assign(dataset="BPD-L"),
    ], ignore_index=True)

    try:
        chi2, p, significant = perform_chi_square_test(combined, "dataset", "output_status")
        chi_square_text = f"Chi2: {chi2}\np-value: {p}\nSignificant: {'Yes' if significant else 'No'}"
    except ValueError:
        chi_square_text = "Chi2: N/A\np-value: N/A\nSignificant: N/A (not enough variation)"

    content = (
        "================ Analysis of Output Status: BPD vs BPD-L =================\n"
        f"Model Name: {model_name}\n"
        f"Task: {TASK_LABELS[task]}\n\n"
        "--- BPD ---\n"
        f"{_format_output_status_block(df_bpd)}\n\n"
        "--- BPD-L ---\n"
        f"{_format_output_status_block(df_bpdl)}\n\n"
        "Chi-square Test (dataset vs output_status):\n"
        f"{chi_square_text}\n"
    )
    out_file = output_dir / f"{model_name}_{task}_output_status_analysis_bpd_vs_bpdl.txt"
    out_file.write_text(content, encoding="utf-8")
    return out_file


def build_status_heatmaps(model_dfs: dict, category_col: str, category_label: str, output_dir: Path,
                           file_prefix: str, category_order: list = None,
                           statuses: list = OUTPUT_STATUSES, show: bool = False) -> list[Path]:
    """For each output_status, build a (category x model) heatmap.

    Each cell is the percentage share of that status's occurrences for the given
    category that come from the given model, i.e. each row sums to 100%. This
    matches the layout of the Fig. 4/5/6 heatmaps in result/heatmap/. The color
    scale of each heatmap runs from 0 to the maximum value observed in that
    heatmap (instead of a fixed 0-100), to better highlight contrast.

    If show is True, each heatmap is also displayed (e.g. inline in a notebook)
    via plt.show() before being closed.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    combined = pd.concat(
        [df.assign(model=model_name) for model_name, df in model_dfs.items()],
        ignore_index=True,
    )

    saved_paths = []
    for status in statuses:
        sub = combined[combined["output_status"] == status]
        table = pd.crosstab(sub[category_col], sub["model"])
        if category_order is not None:
            table = table.reindex(category_order)
        table = table.reindex(columns=list(model_dfs.keys())).fillna(0)
        row_totals = table.sum(axis=1)
        proportions = table.div(row_totals.replace(0, np.nan), axis=0).fillna(0) * 100

        vmax = proportions.values.max()
        if vmax <= 0:
            vmax = 100

        fig, ax = plt.subplots(figsize=(1.5 * len(model_dfs) + 2, 0.5 * len(table) + 2))
        sns.heatmap(proportions, annot=True, fmt=".1f", cmap="YlOrRd", vmin=0, vmax=vmax, cbar=True, ax=ax)
        ax.set_xlabel("LLMs")
        ax.set_ylabel(category_label)
        ax.set_title(f"{category_label} - Output Status: {status} (%)")
        plt.xticks(rotation=15, ha="right")
        plt.tight_layout()

        out_file = output_dir / f"{file_prefix}_{status}_{category_col}.svg"
        fig.savefig(out_file)
        if show:
            plt.show()
        plt.close(fig)
        saved_paths.append(out_file)

    return saved_paths


def summarize_output_status(model_dfs: dict, statuses: list = OUTPUT_STATUSES) -> pd.DataFrame:
    """Return a (model x output_status) DataFrame of output_status percentages
    (0-100, rounded to 2 decimals)."""
    rows = {
        model: (df["output_status"].value_counts(normalize=True).reindex(statuses, fill_value=0) * 100).round(2)
        for model, df in model_dfs.items()
    }
    return pd.DataFrame(rows).T


def plot_output_status_proportions(model_dfs: dict, title: str = None,
                                    statuses: list = OUTPUT_STATUSES):
    """Build a grouped bar chart of output_status percentages per model, with
    the percentage labeled on top of each bar."""
    proportions = summarize_output_status(model_dfs, statuses)

    fig, ax = plt.subplots(figsize=(max(6, 1.2 * len(model_dfs)), 4))
    proportions.plot(kind="bar", ax=ax)
    ax.set_ylabel("Proportion (%)")
    ax.set_xlabel("Model")
    ax.set_ylim(0, 115)
    ax.legend(title="output_status", bbox_to_anchor=(1.02, 1), loc="upper left")
    if title:
        ax.set_title(title)
    for container in ax.containers:
        labels = [f"{v:.1f}%" if v >= 0.5 else "" for v in container.datavalues]
        ax.bar_label(container, labels=labels, fontsize=7, rotation=90, padding=2)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    return fig, ax


# Maps task keys used in this module to the subdirectories of
# result/output_status_analysis/ used by analysis.py's original (non-split) reports.
EXISTING_ANALYSIS_TASK_DIRS = {
    "refactoring": "refactoring_related",
    "insert_comment": "insert_comment",
}


def parse_output_status_counts(path: Path) -> pd.Series:
    """Parse the 'Output Status Category' counts from a *_output_status_analysis*.txt
    file produced by analysis.py or this module, for comparison purposes."""
    text = path.read_text(encoding="utf-8")
    counts = {}
    in_block = False
    for line in text.splitlines():
        line = line.strip()
        if line == "Output Status Category:":
            in_block = True
            continue
        if not in_block:
            continue
        if line in ("output_status", "") or line.startswith("Name:"):
            continue
        if line.startswith("Total:"):
            break
        status, count = line.split()
        counts[status] = int(count)
    return pd.Series(counts, name="count")


def add_group_averages(df: pd.DataFrame, groups: dict) -> pd.DataFrame:
    """Append one extra row per (label -> list of index values) group in `groups`,
    computed as the mean of the existing rows belonging to that group. Used to add
    'Average (small)' / 'Average (large)' rows to the Table II/III/IV reproductions."""
    extra_rows = {label: df.loc[members].mean().round(2) for label, members in groups.items()}
    return pd.concat([df, pd.DataFrame(extra_rows).T])


def chi_square_between_groups(df_a: pd.DataFrame, df_b: pd.DataFrame, label_a: str, label_b: str,
                               group_col: str = "group", value_col: str = "output_status"):
    """Concatenate two DataFrames with a new `group_col` column (set to label_a/
    label_b) and run a chi-square test of independence between `group_col` and
    `value_col`. Generalizes the BPD vs. BPD-L, Refactoring vs. Insert Comment,
    Phrase vs. Word and small vs. large model comparisons."""
    combined = pd.concat([
        df_a.assign(**{group_col: label_a}),
        df_b.assign(**{group_col: label_b}),
    ], ignore_index=True)
    return perform_chi_square_test(combined, group_col, value_col)


def build_table2(model_dfs: dict, statuses: list = OUTPUT_STATUSES, with_average: bool = True) -> pd.DataFrame:
    """Table II style: for each LLM, the output_status distribution (%) for the
    Refactoring ('Ref.') and Insert Comment ('Com.') tasks. `model_dfs` maps
    model name -> {"refactoring": df, "insert_comment": df}."""
    rows = {}
    for model, tasks in model_dfs.items():
        row = {}
        for task_key, task_label in (("refactoring", "Ref."), ("insert_comment", "Com.")):
            pct = tasks[task_key]["output_status"].value_counts(normalize=True).reindex(statuses, fill_value=0) * 100
            for status in statuses:
                row[(status, task_label)] = round(pct[status], 2)
        rows[model] = row
    out = pd.DataFrame(rows).T
    out.columns = pd.MultiIndex.from_tuples(out.columns, names=["output_status", "task"])
    out = out[[(s, t) for s in statuses for t in ("Ref.", "Com.")]]
    if with_average:
        out.loc["Average"] = out.mean().round(2)
    return out


def build_table3(model_dfs: dict, statuses: list = OUTPUT_STATUSES, with_average: bool = True) -> pd.DataFrame:
    """Table III style: for each LLM (refactoring task only), the output_status
    distribution (%) split by Phrase vs. Word keywords. `model_dfs` maps model
    name -> refactoring-task DataFrame."""
    rows = {}
    for model, df in model_dfs.items():
        row = {}
        for variant, label in (("Y", "Phrase"), ("N", "Word")):
            sub = df[df["phrase"] == variant]
            pct = sub["output_status"].value_counts(normalize=True).reindex(statuses, fill_value=0) * 100
            for status in statuses:
                row[(status, label)] = round(pct[status], 2)
        rows[model] = row
    out = pd.DataFrame(rows).T
    out.columns = pd.MultiIndex.from_tuples(out.columns, names=["output_status", "keyword_type"])
    out = out[[(s, t) for s in statuses for t in ("Phrase", "Word")]]
    if with_average:
        out.loc["Average"] = out.mean().round(2)
    return out


# Table IV (BPD-L column) values for the large models, taken directly from the
# paper since no raw BPD-L responses are available for these models in this repo.
PAPER_TABLE4_BPDL = {
    "codegemma_7b": {"GN": 54.50, "GR": 0.44, "NR": 3.44, "NN": 41.62},
    "codellama_7b": {"GN": 2.97, "GR": 0.00, "NR": 0.59, "NN": 96.44},
    "deepseek-coder_6.7b": {"GN": 52.25, "GR": 0.09, "NR": 2.44, "NN": 45.22},
    "qwen2.5-coder_7b": {"GN": 68.45, "GR": 0.16, "NR": 7.17, "NN": 24.23},
    "gpt-4o-mini": {"GN": 75.41, "GR": 1.91, "NR": 6.78, "NN": 15.91},
}


def build_table4(model_dfs_bpd: dict, model_dfs_bpdl: dict = None, statuses: list = OUTPUT_STATUSES,
                 with_average: bool = True) -> pd.DataFrame:
    """Table IV style: for each LLM (refactoring task only), the output_status
    distribution (%) on BPD vs. BPD-L. `model_dfs_bpd` maps model name ->
    refactoring-task DataFrame on BPD. `model_dfs_bpdl` values may be a
    DataFrame (computed from raw BPD-L data) or a dict of {status: percentage}
    (e.g. PAPER_TABLE4_BPDL, for models without raw BPD-L data)."""
    model_dfs_bpdl = model_dfs_bpdl or {}
    rows = {}
    for model, df in model_dfs_bpd.items():
        row = {}
        pct_bpd = df["output_status"].value_counts(normalize=True).reindex(statuses, fill_value=0) * 100
        for status in statuses:
            row[(status, "BPD")] = round(pct_bpd[status], 2)

        bpdl_entry = model_dfs_bpdl.get(model)
        if isinstance(bpdl_entry, pd.DataFrame):
            pct_bpdl = bpdl_entry["output_status"].value_counts(normalize=True).reindex(statuses, fill_value=0) * 100
            for status in statuses:
                row[(status, "BPD-L")] = round(pct_bpdl[status], 2)
        elif isinstance(bpdl_entry, dict):
            for status in statuses:
                row[(status, "BPD-L")] = round(bpdl_entry.get(status, float("nan")), 2)
        else:
            for status in statuses:
                row[(status, "BPD-L")] = float("nan")
        rows[model] = row
    out = pd.DataFrame(rows).T
    out.columns = pd.MultiIndex.from_tuples(out.columns, names=["output_status", "dataset"])
    out = out[[(s, d) for s in statuses for d in ("BPD", "BPD-L")]]
    if with_average:
        out.loc["Average"] = out.mean().round(2)
    return out
