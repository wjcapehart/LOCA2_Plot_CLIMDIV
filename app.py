##########################################################
#
# Libraries
#

import seaborn           as sns
import pyreadr           as pyreadr
import pandas            as pd 
import matplotlib.pyplot as plt
import io
import urllib.request
import calendar

from   shiny         import reactive
from   shiny.express import input, render, ui

#
##########################################################



##########################################################
#
# Initial Read of Cliamte Division by State LUT
#

app_dir = "./"
df_climdivs = pd.read_csv("./NCEI_nClimDiv_LUT.csv")

states_list = df_climdivs["State_Selector"].unique().tolist()

for state in states_list:
    climdivs_in_state = {state:df_climdivs[df_climdivs["State_Selector"] == state]["Climate_Division_Selector"].tolist()}
    if (state == states_list[0]):
        climdiv_by_state = climdivs_in_state
    else:
        climdiv_by_state.update(climdivs_in_state)

# 
##########################################################


##########################################################
#
# Custom Color Tables for SSP Scenarios
#

# SSP Scenarios

SSP_Scenarios  = ["Historical", 
                  "SSP2-4.5",
                  "SSP3-7.0",
                  "SSP5-8.5"]

# Colors (scenarios)

SSP_Colors     = [       "blue", # Historical  
                  "forestgreen", # SSP2-4.5
                    "goldenrod", # SSP3-7.0
                    "firebrick"] # SSP5-8.5

# Bundle Colors into a Dictionary 

SSP_Colors_dict     = dict(zip(SSP_Scenarios,SSP_Colors))

# 
##########################################################

##########################################################
#
# Time Periods for Historical and Future Extraction
#

# Past Period

historical_period        = [1981, 2010]
historical_period_string = str(historical_period[0]) + "-" + \
                           str(historical_period[1])

# Future Periods

future_years = {"2036-2065": [2036, 2065],
                "2070-2099": [2070, 2099]}
# 
##########################################################


##########################################################
#
# User Interface Area
#

#
# Page Options
#

ui.page_opts(title="LOCA2 Plotting Test")

#
# Sidebar
#

with ui.sidebar():
    ui.input_select(id       = "state_selection", 
                    label    = "Select State", 
                    choices  = list(climdiv_by_state.keys()), 
                    selected = "39 South Dakota")
    ui.input_select(id       = "climdiv_selection", 
                    label    = "Select Climate Division", 
                    choices  = []) # selected = "3904 Black Hills")
    ui.input_select(id       = "var", 
                    label    = "Select Variable", 
                    choices  = ["tasmin", "tasavg", "tasmax", "pr"],
                    selected = "tasavg")
    ui.input_select(id       = "period_selection", 
                    label    = "Select Future Period", 
                    choices  = list(future_years.keys()), 
                    selected = "2036-2065")

#
# Reactive Elements
#

@reactive.effect
def update_climdiv_selection():
    ###################################
    #
    # Update Climate Division Selections from State Selection
    #

    # Grab the selected State
    selected_state = input.state_selection()
    # Get corresponding divisions for that State
    new_choices = climdiv_by_state.get(selected_state, [])
    # Dynamically update the Climate Selection input control
    ui.update_select(id      =  "climdiv_selection", 
                     choices =          new_choices)

    #
    ###################################


@reactive.calc
def df_loca2_monthy():
    ###################################
    #
    # Retrieve Monthly LOCA2 DataFrame
    #

    selected_climdiv = input.climdiv_selection()
    climdiv_key = selected_climdiv.split()[0]
    print(" -->", climdiv_key)
    url = "https://thredds.ias.sdsmt.edu:8443/thredds/fileServer/LOCA2/Specific_Regional_Aggregate_Sets/NCEI_Climate_Divisions/R_Monthly_Files/LOCA2_V1_nCLIMDIV_MONTHLY_" + climdiv_key + ".RData"#?raw=true"
    response = urllib.request.urlopen(url)
    result = pyreadr.read_r(io.BytesIO(response.read()))
    df_loca2_monthy = result['loca2_monthly']
    df_loca2_monthy = df_loca2_monthy[df_loca2_monthy["Percentile"]=="MEAN"]
    df_loca2_monthy["tasavg"] = (df_loca2_monthy["tasmax"] + df_loca2_monthy["tasmin"]) /2
    df_loca2_monthy['Scenario'] = pd.Categorical(df_loca2_monthy['Scenario'], 
                                                 categories = SSP_Scenarios, 
                                                 ordered    =   True)
    calmon = list(calendar.month_abbr)[1:]
    df_loca2_monthy['Month'] = df_loca2_monthy['Month'].astype(int)
    df_loca2_monthy['Month'] = df_loca2_monthy['Month'].map(lambda x: calendar.month_abbr[x])
    df_loca2_monthy['Month'] = pd.Categorical(df_loca2_monthy['Month'], 
                                              categories=calmon, 
                                              ordered=True)
    df_loca2_monthy = df_loca2_monthy[((df_loca2_monthy["Year"] >= historical_period[0]) & (df_loca2_monthy["Year"] <= historical_period[1])) |
                                      ((df_loca2_monthy["Year"] >= future_years[input.period_selection()][0]) & (df_loca2_monthy["Year"] <= future_years[input.period_selection()][1])) ]
    
    df_loca2_monthy = df_loca2_monthy.groupby(["Scenario","Month","Model"]).agg({'tasmax':'mean',
                                                              'tasavg':'mean',
                                                               'tasmin':'mean',
                                                               'pr':    'mean'}).reset_index()
    return df_loca2_monthy

    #
    ###################################

