import os
import re
from datetime import *
import numpy as np
import pandas as pd
import pytz

# %%
url = "https://www.arcgis.com/sharing/rest/content/items/f10774f1c63e40168479a1feb6c7ca74/data"
date_latest = datetime.now(pytz.timezone('Europe/Berlin')).date().strftime('%Y-%m-%d')
BV_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Bevoelkerung',
                               'Bevoelkerung.csv')
BV_dtypes = {'AGS': 'str', 'Name': 'str', 'GueltigAb': 'object', 'GueltigBis': 'object', 'Einwohner': 'Int32'}
CV_dtypes = {'Datenstand': 'object', 'IdBundesland': 'str', 'Bundesland': 'str', 'IdLandkreis': 'str',
             'Landkreis': 'str', 'NeuerFall': 'Int8', 'NeuerTodesfall': 'Int8', 'NeuGenesen': 'Int8',
             'AnzahlFall': 'Int32', 'AnzahlTodesfall': 'Int32', 'AnzahlGenesen': 'Int32', 'Meldedatum': 'object'}

# %% open bevoelkerung.csv
BV = pd.read_csv(BV_csv_path, usecols=BV_dtypes.keys(), dtype=BV_dtypes)
BV['GueltigAb'] = pd.to_datetime(BV['GueltigAb'])
BV['GueltigBis'] = pd.to_datetime(BV['GueltigBis'])

# %% load covid latest from web
data_Base = pd.read_csv(url, usecols=CV_dtypes.keys(), dtype=CV_dtypes)
data_Base['IdBundesland'] = data_Base['IdBundesland'].str.zfill(2)

# %% accumulated cases, deaths, recovered
# DistrictsRecoveredData, StatesRecoveredData
LK = data_Base.copy()
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dataStore', 'accumulated')
LK_json_path = os.path.join(path, 'districts.json')
BL_json_path = os.path.join(path, 'states.json')
key_list_LK = ['IdLandkreis' ]
key_list_BL = ['IdBundesland']
LK['Meldedatum'] = pd.to_datetime(LK['Meldedatum']).dt.date
datenstand = pd.to_datetime(LK['Datenstand'].iloc[0], format='%d.%m.%Y, %H:%M Uhr')
LK['Datenstand'] = datenstand.date()
LK['AnzahlFall'] = np.where(LK['NeuerFall'].isin([1, 0]), LK['AnzahlFall'], 0)
LK['AnzahlTodesfall'] = np.where(LK['NeuerTodesfall'].isin([1, 0]), LK['AnzahlTodesfall'], 0)
LK['AnzahlGenesen'] = np.where(LK['NeuGenesen'].isin([1, 0]), LK['AnzahlGenesen'], 0)
LK.drop(['NeuGenesen', 'NeuerFall', 'NeuerTodesfall', 'Bundesland', 'Landkreis'], inplace=True, axis=1)
LK.rename(columns={'AnzahlGenesen': 'recovered', 'AnzahlFall': 'cases', 'AnzahlTodesfall': 'deaths'}, inplace=True)
BL = LK.copy()
LK.drop(['IdBundesland'], inplace=True, axis=1)
BL.drop(['IdLandkreis'], inplace=True, axis=1)
ID0 = BL.copy()
ID0['IdBundesland'] = '00'
agg_key = {
    c: 'max' if c in ['Meldedatum', 'Datenstand'] else 'sum'
    for c in LK.columns
    if c not in key_list_LK
}
LK = LK.groupby(key_list_LK, as_index=False).agg(agg_key)
agg_key = {
    c: 'max' if c in ['Meldedatum', 'Datenstand'] else 'sum'
    for c in BL.columns
    if c not in key_list_BL
}
BL = BL.groupby(key_list_BL, as_index=False).agg(agg_key)
ID0 = ID0.groupby(key_list_BL, as_index=False).agg(agg_key)
BL = pd.concat([ID0, BL])
BL.reset_index(inplace=True, drop=True)

# %% store json files
LK.to_json(LK_json_path, orient="records", date_format="iso", force_ascii=False)
BL.to_json(BL_json_path, orient="records", date_format="iso", force_ascii=False)

