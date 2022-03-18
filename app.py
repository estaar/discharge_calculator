import pandas as pd

xls = pd.ExcelFile('1JA02 Data for JE_20220314.xlsx')
sheet_names = xls.sheet_names
sheet_names = [name for name in sheet_names if name != 'Rating Curves']
print(sheet_names)

rating_curve = pd.read_excel(xls, 'Rating Curves', )


def calculate_discharge(row):
    rating_curve_date = rating_curve[(rating_curve.ID == sheet_name)]
    end_date_max = rating_curve_date.EDATE.max()
    start_date_min = rating_curve_date.SDATE.min()

    record_date = row.Date_Time
    record_wl = row.Water_Level

    if record_date > end_date_max:
        rates = rating_curve_date[(rating_curve_date.EDATE == end_date_max)]
    elif record_date < start_date_min:
        rates = rating_curve_date[(rating_curve_date.SDATE == start_date_min)]
    else:
        rates = rating_curve_date[
            (record_date >= rating_curve_date.SDATE) &
            (record_date <= rating_curve_date.EDATE) &
            (record_wl >= rating_curve_date.LWL) &
            (record_wl < rating_curve_date.HWL)]

    if len(rates) > 0:
        a = rates.A_CONST.values[0]
        b = rates.B_CONST.values[0]
        h0 = rates.Dho.values[0]

        discharge = a * (record_wl - h0) ** b

    else:
        discharge = None

    return discharge


for sheet_name in sheet_names:
    df = pd.read_excel(xls, sheet_name, skiprows=2, names=['Date_Time', 'Water_Level'], header=None, index_col=None)
    df = df.head(200)
    df['Water_Level'] = df['Water_Level'].apply(lambda x: round(x, 6))

    df['Discharge'] = df.apply(calculate_discharge, axis=1)
    df['Date_Time'] = df['Date_Time'].astype('datetime64[ns]')
    df['Date'] = df['Date_Time'].dt.date

    df = df.groupby('Date')[['Discharge', 'Water_Level']].mean().reset_index()
    with pd.ExcelWriter('output.xlsx', engine="openpyxl", mode='a', if_sheet_exists="replace", ) as writer:
        df.to_excel(writer, sheet_name=sheet_name)
