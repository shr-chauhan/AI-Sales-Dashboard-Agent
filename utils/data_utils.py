
# ---

# ## 4. `utils/data_utils.py`

# ```python
import pandas as pd
from dateutil.parser import parse


def load_sales_csv(file) -> pd.DataFrame:
    """Load CSV into a pandas DataFrame with basic cleaning.
    Tries multiple encodings to handle files that aren't UTF-8.
    """
    # Common encodings to try (in order of likelihood)
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
    
    for encoding in encodings:
        try:
            # Reset file pointer to beginning
            if hasattr(file, 'seek'):
                file.seek(0)
            df = pd.read_csv(file, encoding=encoding)
            # Strip column names
            df.columns = [c.strip() for c in df.columns]
            return df
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            # If it's not an encoding error, re-raise it
            if encoding == encodings[0]:  # Only raise if it's the first attempt
                raise e
            continue
    
    # If all encodings fail, try with error handling
    if hasattr(file, 'seek'):
        file.seek(0)
    df = pd.read_csv(file, encoding='utf-8', errors='replace')
    df.columns = [c.strip() for c in df.columns]
    return df


def detect_date_column(df: pd.DataFrame):
    """Try to guess the date column."""
    candidates = [c for c in df.columns if "date" in c.lower()]
    if candidates:
        return candidates[0]
    # fallback: try to parse first column as date
    first = df.columns[0]
    try:
        _ = parse(str(df[first].iloc[0]), fuzzy=False)
        return first
    except Exception:
        return None


def detect_numeric_column(df: pd.DataFrame, preferred_names=None):
    """
    Try to infer a numeric column from preferred_names or any numeric col.
    """
    if preferred_names is None:
        preferred_names = []

    # First, look for preferred names
    for name in preferred_names:
        for col in df.columns:
            if col.lower().replace(" ", "") == name.lower().replace(" ", ""):
                if pd.api.types.is_numeric_dtype(df[col]):
                    return col

    # Otherwise, pick first numeric column
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            return col

    return None


def detect_categorical_column(df: pd.DataFrame, preferred_names=None):
    if preferred_names is None:
        preferred_names = []

    for name in preferred_names:
        for col in df.columns:
            if col.lower().replace(" ", "") == name.lower().replace(" ", ""):
                if not pd.api.types.is_numeric_dtype(df[col]):
                    return col

    # fallback: any non-numeric column
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            return col

    return None


def basic_sales_aggregates(df: pd.DataFrame, date_col: str, sales_col: str, profit_col: str | None = None):
    """Compute basic KPIs and groupings for charts and AI insights."""
    result = {}

    total_sales = df[sales_col].sum()
    result["total_sales"] = float(total_sales)

    if profit_col and profit_col in df.columns:
        total_profit = df[profit_col].sum()
        result["total_profit"] = float(total_profit)
        result["profit_margin"] = float(total_profit / total_sales) if total_sales else 0.0
    else:
        result["total_profit"] = None
        result["profit_margin"] = None

    # Orders count
    result["order_count"] = len(df)

    # Sales over time (by month)
    date_series = pd.to_datetime(df[date_col])
    df["_parsed_date"] = date_series
    monthly = df.groupby(pd.Grouper(key="_parsed_date", freq="M"))[sales_col].sum().reset_index()
    result["monthly_sales"] = monthly

    # Category-wise
    category_col = detect_categorical_column(df, preferred_names=["Category", "Product Category"])
    if category_col:
        cat_sales = df.groupby(category_col)[sales_col].sum().reset_index()
        result["category_col"] = category_col
        result["category_sales"] = cat_sales
    else:
        result["category_col"] = None
        result["category_sales"] = None

    # Region-wise
    region_col = detect_categorical_column(df, preferred_names=["Region", "State"])
    if region_col and region_col != result.get("category_col"):
        region_sales = df.groupby(region_col)[sales_col].sum().reset_index()
        result["region_col"] = region_col
        result["region_sales"] = region_sales
    else:
        result["region_col"] = None
        result["region_sales"] = None

    return result


def aggregates_to_text(agg: dict) -> str:
    """Turn aggregates into a textual summary for the LLM."""
    lines = []
    lines.append(f"Total sales: {agg.get('total_sales'):.2f}")
    if agg.get("total_profit") is not None:
        lines.append(f"Total profit: {agg.get('total_profit'):.2f}")
        lines.append(f"Profit margin: {agg.get('profit_margin'):.2%}")
    lines.append(f"Order count: {agg.get('order_count')}")

    if agg.get("category_col") and agg.get("category_sales") is not None:
        lines.append(f"\nSales by {agg['category_col']}:")
        for _, row in agg["category_sales"].iterrows():
            lines.append(f"- {row[agg['category_col']]}: {row['Sales'] if 'Sales' in row else row.iloc[1]:.2f}")

    if agg.get("region_col") and agg.get("region_sales") is not None:
        lines.append(f"\nSales by {agg['region_col']}:")
        for _, row in agg["region_sales"].iterrows():
            lines.append(f"- {row[agg['region_col']]}: {row['Sales'] if 'Sales' in row else row.iloc[1]:.2f}")

    # Add monthly summary (just last and first)
    monthly = agg.get("monthly_sales")
    if monthly is not None and len(monthly) > 0:
        first = monthly.iloc[0]
        last = monthly.iloc[-1]
        lines.append(
            f"\nMonthly sales start at {first['_parsed_date'].date()} "
            f"with {first['Sales'] if 'Sales' in first else first.iloc[1]:.2f} "
            f"and end at {last['_parsed_date'].date()} "
            f"with {last['Sales'] if 'Sales' in last else last.iloc[1]:.2f}."
        )

    return "\n".join(lines)