# %% New
# DistrictsCases, DistrictsDeaths, DistrictsRecovered
# StatesCases, StatesDeaths, StatesRecovered
LK = data_Base.copy()
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dataStore', 'new')
LK_json_path = os.path.join(path, 'districts.json')
BL_json_path = os.path.join(path, 'states.json')
key_list_LK = ['IdLandkreis' ]
key_list_BL = ['IdBundesland']
LK.drop(['Bundesland', 'Landkreis'], inplace=True, axis=1)
LK['Meldedatum'] = pd.to_datetime(LK['Meldedatum']).dt.date
datenstand = pd.to_datetime(LK['Datenstand'].iloc[0], format='%d.%m.%Y, %H:%M Uhr')
LK['Datenstand'] = datenstand.date()
LK['AnzahlFall'] = np.where(LK['NeuerFall'].isin([1, -1]), LK['AnzahlFall'], 0)
LK['AnzahlTodesfall'] = np.where(LK['NeuerTodesfall'].isin([1, -1]), LK['AnzahlTodesfall'], 0)
LK['AnzahlGenesen'] = np.where(LK['NeuGenesen'].isin([1, -1]), LK['AnzahlGenesen'], 0)
LK.drop(['NeuerFall','NeuerTodesfall','NeuGenesen'], inplace=True, axis=1)
LK.rename(columns={'AnzahlFall': 'cases', 'AnzahlTodesfall': 'deaths', 'AnzahlGenesen': 'recovered'}, inplace=True)
BL = LK.copy()
BL.drop(['IdLandkreis'], inplace=True, axis=1)
LK.drop(['IdBundesland'], inplace=True, axis=1)
ID0 = BL.copy()
ID0['IdBundesland'] = '00'
agg_key = {
    c: 'max' if c in ['Meldedatum', 'Datenstand'] else 'sum'
    for c in LK.columns
    if c not in key_list_LK
}
LK = LK.groupby(key_list_LK, as_index=False).agg(agg_key)
agg_key = {
    c: 'max' if c in ['Meldedatum', 'Datenstand'] else 'sum'
    for c in BL.columns
    if c not in key_list_BL
}
BL = BL.groupby(key_list_BL, as_index=False).agg(agg_key)
ID0 = ID0.groupby(key_list_BL, as_index=False).agg(agg_key)
BL = pd.concat([ID0, BL])
BL.reset_index(inplace=True, drop=True)

# %% store json files
LK.to_json(LK_json_path, orient="records", date_format="iso", force_ascii=False)
BL.to_json(BL_json_path, orient="records", date_format="iso", force_ascii=False)

# %% History
# DistrictCasesHistory, DistrictDeathsHistory, DistrictRecoveredHistory
# StateCasesHistory, StateDeathsHistory, StateRecoveredHistory
LK = data_Base.copy()
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dataStore', 'history')
LK_json_path = os.path.join(path, 'districts.json')
BL_json_path = os.path.join(path, 'states.json')
key_list_LK = ['IdLandkreis', 'Meldedatum']
key_list_BL = ['IdBundesland', 'Meldedatum']
LK['Meldedatum'] = pd.to_datetime(LK['Meldedatum']).dt.date
datenstand = pd.to_datetime(LK['Datenstand'].iloc[0], format='%d.%m.%Y, %H:%M Uhr')
LK['Datenstand'] = datenstand.date()
LK['AnzahlFall'] = np.where(LK['NeuerFall'].isin([1, 0]), LK['AnzahlFall'], 0)
LK['AnzahlTodesfall'] = np.where(LK['NeuerTodesfall'].isin([1, 0, -9]), LK['AnzahlTodesfall'], 0)
LK['AnzahlGenesen'] = np.where(LK['NeuGenesen'].isin([1, 0, -9]), LK['AnzahlGenesen'], 0)
LK.drop(['NeuerFall','NeuerTodesfall','NeuGenesen'], inplace=True, axis=1)
LK.rename(columns={'AnzahlFall': 'cases', 'AnzahlTodesfall': 'deaths', 'AnzahlGenesen': 'recovered'}, inplace=True)
BL = LK.copy()
BL.drop(['IdLandkreis', 'Landkreis'], inplace=True, axis=1)
LK.drop(['IdBundesland', 'Bundesland'], inplace=True, axis=1)
ID0 = BL.copy()
ID0['IdBundesland'] = '00'
ID0['Bundesland'] = 'Bundesgebiet'
agg_key = {
    c: 'max' if c in ['Datenstand', 'Landkreis'] else 'sum'
    for c in LK.columns
    if c not in key_list_LK
}
LK = LK.groupby(key_list_LK, as_index=False).agg(agg_key)
agg_key = {
    c: 'max' if c in ['Datenstand', 'Bundesland'] else 'sum'
    for c in BL.columns
    if c not in key_list_BL
}
BL = BL.groupby(key_list_BL, as_index=False).agg(agg_key)
ID0 = ID0.groupby(key_list_BL, as_index=False).agg(agg_key)
BL = pd.concat([ID0, BL])
BL.reset_index(inplace=True, drop=True)

# %% store json files
LK.to_json(LK_json_path, orient="records", date_format="iso", force_ascii=False)
BL.to_json(BL_json_path, orient="records", date_format="iso", force_ascii=False)