@reactive.calc
def df_loca2_annual():
    ###################################
    #
    # Retrieve Annual LOCA2 DataFrame
    #

    selected_climdiv = input.climdiv_selection()
    climdiv_key = selected_climdiv.split()[0]
    print(" -->", climdiv_key)
    url = "https://thredds.ias.sdsmt.edu:8443/thredds/fileServer/LOCA2/Specific_Regional_Aggregate_Sets/NCEI_Climate_Divisions/R_Annual_Files/LOCA2_V1_nCLIMDIV_ANNUAL_" + climdiv_key + ".RData"#?raw=true"
    response = urllib.request.urlopen(url)
    result = pyreadr.read_r(io.BytesIO(response.read()))
    df_loca2_annual = result['loca2_annual']
    df_loca2_annual = df_loca2_annual[df_loca2_annual["Percentile"]=="MEAN"]
    df_loca2_annual['Scenario'] = pd.Categorical(df_loca2_annual['Scenario'], 
                                                 categories = SSP_Scenarios, 
                                                 ordered    =   True)

    df_loca2_annual["tasavg"] = (df_loca2_annual["tasmax"] + df_loca2_annual["tasmin"]) /2

    return df_loca2_annual

    #
    ###################################

# 
##########################################################










@render.plot
def annual_plot():

    my_metadata = df_climdivs[df_climdivs["Climate_Division_Selector"]==input.climdiv_selection()]


    climdiv_string = "CMIP6-LOCA2 Downscaled Climate Ensembles\n" + \
                     my_metadata["climdiv_name"].values[0]       + \
                     ", "                                           + \
                     my_metadata["climdiv_state_name"].values[0]    + \
                     " ("                                           + \
                     str(my_metadata["climdiv"].values[0]).zfill(4) + \
                     ") NCEI Climate Division"


    yaxes_labels = {"tasmax": "2-m Mean Daily Maximum Temperature (°C)",
                    "tasavg": "2-m Mean Temperature (°C)",
                    "tasmin": "2-m Mean Daily Minimum Temperature (°C)",
                    "pr"    : "2-m Annual Total Precipitation (mm)"}


    sns.lineplot(data     = df_loca2_annual(),
                 y        = input.var(),
                 x        = "Year",
                 hue      = "Scenario",
                 palette  = SSP_Colors_dict,
                 errorbar = ("pi", 50))
    plt.title(climdiv_string, loc='left')
    plt.ylabel(yaxes_labels[input.var()])
    plt.axvspan(xmin  = historical_period[0], 
                xmax  = historical_period[1], 
                color = 'lightgrey',
                alpha = 0.25)
    plt.axvspan(xmin  = future_years[input.period_selection()][0], 
                xmax  = future_years[input.period_selection()][1], 
                color = 'lightgrey',
                alpha = 0.25)


@render.plot
def monthly_plot():

    my_metadata = df_climdivs[df_climdivs["Climate_Division_Selector"]==input.climdiv_selection()]


    climdiv_string = "CMIP6-LOCA2 Downscaled Climate Ensembles " + \
                     "(" + historical_period_string + ") vs (" + input.period_selection() + ")" + \
                     "\n" + \
                     my_metadata["climdiv_name"].values[0]          + \
                     ", "                                           + \
                     my_metadata["climdiv_state_name"].values[0]    + \
                     " ("                                           + \
                     str(my_metadata["climdiv"].values[0]).zfill(4) + \
                     ") NCEI Climate Division"


    yaxes_labels = {"tasmax": "2-m Mean Daily Maximum Temperature (°C)",
                    "tasavg": "2-m Mean Temperature (°C)",
                    "tasmin": "2-m Mean Daily Minimum Temperature (°C)",
                    "pr"    : "2-m Monthly Total Precipitation (mm)"}

    sns.lineplot(data     = df_loca2_monthy(),
                 y        = input.var(),
                 x        = "Month",
                 hue      = "Scenario",
                 palette  = SSP_Colors_dict,
                 errorbar = ("pi", 50))
    plt.title(climdiv_string, loc='left')
    plt.ylabel(yaxes_labels[input.var()])

 
