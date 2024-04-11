import streamlit as st
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go

from all_together import join


st.write("# ADP Payslips Reader")

st.write("Convert your payslips into usable CSVs. You can download any table.")
st.write("""
The file names must have a format `YYYY_MM.pdf`. You can run something
like:
```sh
for file in payslips/*; do mv "$file" "payslips/$(basename $file | cut -d'_' -f 2,3).pdf"; done
```
in order to format all the files under the "payslips" folder.
""")
uploaded_files = st.file_uploader(
    "Choose one or more payslips (PDF format)", accept_multiple_files=True)
payslips = []
payslisps_filenames = []
for uploaded_file in uploaded_files:
    payslips.append(BytesIO(uploaded_file.read()))
    payslisps_filenames.append(uploaded_file.name)

if len(payslips) > 0:
    st.write(f"Found {len(payslips)} payslips")
    main_concepts_df, bases_df, totales_df = join(payslips, payslisps_filenames)

    st.write("## Totales")
    col1, col2 = st.columns(2)
    col1.dataframe(totales_df)

    bars = px.bar(totales_df, y = ["devengos", "deducciones"], barmode='group')
    line = px.line(totales_df, y = ["liquido_a_recibir"])
    line.update_traces(line=dict(color='black', dash='dash'))
    fig = go.Figure(data = bars.data + line.data)
    col2.plotly_chart(fig)


    st.write("## Main concepts")
    st.dataframe(main_concepts_df)


    st.write("## Bases")
    st.dataframe(bases_df)
