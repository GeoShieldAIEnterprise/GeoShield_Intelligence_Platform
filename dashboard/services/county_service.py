import pandas as pd

DATA = "dashboard/data/county_master_intelligence.csv"

df = pd.read_csv(DATA)


def dashboard_summary():

    return {
        "counties": len(df),

        "highest_drought":
            df.sort_values(
                "Drought_Risk",
                ascending=False
            ).iloc[0].to_dict(),

        "highest_rainfall":
            df.sort_values(
                "Rainfall_mm",
                ascending=False
            ).iloc[0].to_dict(),

        "highest_temperature":
            df.sort_values(
                "Temperature_C",
                ascending=False
            ).iloc[0].to_dict()
    }


def all_counties():

    return df.to_dict("records")


def county(name):

    row = df[df["County"].str.lower() == name.lower()]

    if row.empty:
       return {
        "error": "County not found"
    }
    return row.iloc[0].to_dict()
