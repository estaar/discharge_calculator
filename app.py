import pandas as pd
import streamlit as st
from io import BytesIO

st.set_page_config(
    page_title="Discharge Calculator",
    page_icon="random",
    layout="centered",
)

# Sidebar Header
st.sidebar.header("Select Excel File")

# Sidebar Select File
uploaded_file = st.sidebar.file_uploader(
    "Select Your Data File", type=["csv", "txt", "xlsx"], accept_multiple_files=False
)

output = BytesIO()
writer = pd.ExcelWriter(output, engine='xlsxwriter')


def write_to_excel(sheets_names):
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

            discharge = a * (record_wl + h0) ** b

        else:
            discharge = None

        return discharge

    for sheet_name in sheets_names:
        df = pd.read_excel(xls, sheet_name, skiprows=2, names=['Date_Time', 'Water_Level'], header=None, index_col=None)
        # df = df.head(200)
        df['Water_Level'] = df['Water_Level'].apply(lambda x: round(x, 6))
        df['Discharge'] = df.apply(calculate_discharge, axis=1)
        df['Date_Time'] = df['Date_Time'].astype('datetime64[ns]')
        df['Date'] = df['Date_Time'].dt.date
        start_date = df.Date.min()
        end_date = df.Date.max()
        df = df.groupby('Date')[['Discharge', 'Water_Level']].mean().reset_index()
        df = (df.set_index('Date')
              .reindex(pd.date_range(start_date, end_date, freq='D'))
              .rename_axis(['Date'])
              .reset_index())
        df['Date'] = df['Date'].dt.date

        df.to_excel(writer, sheet_name=sheet_name, index=False)
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
    writer.save()


if uploaded_file is not None:
    st.write(f"Data File {uploaded_file.name} uploaded successfully")
    xls = pd.ExcelFile(uploaded_file)
    rating_curve = pd.read_excel(xls, 'Rating Curves', )
    sheet_names = xls.sheet_names
    sheet_names = [name for name in sheet_names if name != 'Rating Curves']

    write_to_excel(sheet_names)

    st.download_button(
        label="📥 Download Excel workbook",
        data=output.getvalue(),
        file_name="Calculated Discharge.xlsx",
        mime="application/vnd.ms-excel"
    )

else:
    st.write("No file uploaded. Please upload a file")
