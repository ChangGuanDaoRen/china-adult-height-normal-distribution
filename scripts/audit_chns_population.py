# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
import pyreadstat


# ============================================================
# 1. 项目路径
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# 2. 工具函数
# ============================================================

def normalize_name(name):
    return str(name).strip().upper()


def get_metadata(path):
    """
    只读取 SAS 元数据，不读取全部数据。
    """
    _, meta = pyreadstat.read_sas7bdat(
        str(path),
        metadataonly=True
    )
    return meta


def find_columns(meta):
    """
    返回：
    原始变量名 -> 大写变量名
    """
    return {
        col: normalize_name(col)
        for col in meta.column_names
    }


# ============================================================
# 3. 扫描所有 SAS 文件
# ============================================================

print("=" * 80)
print("CHNS 人口学信息审计")
print("=" * 80)

if not DATA_DIR.exists():
    raise FileNotFoundError(
        f"找不到数据目录：{DATA_DIR}"
    )

sas_files = sorted(
    DATA_DIR.rglob("*.sas7bdat")
)

print(f"\n数据目录：{DATA_DIR}")
print(f"发现 SAS 文件：{len(sas_files)}")
print()


# ============================================================
# 4. 检查每一个文件的变量
# ============================================================

TARGETS = {
    "IDIND",
    "IDINDIV",
    "GENDER",
    "SEX",
    "WEST_DOB_Y",
    "AGE",
    "WAVE",
    "HEIGHT",
    "CLN_HT",
}

file_infos = []

for path in sas_files:

    print("-" * 80)
    print(f"文件：{path}")

    try:
        meta = get_metadata(path)

    except Exception as e:
        print("读取元数据失败：", e)
        continue

    columns = list(meta.column_names)

    upper_map = {
        normalize_name(c): c
        for c in columns
    }

    matched = []

    for target in TARGETS:
        if target in upper_map:
            matched.append(
                upper_map[target]
            )

    print(f"变量总数：{len(columns)}")

    if matched:
        print("关注变量：")
        for col in sorted(matched):
            print(f"  {col}")

    file_infos.append({
        "path": path,
        "columns": columns,
        "upper_map": upper_map,
    })


# ============================================================
# 5. 自动寻找身高文件
# ============================================================

print()
print("=" * 80)
print("候选身高文件")
print("=" * 80)

height_candidates = []

for info in file_infos:

    upper_map = info["upper_map"]

    has_height = "HEIGHT" in upper_map
    has_wave = "WAVE" in upper_map

    if has_height:
        height_candidates.append(info)

        print(
            f"\n{info['path']}"
        )

        print(
            "  HEIGHT =",
            upper_map.get("HEIGHT")
        )

        print(
            "  WAVE   =",
            upper_map.get("WAVE")
        )

        print(
            "  IDIND  =",
            upper_map.get("IDIND")
        )

        print(
            "  CLN_HT =",
            upper_map.get("CLN_HT")
        )


if not height_candidates:
    raise RuntimeError(
        "没有找到包含 HEIGHT 的 SAS 文件。"
    )


# ============================================================
# 6. 自动寻找人口学文件
# ============================================================

print()
print("=" * 80)
print("候选人口学文件")
print("=" * 80)

demo_candidates = []

for info in file_infos:

    upper_map = info["upper_map"]

    has_id = (
        "IDIND" in upper_map
        or "IDINDIV" in upper_map
    )

    has_gender = (
        "GENDER" in upper_map
        or "SEX" in upper_map
    )

    has_birth = (
        "WEST_DOB_Y" in upper_map
    )

    has_age = (
        "AGE" in upper_map
    )

    has_wave = (
        "WAVE" in upper_map
    )

    if has_id and (
        has_gender
        or has_birth
        or has_age
    ):
        demo_candidates.append(info)

        print(
            f"\n{info['path']}"
        )

        print(
            "  ID：",
            upper_map.get("IDIND")
            or upper_map.get("IDINDIV")
        )

        print(
            "  GENDER/SEX：",
            upper_map.get("GENDER")
            or upper_map.get("SEX")
        )

        print(
            "  WEST_DOB_Y：",
            upper_map.get("WEST_DOB_Y")
        )

        print(
            "  AGE：",
            upper_map.get("AGE")
        )

        print(
            "  WAVE：",
            upper_map.get("WAVE")
        )


