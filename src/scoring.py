import pandas as pd

# indicator -> True if lower is better
INDICATORS = {
    "wait": True,
    "processing": True,
    "cost": True,
    "complaints": True,
    "coverage": False,
    "satisfaction": False,
}


def midpoints(df):
    """Turn the min/max range columns into one value per indicator."""
    out = pd.DataFrame(index=df.index)
    for name in ["wait", "processing", "coverage"]:
        out[name] = df[[f"{name}_min", f"{name}_max"]].mean(axis=1)
    out["cost"] = df["cost"]
    out["complaints"] = df["complaints"]
    out["satisfaction"] = df["satisfaction"]
    return out


def min_max(series, lower_is_better):
    """Rescale to 0-100: best facility in the group = 100, worst = 0."""
    low, high = series.min(), series.max()
    if pd.isna(low) or high == low:
        return pd.Series(float("nan"), index=series.index)
    scaled = (series - low) / (high - low) * 100
    return 100 - scaled if lower_is_better else scaled


def composite_score(df, weights):
    """Weighted average of the 0-100 scores.

    Indicators with no usable data are dropped and their weight is shared
    among the rest. A facility missing any used indicator is not ranked.
    """
    values = midpoints(df)
    scaled = pd.DataFrame(
        {name: min_max(values[name], lower) for name, lower in INDICATORS.items()}
    )
    usable = [name for name in INDICATORS if scaled[name].notna().any()]
    total = sum(weights[name] for name in usable)
    if not usable or total == 0:
        nothing = pd.Series(float("nan"), index=df.index)
        return scaled, nothing, nothing, usable

    score = sum(scaled[name] * weights[name] for name in usable) / total
    score = score.where(scaled[usable].notna().all(axis=1))
    rank = score.rank(ascending=False, method="min")
    return scaled, score, rank, usable