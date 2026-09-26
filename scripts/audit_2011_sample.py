# -*- coding: utf-8 -*-

from pathlib import Path

import pandas as pd
import pyreadstat


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

HEIGHT_FILE = DATA_DIR / "pexam_00.sas7bdat"
MASTER_FILE = DATA_DIR / "mast_pub_12.sas7bdat"


height, _ = pyreadstat.read_sas7bdat(
    str(HEIGHT_FILE),
    usecols=["IDind", "HEIGHT", "WAVE"]
)

master, _ = pyreadstat.read_sas7bdat(
    str(MASTER_FILE),
    usecols=["Idind", "GENDER", "WEST_DOB_Y"]
)

height.columns = [str(c).upper() for c in height.columns]
master.columns = [str(c).upper() for c in master.columns]

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

df = height.merge(
    master[["ID", "GENDER", "WEST_DOB_Y"]],
    on="ID",
    how="left",
    validate="many_to_one"
)

df["AGE"] = (
    df["WAVE"] - df["WEST_DOB_Y"]
)

# --------------------------------------------------
# 原始2011年20～24岁样本
# --------------------------------------------------

base = df[
    (df["WAVE"] == 2011)
    & (df["AGE"] >= 20)
    & (df["AGE"] <= 24)
].copy()

print("=" * 80)
print("2011年 CHNS 20～24岁样本清洗审计")
print("=" * 80)

print("\n原始20～24岁记录数：", len(base))

print("\nGENDER 分布：")
print(
    base["GENDER"]
    .value_counts(dropna=False)
    .sort_index()
)

print("\nHEIGHT 缺失数：")
print(base["HEIGHT"].isna().sum())

print("\nHEIGHT < 100：")
print(
    (base["HEIGHT"] < 100).sum()
)

print("\nHEIGHT > 220：")
print(
    (base["HEIGHT"] > 220).sum()
)

print("\nHEIGHT < 100 或 > 220：")
print(
    (
        (base["HEIGHT"] < 100)
        | (base["HEIGHT"] > 220)
    ).sum()
)

print("\n有效HEIGHT记录：")

valid_height = base[
    base["HEIGHT"].notna()
    & (base["HEIGHT"] >= 100)
    & (base["HEIGHT"] <= 220)
]

print(len(valid_height))

print("\n最终性别有效样本：")

final = valid_height[
    valid_height["GENDER"].isin([1, 2])
]

print(len(final))

print("\n最终男性：")
print(
    (final["GENDER"] == 1).sum()
)

print("\n最终女性：")
print(
    (final["GENDER"] == 2).sum()
)

print("\n排除总数：")
print(
    len(base) - len(final)
)

print()
print("=" * 80)
print("完成")
print("=" * 80)