# ============================================================
# 7. 如果找不到人口学文件，只输出扫描结果
# ============================================================

if not demo_candidates:

    print()
    print("=" * 80)
    print("没有找到明显的人口学文件")
    print("=" * 80)

    print(
        "\n目前只能确认哪些文件存在，以及它们有哪些变量。"
    )

    print(
        "\n请把本次完整输出保存下来。"
    )

    raise SystemExit(0)


# ============================================================
# 8. 自动选择身高文件
#
# 优先：
#   文件名包含 pexam
#   否则选择第一个包含 HEIGHT 的文件
# ============================================================

height_info = None

for info in height_candidates:

    if "PEXAM" in info["path"].name.upper():
        height_info = info
        break

if height_info is None:
    height_info = height_candidates[0]

height_path = height_info["path"]

print()
print("=" * 80)
print("本次使用的身高文件")
print("=" * 80)
print(height_path)


# ============================================================
# 9. 读取身高数据
# ============================================================

height_upper = height_info["upper_map"]

height_cols = []

for key in [
    "IDIND",
    "IDINDIV",
    "HEIGHT",
    "WAVE",
    "CLN_HT",
]:

    if key in height_upper:
        height_cols.append(
            height_upper[key]
        )


height_df, height_meta = pyreadstat.read_sas7bdat(
    str(height_path),
    usecols=height_cols
)

height_df.columns = [
    normalize_name(c)
    for c in height_df.columns
]

print()
print("身高文件记录数：", len(height_df))

# 统一 ID 字段
if "IDIND" in height_df.columns:
    height_id_col = "IDIND"
elif "IDINDIV" in height_df.columns:
    height_id_col = "IDINDIV"
else:
    raise RuntimeError(
        "身高文件没有找到 IDIND/IDINDIV，无法进行人口学匹配。"
    )

height_df["_ID"] = pd.to_numeric(
    height_df[height_id_col],
    errors="coerce"
)

height_df["HEIGHT"] = pd.to_numeric(
    height_df["HEIGHT"],
    errors="coerce"
)

if "WAVE" in height_df.columns:
    height_df["WAVE"] = pd.to_numeric(
        height_df["WAVE"],
        errors="coerce"
    )


# ============================================================
# 10. 逐个检查人口学候选文件
# ============================================================

summary_rows = []

