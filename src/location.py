import re

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


US_STATE_NAME_TO_CODE = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
    "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    "District of Columbia": "DC", "Puerto Rico": "PR",
}
# geocoder country name -> spelling already used in students.address.country
FORMATTED_COUNTRY_ALIASES = {
    "USA": "United States",
    "US": "United States",
    "China": "China, Peoples Republic of",
    "South Korea": "Korea, South",
}


def parse_formatted_location(s):
    """Parse a geocoded address string like '314 E White St #304, Champaign, IL 61820, USA'.

    Returns a dict with whichever of city/state/zip/country could be read; {} if nothing.
    Non-US strings only give `country`.
    """
    if not isinstance(s, str) or not s.strip() or s.strip() == "NOTFOUND":  # geocoder failure sentinel
        return {}
    parts = [p.strip() for p in s.split(",") if p.strip()]
    # some non-US strings end with a postal code after the country (e.g. '..., China, 100080')
    if len(parts) > 1 and re.fullmatch(r"[\d\s-]+", parts[-1]):
        parts = parts[:-1]

    country = FORMATTED_COUNTRY_ALIASES.get(parts[-1], parts[-1])
    out = {"country": country}
    rest = parts[:-1]
    if country != "United States":
        return out  # non-US address formats vary too much to pick out the city reliably

    if not rest:
        return out
    m = re.fullmatch(r"([A-Z]{2})(?:\s+(\d{5}(?:-\d{4})?))?", rest[-1])
    if m:
        out["state"] = m.group(1)
        if m.group(2):
            out["zip"] = m.group(2)
    elif rest[-1] in US_STATE_NAME_TO_CODE:
        out["state"] = US_STATE_NAME_TO_CODE[rest[-1]]
    else:
        return out  # can't tell which part is the state -> don't guess the city either
    if len(rest) >= 2:
        out["city"] = rest[-2]
    return out


def fill_location_from_formatted(df):
    """Fill missing city/state/zip/country from formatted_location. Existing values are never overwritten.

    Adds `location_filled` = True on rows where at least one field was filled.
    """
    df = df.copy()
    parsed = df["formatted_location"].map(parse_formatted_location)
    df["location_filled"] = False
    for field in ["city", "state", "zip", "country"]:
        value = parsed.map(lambda d: d.get(field))
        fill = df[field].isna() & value.notna()
        df.loc[fill, field] = value[fill]
        df.loc[fill, "location_filled"] = True
    return df
