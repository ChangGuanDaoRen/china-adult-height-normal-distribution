# -*- coding: utf-8 -*-

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
from scipy import stats
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

HEIGHT_FILE = DATA_DIR / "pexam_00.sas7bdat"
MASTER_FILE = DATA_DIR / "mast_pub_12.sas7bdat"


def load_data():

    height, _ = pyreadstat.read_sas7bdat(
        str(HEIGHT_FILE),
        usecols=["IDind", "HEIGHT", "WAVE"]
    )

    master, _ = pyreadstat.read_sas7bdat(
        str(MASTER_FILE),
        usecols=["Idind", "GENDER", "WEST_DOB_Y"]
    )

    height.columns = [
        str(c).upper()
        for c in height.columns
    ]

    master.columns = [
        str(c).upper()
        for c in master.columns
    ]

    height["ID"] = pd.to_numeric(
        height["IDIND"],
        errors="coerce"
    )

    master["ID"] = pd.to_numeric(
        master["IDIND"],
        errors="coerce"
    )

    height["HEIGHT"] = pd.to_numeric(
        height["HEIGHT"],
        errors="coerce"
    )

    height["WAVE"] = pd.to_numeric(
        height["WAVE"],
        errors="coerce"
    )

    master["GENDER"] = pd.to_numeric(
        master["GENDER"],
        errors="coerce"
    )

    master["WEST_DOB_Y"] = pd.to_numeric(
        master["WEST_DOB_Y"],
        errors="coerce"
    )

    merged = height.merge(
        master[
            ["ID", "GENDER", "WEST_DOB_Y"]
        ],
        on="ID",
        how="left",
        validate="many_to_one"
    )

    merged["AGE"] = (
        merged["WAVE"]
        - merged["WEST_DOB_Y"]
    )

    return merged


def analyze_group(x):

    x = pd.to_numeric(
        x,
        errors="coerce"
    ).dropna()

    n = len(x)

    mean = x.mean()
    median = x.median()

    variance = x.var(ddof=1)
    std = x.std(ddof=1)

    skew = stats.skew(
        x,
        bias=False
    )

    kurtosis = stats.kurtosis(
        x,
        bias=False
    )

    # Shapiro-Wilk
    W, p = stats.shapiro(x)

    # 经验 1σ、2σ、3σ 覆盖率
    proportions = {}

    for k in [1, 2, 3]:

        low = mean - k * std
        high = mean + k * std

        proportion = (
            ((x >= low) & (x <= high))
            .mean()
        )

        proportions[
            f"within_{k}sigma"
        ] = proportion

    return {
        "n": n,
        "mean_cm": mean,
        "median_cm": median,
        "variance_cm2": variance,
        "std_cm": std,
        "skew": skew,
        "excess_kurtosis": kurtosis,
        "min_cm": x.min(),
        "max_cm": x.max(),
        "shapiro_W": W,
        "shapiro_p": p,
        **proportions
    }