# %% fixed-incidence
LK = data_Base.copy()
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dataStore', 'frozen-incidence')
LK_json_path = os.path.join(path, 'frozen-incidence_' + date_latest + '_LK.json')
BL_json_path = os.path.join(path, 'frozen-incidence_' + date_latest + '_BL.json')
key_list_LK = ['IdLandkreis']
key_list_BL = ['IdBundesland']
LK['Meldedatum'] = pd.to_datetime(LK['Meldedatum']).dt.date
datenstand = pd.to_datetime(LK['Datenstand'].iloc[0], format='%d.%m.%Y, %H:%M Uhr')
LK['AnzahlFall_neu'] = np.where(LK['NeuerFall'].isin([-1, 1]), LK['AnzahlFall'], 0)
LK['AnzahlFall'] = np.where(LK['NeuerFall'].isin([0, 1]), LK['AnzahlFall'], 0)
LK['AnzahlFall_7d'] = np.where(LK['Meldedatum'] > (datenstand - timedelta(days=8)), LK['AnzahlFall'], 0)
LK['Datenstand'] = datenstand.date()
LK.drop(['NeuerFall', 'NeuerTodesfall', 'AnzahlFall', 'AnzahlTodesfall', 'AnzahlFall_neu', 'Landkreis', 'Bundesland', 'NeuGenesen', 'AnzahlGenesen'], inplace=True, axis=1)
BL = LK.copy()
BL.drop(['IdLandkreis'], inplace=True, axis=1)
LK.drop(['IdBundesland'], inplace=True, axis=1)
ID0 = BL.copy()
ID0['IdBundesland'] = '00'
agg_key = {
    c: 'max' if c in ['Meldedatum', 'Datenstand'] else 'sum'
    for c in LK.columns
    if c not in key_list_LK
}
LK = LK.groupby(key_list_LK, as_index=True).agg(agg_key)
agg_key = {
    c: 'max' if c in ['Meldedatum', 'Datenstand'] else 'sum'
    for c in BL.columns
    if c not in key_list_BL
}
BL = BL.groupby(key_list_BL, as_index=True).agg(agg_key)
ID0 = ID0.groupby(key_list_BL, as_index=True).agg(agg_key)
BL = pd.concat([ID0, BL])
BL.drop(['Meldedatum'], inplace=True, axis=1)
LK.drop(['Meldedatum'], inplace=True, axis=1)
LK.sort_values(by=key_list_LK, inplace=True)
BL.sort_values(by=key_list_BL, inplace=True)
LK_pop_mask = (BV['AGS'].isin(LK.index)) & (BV['GueltigAb'] <= datenstand) & (BV['GueltigBis'] >= datenstand)
LK_pop = BV[LK_pop_mask]
LK_pop.set_index(['AGS'], inplace=True, drop=True)
LK['population'] = LK_pop['Einwohner']
LK.insert(loc=0, column='Landkreis', value=LK_pop['Name'])
LK['AnzahlFall_7d'] = LK['AnzahlFall_7d'].astype(int)
LK['incidence_7d'] = LK['AnzahlFall_7d'] / LK['population'] * 100000
LK.drop(['population'], inplace=True, axis=1)
BL_pop_mask = (BV['AGS'].isin(BL.index)) & (BV['GueltigAb'] <= datenstand) & (BV['GueltigBis'] >= datenstand)
BL_pop = BV[BL_pop_mask]
BL_pop.set_index(['AGS'], inplace=True, drop=True)
BL['population'] = BL_pop['Einwohner']
BL.insert(loc=0, column='Bundesland', value=BL_pop['Name'])
BL['AnzahlFall_7d'] = BL['AnzahlFall_7d'].astype(int)
BL['incidence_7d'] = BL['AnzahlFall_7d'] / BL['population'] * 100000
BL.drop(['population'], inplace=True, axis=1)

# %% store json files
LK.to_json(LK_json_path, orient="index", date_format="iso", force_ascii=False)
BL.to_json(BL_json_path, orient="index", date_format="iso", force_ascii=False)

# %% limit frozen-incidence files to the last 10 days
iso_date_re = '([0-9]{4})(-?)(1[0-2]|0[1-9])\\2(3[01]|0[1-9]|[12][0-9])'
file_list = os.listdir(path)
file_list.sort(reverse=False)
pattern = 'FixFallzahlen'
all_files = []
for file in file_list:
    file_path_full = os.path.join(path, file)
    if not os.path.isdir(file_path_full):
        filename = os.path.basename(file)
        re_filename = re.search(pattern, filename)
        re_search = re.search(iso_date_re, filename)
        if re_search and re_filename:
            report_date = date(int(re_search.group(1)), int(re_search.group(3)), int(re_search.group(4))).strftime('%Y-%m-%d')
            all_files.append((file_path_full, report_date))
day_range = pd.date_range(end=datetime.today(), periods=10).tolist()
day_range_str = []
for datum in day_range:
    day_range_str.append(datum.strftime('%Y-%m-%d'))
for file_path_full, report_date in all_files:
    if report_date not in day_range_str:
        os.remove(file_path_full)
