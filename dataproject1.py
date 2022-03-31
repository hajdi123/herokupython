import pandas as pd
import altair as alt
import numpy as np
import wget
# url of the raw csv dataset
urls = [
    'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv',
    'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv',
    'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'
]
[wget.download(url) for url in urls]

confirmed = pd.read_csv('time_series_covid19_confirmed_global.csv')
deaths = pd.read_csv('time_series_covid19_deaths_global.csv')
recovered = pd.read_csv('time_series_covid19_recovered_global.csv')

confirmed = confirmed.drop(columns = ['3/27/22','3/28/22','3/29/22'])

dates = confirmed.columns[4:]
confirmed_long = confirmed.melt(
    id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'], 
    value_vars=dates, 
    var_name='Date', 
    value_name='Confirmed'
)
deaths_long = deaths.melt(
    id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'], 
    value_vars=dates, 
    var_name='Date', 
    value_name='Deaths'
)
recovered_long = recovered.melt(
    id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'], 
    value_vars=dates, 
    var_name='Date', 
    value_name='Recovered'
)

recovered_long = recovered_long[recovered_long['Country/Region']!='Canada']

# Merging confirmed_df_long and deaths_df_long
full_table = confirmed_long.merge(
  right=deaths_long, 
  how='left',
  on=['Province/State', 'Country/Region', 'Date', 'Lat', 'Long']
)
# Merging full_table and recovered_df_long
full_table = full_table.merge(
  right=recovered_long, 
  how='left',
  on=['Province/State', 'Country/Region', 'Date', 'Lat', 'Long']
)

full_table['Date'] = pd.to_datetime(full_table['Date'])

full_table['Recovered'] = full_table['Recovered'].fillna(0)

ship_rows = full_table['Province/State'].str.contains('Grand Princess') | full_table['Province/State'].str.contains('Diamond Princess') | full_table['Country/Region'].str.contains('Diamond Princess') | full_table['Country/Region'].str.contains('MS Zaandam')
full_ship = full_table[ship_rows]

full_table = full_table[~(ship_rows)]

full_table['Active'] = full_table['Confirmed'] - full_table['Deaths'] - full_table['Recovered']

full_grouped = full_table.groupby(['Date', 'Country/Region'])['Confirmed', 'Deaths', 'Recovered', 'Active'].sum().reset_index()

# new cases 
temp = full_grouped.groupby(['Country/Region', 'Date', ])['Confirmed', 'Deaths', 'Recovered']
temp = temp.sum().diff().reset_index()
mask = temp['Country/Region'] != temp['Country/Region'].shift(1)
temp.loc[mask, 'Confirmed'] = np.nan
temp.loc[mask, 'Deaths'] = np.nan
temp.loc[mask, 'Recovered'] = np.nan
# renaming columns
temp.columns = ['Country/Region', 'Date', 'New cases', 'New deaths', 'New recovered']
# merging new values
full_grouped = pd.merge(full_grouped, temp, on=['Country/Region', 'Date'])
# filling na with 0
full_grouped = full_grouped.fillna(0)
# fixing data types
cols = ['New cases', 'New deaths', 'New recovered']
full_grouped[cols] = full_grouped[cols].astype('int')
# 
full_grouped['New cases'] = full_grouped['New cases'].apply(lambda x: 0 if x<0 else x)

full_grouped.to_csv('COVID-19-time-series-clean-complete.csv')



brush = alt.selection_interval()

url = 'full_grouped.json'
full_grouped.to_json(url, orient='records')




import streamlit as st
import altair as alt
import pandas as pd 
from vega_datasets import data

covid = pd.read_csv('COVID-19-time-series-clean-complete.csv')
covid =covid.rename(columns={"Country/Region": "Country"}, errors="raise")




st.title('🦠 Covid-19 Dashborad 🦠 ')
st.sidebar.markdown('🦠 **Covid-19 Dashborad** 🦠 ')
st.sidebar.markdown(''' 
This app is to give insights about Covid-19 Infections around the world.
The data considerd for this analysis for 10 Months starting from 01-02-2020 to 30-11-2020
Select the different options to vary the Visualization
All the Charts are interactive. 
Scroll the mouse over the Charts to feel the interactive features like Tool tip, Zoom, Pan
                    
''')  

st.header("Select the Country to Visualize the Covid-19 Cases")
    
cty = st.selectbox("Select country",covid["Country"][:186])



st.header(f"View Daily New Cases/Recoveries/Deaths for {cty}")
daily = st.selectbox("Select the option",('Daily New Cases', 'Daily New Recoveries','Daily New Deaths'))
typ = st.radio("Select the type of Chart",("Line Chart","Scatter Chart"))

ca = alt.Chart(covid[covid["Country"]==cty]).encode(
    x="Date",
    y="New cases",
    tooltip=["Date","Country","New cases"]
).interactive()

re = alt.Chart(covid[covid["Country"]==cty]).encode(
    x="Date",
    y="New recovered",
    tooltip=["Date","Country","New recovered"]
).interactive()

de = alt.Chart(covid[covid["Country"]==cty]).encode(
    x="Date",
    y="New deaths",
    tooltip=["Date","Country","New deaths"]
).interactive()


cas= alt.Chart(covid[covid["Country"]==cty],title="Scatter Chart",width=500,height=400).mark_circle(color='green').encode(
    x="Date",
    y="New cases",
    size="New deaths",
    color="New recovered",
    tooltip=["Date","Country","New cases","New deaths","New recovered"]
).interactive()


if daily =='Daily New Cases':
    if typ == "Line Chart":
        st.altair_chart(ca.mark_line(color='firebrick'))
    else:
        st.altair_chart(ca.mark_circle(color='firebrick'))
elif daily =='Daily New Recoveries':
    if typ == "Line Chart":
        st.altair_chart(re.mark_line(color='green'))
    else:
        st.altair_chart(re.mark_circle(color='green'))
elif daily =='Daily New Deaths':
    if typ == "Line Chart":
        st.altair_chart(de.mark_line(color='purple'))
    else:
        st.altair_chart(de.mark_circle(color='purple'))