def make_histogram(
    x,
    gender_name,
    out_name
):

    mean = x.mean()
    std = x.std(ddof=1)

    plt.figure(
        figsize=(9, 6)
    )

    plt.hist(
        x,
        bins=20,
        density=True,
        alpha=0.70,
        edgecolor="black"
    )

    grid = np.linspace(
        x.min(),
        x.max(),
        500
    )

    normal_curve = stats.norm.pdf(
        grid,
        mean,
        std
    )

    plt.plot(
        grid,
        normal_curve,
        linewidth=2,
        label=(
            f"Normal curve "
            f"(μ={mean:.2f}, σ={std:.2f})"
        )
    )

    plt.xlabel(
        "Height (cm)"
    )

    plt.ylabel(
        "Density"
    )

    plt.title(
        f"CHNS 2011 Height Distribution "
        f"(Age 20–24, {gender_name})"
    )

    plt.legend()

    plt.tight_layout()

    output = (
        OUTPUT_DIR
        / out_name
    )

    plt.savefig(
        output,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    return output


def make_qqplot(
    x,
    gender_name,
    out_name
):

    plt.figure(
        figsize=(7, 7)
    )

    stats.probplot(
        x,
        dist="norm",
        plot=plt
    )

    plt.title(
        f"Q-Q Plot of CHNS 2011 Height "
        f"(Age 20–24, {gender_name})"
    )

    plt.tight_layout()

    output = (
        OUTPUT_DIR
        / out_name
    )

    plt.savefig(
        output,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    return output


# 论文插图编号：图5-1 男性直方图 / 图5-2 女性直方图
#               图5-3 男性 Q-Q 图 / 图5-4 女性 Q-Q 图
# 输出文件名与仓库 outputs/ 中正式文件保持完全一致
FIGURE_NAMES = {
    ("Male", "hist"): "fig5_1_2011_CHNS_male_histogram.png",
    ("Female", "hist"): "fig5_2_2011_CHNS_female_histogram.png",
    ("Male", "QQ"): "fig5_3_2011_CHNS_male_qq.png",
    ("Female", "QQ"): "fig5_4_2011_CHNS_female_qq.png",
}


def main():

    print("=" * 80)
    print("CHNS 2011年20～24岁成年人身高正态性分析")
    print("=" * 80)

    df = load_data()

    sample = df[
        (df["WAVE"] == 2011)
        & (df["AGE"] >= 20)
        & (df["AGE"] <= 24)
        & df["HEIGHT"].notna()
        & (df["HEIGHT"] >= 100)
        & (df["HEIGHT"] <= 220)
    ].copy()

    print(
        "\n研究总体：2011年 CHNS 20～24岁成年人"
    )

    print(
        "有效样本量：",
        len(sample)
    )

    results = []

    for gender_code, gender_name in [
        (1, "Male"),
        (2, "Female")
    ]:

        group = sample[
            sample["GENDER"] == gender_code
        ]

        x = group["HEIGHT"]

        result = analyze_group(x)

        result["gender"] = gender_name
        result["wave"] = 2011
        result["age_range"] = "20-24"

        results.append(result)

        print()
        print("-" * 80)

        print(
            f"{gender_name}"
        )

        print(
            f"n = {result['n']}"
        )

        print(
            f"mean = {result['mean_cm']:.4f} cm"
        )

        print(
            f"median = {result['median_cm']:.4f} cm"
        )

        print(
            f"variance = {result['variance_cm2']:.4f} cm²"
        )

        print(
            f"std = {result['std_cm']:.4f} cm"
        )

        print(
            f"skew = {result['skew']:.6f}"
        )

        print(
            f"excess kurtosis = "
            f"{result['excess_kurtosis']:.6f}"
        )

        print(
            f"min = {result['min_cm']:.2f} cm"
        )

        print(
            f"max = {result['max_cm']:.2f} cm"
        )

        print(
            f"Shapiro-Wilk W = "
            f"{result['shapiro_W']:.6f}"
        )

        print(
            f"Shapiro-Wilk p = "
            f"{result['shapiro_p']:.10g}"
        )

        print(
            f"±1σ 实际比例 = "
            f"{result['within_1sigma']:.4%}"
        )

        print(
            f"±2σ 实际比例 = "
            f"{result['within_2sigma']:.4%}"
        )

        print(
            f"±3σ 实际比例 = "
            f"{result['within_3sigma']:.4%}"
        )

        make_histogram(
            x,
            gender_name,
            FIGURE_NAMES[
                (gender_name, "hist")
            ]
        )

        make_qqplot(
            x,
            gender_name,
            FIGURE_NAMES[
                (gender_name, "QQ")
            ]
        )

    result_df = pd.DataFrame(
        results
    )

    columns = [
        "wave",
        "age_range",
        "gender",
        "n",
        "mean_cm",
        "median_cm",
        "variance_cm2",
        "std_cm",
        "skew",
        "excess_kurtosis",
        "min_cm",
        "max_cm",
        "shapiro_W",
        "shapiro_p",
        "within_1sigma",
        "within_2sigma",
        "within_3sigma"
    ]

    result_df = result_df[
        columns
    ]

    # 表 5-2：正态性检验结果（与仓库 outputs/ 正式文件同名同格式）
    output_t52 = (
        OUTPUT_DIR
        / "table5_2_2011_CHNS_20_24_normality_test.csv"
    )

    result_df.to_csv(
        output_t52,
        index=False,
        encoding="utf-8-sig"
    )

    # 表 5-1：描述统计量（与仓库 outputs/ 正式文件同名同格式）
    male = results[0]
    female = results[1]

    desc_rows = [
        ("样本量 n", f"{male['n']:d}", f"{female['n']:d}"),
        ("均值（厘米）", f"{male['mean_cm']:.4f}", f"{female['mean_cm']:.4f}"),
        ("中位数（厘米）", f"{male['median_cm']:.4f}", f"{female['median_cm']:.4f}"),
        ("方差（平方厘米）", f"{male['variance_cm2']:.4f}", f"{female['variance_cm2']:.4f}"),
        ("标准差（厘米）", f"{male['std_cm']:.4f}", f"{female['std_cm']:.4f}"),
        ("偏度", f"{male['skew']:.4f}", f"{female['skew']:.4f}"),
        ("超额峰度", f"{male['excess_kurtosis']:.4f}", f"{female['excess_kurtosis']:.4f}"),
        ("最小值（厘米）", f"{male['min_cm']:.4f}", f"{female['min_cm']:.4f}"),
        ("最大值（厘米）", f"{male['max_cm']:.4f}", f"{female['max_cm']:.4f}"),
    ]

    desc_df = pd.DataFrame(
        desc_rows,
        columns=["统计量", "男性", "女性"]
    )

    output_t51 = (
        OUTPUT_DIR
        / "table5_1_2011_CHNS_20_24_descriptive_statistics.csv"
    )

    desc_df.to_csv(
        output_t51,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print("=" * 80)
    print("分析完成")
    print("=" * 80)

    print(
        "\n结果表：",
        output_t51
    )

    print(
        "结果表：",
        output_t52
    )

    print(
        "\n已生成两组直方图和两组 Q-Q 图。"
    )


if __name__ == "__main__":
    main()