for demo_info in demo_candidates:

    demo_path = demo_info["path"]
    upper_map = demo_info["upper_map"]

    print()
    print("=" * 80)
    print("检查人口学文件")
    print("=" * 80)
    print(demo_path)

    # --------------------------------------------------------
    # 决定需要读取哪些变量
    # --------------------------------------------------------

    demo_cols = []

    id_col = (
        upper_map.get("IDIND")
        or upper_map.get("IDINDIV")
    )

    gender_col = (
        upper_map.get("GENDER")
        or upper_map.get("SEX")
    )

    birth_col = upper_map.get(
        "WEST_DOB_Y"
    )

    age_col = upper_map.get(
        "AGE"
    )

    wave_col = upper_map.get(
        "WAVE"
    )

    for col in [
        id_col,
        gender_col,
        birth_col,
        age_col,
        wave_col,
    ]:

        if col is not None and col not in demo_cols:
            demo_cols.append(col)

    # --------------------------------------------------------
    # 读取
    # --------------------------------------------------------

    try:

        demo_df, demo_meta = pyreadstat.read_sas7bdat(
            str(demo_path),
            usecols=demo_cols
        )

    except Exception as e:

        print(
            "读取人口学文件失败：",
            e
        )

        continue

    demo_df.columns = [
        normalize_name(c)
        for c in demo_df.columns
    ]

    print(
        "人口学记录数：",
        len(demo_df)
    )

    # --------------------------------------------------------
    # 统一 ID
    # --------------------------------------------------------

    if "IDIND" in demo_df.columns:
        demo_id_col = "IDIND"
    elif "IDINDIV" in demo_df.columns:
        demo_id_col = "IDINDIV"
    else:
        print(
            "没有可用的 IDIND/IDINDIV。"
        )
        continue

    demo_df["_ID"] = pd.to_numeric(
        demo_df[demo_id_col],
        errors="coerce"
    )

    # --------------------------------------------------------
    # 检查 ID 唯一性
    # --------------------------------------------------------

    duplicate_count = (
        demo_df["_ID"]
        .duplicated()
        .sum()
    )

    print(
        "人口学文件重复 ID 数：",
        duplicate_count
    )

    # --------------------------------------------------------
    # 选择合并方式
    #
    # 如果人口学文件本身有 WAVE：
    #     ID + WAVE
    #
    # 如果没有 WAVE：
    #     仅 ID
    # --------------------------------------------------------

    if (
        "WAVE" in demo_df.columns
        and "WAVE" in height_df.columns
    ):

        demo_df["WAVE"] = pd.to_numeric(
            demo_df["WAVE"],
            errors="coerce"
        )

        merge_keys = [
            "_ID",
            "WAVE",
        ]

        print(
            "合并方式：ID + WAVE"
        )

    else:

        merge_keys = [
            "_ID"
        ]

        print(
            "合并方式：仅 ID"
        )

    # --------------------------------------------------------
    # 合并
    # --------------------------------------------------------

    merged = height_df.merge(
        demo_df,
        on=merge_keys,
        how="left",
        suffixes=(
            "",
            "_DEMO"
        ),
        indicator=True
    )

    matched = (
        merged["_merge"] == "both"
    ).sum()

    match_rate = (
        matched / len(height_df)
        if len(height_df) > 0
        else 0
    )

    print(
        f"成功匹配：{matched:,}"
    )

    print(
        f"匹配率：{match_rate:.4%}"
    )

    # --------------------------------------------------------
    # 年龄
    # --------------------------------------------------------

    if "AGE" in merged.columns:

        merged["AGE_CALC"] = pd.to_numeric(
            merged["AGE"],
            errors="coerce"
        )

        age_source = "AGE"

    elif (
        "WEST_DOB_Y" in merged.columns
        and "WAVE" in merged.columns
    ):

        merged["WEST_DOB_Y"] = pd.to_numeric(
            merged["WEST_DOB_Y"],
            errors="coerce"
        )

        merged["AGE_CALC"] = (
            merged["WAVE"]
            - merged["WEST_DOB_Y"]
        )

        age_source = (
            "WAVE - WEST_DOB_Y"
        )

    else:

        merged["AGE_CALC"] = pd.NA

        age_source = "无法计算"

    print(
        "年龄来源：",
        age_source
    )

    # --------------------------------------------------------
    # 性别
    # --------------------------------------------------------

    if "GENDER" in merged.columns:

        gender_col_final = "GENDER"

    elif "SEX" in merged.columns:

        gender_col_final = "SEX"

    else:

        gender_col_final = None

    if gender_col_final:

        print(
            "\n性别取值："
        )

        print(
            merged[
                gender_col_final
            ]
            .value_counts(
                dropna=False
            )
            .sort_index()
        )

    # --------------------------------------------------------
    # 年龄总体情况
    # --------------------------------------------------------

    print()
    print(
        "年龄基本统计："
    )

    print(
        merged["AGE_CALC"]
        .describe()
    )

    # --------------------------------------------------------
    # 关键年龄段
    # --------------------------------------------------------

    adult = merged[
        merged["AGE_CALC"].notna()
        & (
            merged["AGE_CALC"] >= 18
        )
        & (
            merged["AGE_CALC"] <= 75
        )
    ].copy()

    print()
    print(
        "18～75 岁记录数：",
        len(adult)
    )

    print(
        "18～75 岁占比：",
        (
            len(adult) / matched
            if matched > 0
            else 0
        )
    )

    # --------------------------------------------------------
    # 20～24 岁
    # --------------------------------------------------------

    age20_24 = adult[
        (
            adult["AGE_CALC"] >= 20
        )
        & (
            adult["AGE_CALC"] <= 24
        )
    ]

    print(
        "20～24 岁记录数：",
        len(age20_24)
    )

    # --------------------------------------------------------
    # 各年龄段数量
    # --------------------------------------------------------

    bins = [
        18, 20, 25, 30, 35,
        40, 45, 50, 55, 60,
        65, 70, 76
    ]

    labels = [
        "18-19",
        "20-24",
        "25-29",
        "30-34",
        "35-39",
        "40-44",
        "45-49",
        "50-54",
        "55-59",
        "60-64",
        "65-69",
        "70-75",
    ]

    adult["AGE_GROUP"] = pd.cut(
        adult["AGE_CALC"],
        bins=bins,
        labels=labels,
        right=False
    )

    age_counts = (
        adult["AGE_GROUP"]
        .value_counts()
        .sort_index()
    )

    print()
    print(
        "年龄组分布："
    )

    print(
        age_counts.to_string()
    )

    # --------------------------------------------------------
    # 各性别 × 20～24 岁
    # --------------------------------------------------------

    if gender_col_final:

        young = adult[
            (
                adult["AGE_CALC"] >= 20
            )
            & (
                adult["AGE_CALC"] <= 24
            )
        ]

        print()
        print(
            "20～24 岁 × 性别："
        )

        print(
            young[
                gender_col_final
            ]
            .value_counts(
                dropna=False
            )
            .sort_index()
            .to_string()
        )

    # --------------------------------------------------------
    # 各 WAVE × 20～24 岁
    # --------------------------------------------------------

    if "WAVE" in adult.columns:

        young = adult[
            (
                adult["AGE_CALC"] >= 20
            )
            & (
                adult["AGE_CALC"] <= 24
            )
        ]

        wave_counts = (
            young["WAVE"]
            .value_counts(
                dropna=False
            )
            .sort_index()
        )

        print()
        print(
            "20～24 岁各调查年份记录数："
        )

        print(
            wave_counts.to_string()
        )

    # --------------------------------------------------------
    # 保存摘要信息
    # --------------------------------------------------------

    summary_rows.append({
        "demographic_file": str(
            demo_path
        ),
        "demo_records": len(demo_df),
        "duplicate_ids": int(
            duplicate_count
        ),
        "height_records": len(
            height_df
        ),
        "matched_records": int(
            matched
        ),
        "match_rate": match_rate,
        "age_source": age_source,
        "adult_18_75": int(
            len(adult)
        ),
        "age20_24": int(
            len(age20_24)
        ),
    })


# ============================================================
# 11. 保存审计摘要
# ============================================================

summary_df = pd.DataFrame(
    summary_rows
)

summary_file = (
    OUTPUT_DIR
    / "chns_population_audit.csv"
)

summary_df.to_csv(
    summary_file,
    index=False,
    encoding="utf-8-sig"
)

print()
print("=" * 80)
print("人口学审计完成")
print("=" * 80)

print(
    "摘要文件：",
    summary_file
)

print(
    "\n重要：本程序没有把合并后的个体数据保存到 outputs。"
)

print(
    "请不要把原始 CHNS 个体级 SAS 文件上传到公开 GitHub。"
)