import pandas as pd

# 50 states + DC, territories (PR, GU, VI, AS, MP) and military mail (AA, AE, AP)
US_STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
    "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT",
    "VA", "WA", "WV", "WI", "WY", "DC",
    "PR", "GU", "VI", "AS", "MP", "AA", "AE", "AP",
}
STATE_NAME_TO_CODE = {"Illinois": "IL"}  # full names found in the data


def extract_address_field(addr, field):
    if isinstance(addr, dict):
        value = addr.get(field)
        if isinstance(value, str):
            return value.strip() or None  # treat '' as missing
        return value
    return None


def add_location_columns(df):
    """Flatten students.address / students.location into street/city/state/zip/country/formatted_location.

    Same logic as 02_location_and_grades.ipynb section 2.
    """
    df = df.copy()
    for field in ["street", "city", "state", "zip"]:
        df[field] = df["address"].apply(lambda a: extract_address_field(a, field))
    country_raw = df["address"].apply(lambda a: extract_address_field(a, "country"))

    df["formatted_location"] = df["location"].apply(
        lambda loc: loc.get("formatted") if isinstance(loc, dict) else None
    )

    df["state"] = df["state"].replace(STATE_NAME_TO_CODE)

    # fill "United States" only if state is a US state
    is_us = df["state"].isin(US_STATE_CODES)
    df["country"] = country_raw.where(country_raw.notna(), pd.Series("United States", index=df.index).where(is_us))
    return df
