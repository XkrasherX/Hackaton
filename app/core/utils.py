import pandas as pd


def merge_gps_coordinates(gps_df, east, north, up):
    gps_df = gps_df.copy()
    gps_df["east"] = east
    gps_df["north"] = north
    gps_df["up"] = up
    return gps_df


def export_csv(df, filename="flight_data.csv"):
    df.to_csv(filename, index=False)