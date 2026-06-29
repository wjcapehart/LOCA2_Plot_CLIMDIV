


##########################################################
#
# Libraries
#

import seaborn           as sns
import pyreadr           as pyreadr
import pandas            as pd 
import matplotlib.pyplot as plt
import numpy             as np
import xarray            as xr
import xclim             as xclim
import cf_xarray         as cf_xarray
import cftime            as cftime
import io
import urllib.request
import socket



from   shiny.types   import ImgData
from   shiny         import reactive, App, render, ui  

#
##########################################################

##########################################################
#
# Remote vs Local Access
#

hostname = socket.gethostname()
if (hostname == "kyrill"):
    use_url = False
else:
    use_url = True
print("===============")
print(" hostname :", hostname)
print("  use_url :", use_url)
print("===============")

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
# Index List
#

print("##########################################################")
print("#")
print("####### Initial Read of Climate Index Lookup Table #######")
print("#")

df_climate_indicies = pd.read_csv(filepath_or_buffer = "./Climate_Indicies.csv")

print(" DataFrame for Climate Index Information")
print(df_climate_indicies)

menu_index_list = list(df_climate_indicies["selected_index"].values)

print("print available indicies",menu_index_list)

print("#")
print("####### Initial Read of Climate Index Lookup Table #######")
print("##########################################################")


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
# Customized Plotting and Text Parameters
#

custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", rc=custom_params)

# 
##########################################################


##########################################################
#
# App User Interface
#

app_ui = ui.page_sidebar(

 

    ui.sidebar(

        ui.input_select(id       = "state_selection", 
                        label    = "US State", 
                        choices  = list(climdiv_by_state.keys()), 
                        selected = "39 South Dakota"),

        ui.input_select(id       = "climdiv_selection", 
                        label    = "State Climate Division", 
                        choices  = []), # selected = "3904 Black Hills"),

        ui.input_select(id       = "selected_index", 
                        label    = "Climate Index", 
                        choices  = menu_index_list), #,
                        #selected = menu_index_list[0]),

        ui.input_select(id       = "period_selection", 
                        label    = "Select Future Period", 
                        choices  = list(future_years.keys()), 
                        selected = "2036-2065"),
        ui.p("State Climate Zone Map"),
        ui.output_plot(id        = "state_zone_map"),

        title = "User Control",
        lang = "en",

    ),

        ui.card( 

        ui.p("All plots are made to order from raw inputs and subsequent calculations. Please be patient."),
        ui.p("New indicies are also slowly being added."),

    ),

    ui.br(),

 
    ui.card(
      ui.card_header("Annual Time Series Plot"),
      ui.output_plot("annual_plot"),
    ),

    ui.br(),

    ui.card(
      ui.card_header("Monthly Period Plot"),
      ui.output_plot("monthly_plot"),
    ),

    ui.br(),

    ui.card(
      ui.card_header("Index Description"),
      ui.output_text("index_description"),
    ),

    ui.br(),


    ui.card( 
        ui.card_header("Download"),

        ui.p("Download as a comma-delimited file (CSV)"),
        ui.download_button(id = "annual_download_btn", 
                           label = "Download Annual Data (CSV)"),
        ui.download_button(id = "monthly_download_btn", 
                           label = "Download Monthly Data (CSV)"),
    ),
    
    ui.br(),

    ui.card(

        ui.card_header("About This Display"),

        ui.p("This display shows a various climate metrics by US State Climate Divisions."),


        ui.p("The data is erived from climate simulations from the CMIP6 Climate Model Ensembles ",
             "and are a collection of the best simulations from each center's model participating in CMIP6."),

        ui.p("The output from these models were 'downscaled' from the global to regional scale using the ",
             "Localized Constructed Analog Method (LOCA) by ",
               ui.tags.a("Pierce et al. (2023)." ,href='https://doi.org/10.1175/JHM-D-22-0194.1')),

        ui.p("The results for the downscaling have been averaged over State Climate Divisions chosen by the user."),

        ui.p("The user may select a variable from the pulldown menus, and also select a future ",
             "30-year period by which to view the monthly trends and compare them to a fixed historical period (1981-2010)."),


        ui.p("For both the annual and monthly plots, the solid lines represent the ensemble means, while the shading ",
             "represents the middle 50% range of the collected ensembles.",),
            
    ),
    
    ui.br(),

    ui.card(
        ui.card_header("Citations & References"),

        ui.markdown("""Pierce, D.W., D.R. Cayan, D.R. Feldman, and M.D. Risser, 2023: Future Increases in North American Extreme Precipitation in CMIP6 Downscaled with LOCA, *Journal of Hydrometeorology*, **24**(5), 951-975, doi:[10.1175/JHM-D-22-0194.1](https://doi.org/10.1175/JHM-D-22-0194.1)."""),

    ),

  

      
    title="CMIP6-LOCA2 Climate Indicies",
    lang="en",

)
# 
##########################################################

##########################################################
#
# Server Interface
#
def server(input, output, session):

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
    def loca2_daily():
        ###################################
        #
        # Retrieve Daily LOCA2 Xarray
        #

        selected_climdiv = input.climdiv_selection()
        climdiv_key = selected_climdiv.split()[0]

        if (use_url):
            url = "https://thredds.ias.sdsmt.edu:8443/thredds/fileServer/LOCA2/Specific_Regional_Aggregate_Sets/NCEI_Climate_Divisions/R_Daily_Files/LOCA2_V1_nCLIMDIV_" + climdiv_key + ".RData"#?raw=true"

            print("===============") 
            print(" hostname :", hostname)
            print("  use_url :", use_url)
            print("      url :", url)
            print("===============")
 
            response = urllib.request.urlopen(url)
            result = pyreadr.read_r(io.BytesIO(response.read()))
        else:
            filename = "/data/DATASETS/LOCA_MACA_Ensembles/LOCA2/LOCA2_CONUS/Specific_Regional_Aggregate_Sets/NCEI_Climate_Divisions/R_Daily_Files/LOCA2_V1_nCLIMDIV_" + climdiv_key + ".RData"
            print("===============")
            print(" hostname :", hostname)
            print("  use_url :", use_url)
            print(" filename :", filename)
            print("===============")
            result = pyreadr.read_r(path = filename)

        loca2_daily                 = result["loca2_daily"]
        loca2_daily                 = loca2_daily[loca2_daily["Percentile"] == "MEAN"]
        loca2_daily["time"]         = pd.to_datetime(loca2_daily["Time"])    
        loca2_daily["Ensemble"]     = loca2_daily["Model"].astype(str) + "__" + loca2_daily["Member"].astype(str)
        loca2_daily = loca2_daily[["Ensemble","Scenario","time","tasmax","tasmin","pr"]]

        loca2_daily["tasmax"] = loca2_daily["tasmax"] +273.15
        loca2_daily["tasmin"] = loca2_daily["tasmin"] +273.15
        loca2_daily["tasavg"] = (loca2_daily["tasmax"] + loca2_daily["tasmin"]) / 2.
        loca2_daily["pr"]     = loca2_daily[    "pr"] / 86400.

        loca2_daily = loca2_daily.set_index(["Ensemble","Scenario","time"]).to_xarray()

        loca2_daily["tasmax"].attrs["units"]         = "K"
        loca2_daily["tasavg"].attrs["units"]         = "K"
        loca2_daily["tasmin"].attrs["units"]         = "K"
        loca2_daily[    "pr"].attrs["units"]         = "kg m-2 s-1"
        loca2_daily["tasmax"].attrs["long_name"]     = "Maximal daily temperature"
        loca2_daily["tasavg"].attrs["long_name"]     = "Mean daily temperature"
        loca2_daily["tasmin"].attrs["long_name"]     = "Minimal daily temperature"
        loca2_daily[    "pr"].attrs["long_name"]     = "Mean daily precipitation rate"
        loca2_daily["tasmax"].attrs["cell_methods"]  = "time: max within days"
        loca2_daily["tasavg"].attrs["cell_methods"]  = "time: mean within days"
        loca2_daily["tasmin"].attrs["cell_methods"]  = "time: min within days"
        loca2_daily[    "pr"].attrs["cell_methods"]  = "time: mean within days"
        loca2_daily["tasmax"].attrs["standard_name"] = "air_temperature"
        loca2_daily["tasavg"].attrs["standard_name"] = "air_temperature"
        loca2_daily["tasmin"].attrs["standard_name"] = "air_temperature"
        loca2_daily[    "pr"].attrs["standard_name"] = "precipitation_flux"


        loca2_daily  = loca2_daily.convert_calendar(calendar = "standard", dim = "time", use_cftime = True)

        return loca2_daily

        #
        ###################################


    @reactive.calc
    def index_y():
        ###################################
        #
        # Calculate Annual Index Dataframe
        #

        mask_annual  = np.isnan(xclim.atmos.precip_accumulation(pr=loca2_daily()["pr"], freq='YS'))

        if (input.selected_index() == "Mean Temperature"):
            
            index_y = loca2_daily()["tasavg"].resample(time="YS").mean(dim="time")
            index_y.values = np.where(mask_annual,  np.nan, index_y)
            index_y.name   = "tasavg"
            index_y.values = index_y.values - 273.15

        if (input.selected_index() == "Total Precipitation"):
            
            index_y =  xclim.indices.precip_accumulation(loca2_daily()["pr"], freq="YS")
            index_y.values = np.where(mask_annual,  np.nan, index_y)
            index_y.name   = "pr"
            
        if (input.selected_index() == "Simple Precip Intensity Index (SPII)"):
            
            index_y = xclim.indicators.atmos.daily_pr_intensity(loca2_daily()["pr"], freq="YS")
            index_y.values = np.where(mask_annual,  np.nan, index_y)

        elif (input.selected_index() == "Dry Spell Frequency"):   
            
            index_y = xclim.indicators.atmos.dry_spell_frequency(loca2_daily()["pr"], window=5, freq="YS")
            index_y.values = np.where(mask_annual,  np.nan, index_y)

        elif (input.selected_index() == "Heat Wave Frequency"):   
            
            index_y = xclim.indicators.atmos.heat_wave_frequency(tasmin             = loca2_daily()["tasmin"], 
                                                                 tasmax             = loca2_daily()["tasmax"],
                                                                 freq               =        'YS')
            index_y.values = np.where(mask_annual,  np.nan, index_y)

        elif (input.selected_index() == "Heat Wave Frequency Max Length"):   
            
            index_y = xclim.indicators.atmos.heat_wave_max_length(tasmin             = loca2_daily()["tasmin"], 
                                                                 tasmax             = loca2_daily()["tasmax"],
                                                                 freq               =        'YS')
            index_y.values = np.where(mask_annual,  np.nan, index_y)

        elif (input.selected_index() == "Heat Wave Frequency Total Length"):   
            
            index_y = xclim.indicators.atmos.heat_wave_total_length(tasmin             = loca2_daily()["tasmin"], 
                                                                    tasmax             = loca2_daily()["tasmax"],
                                                                    freq               =        'YS')
            index_y.values = np.where(mask_annual,  np.nan, index_y)

        elif (input.selected_index() == "7-day Anticedant Precipitation Index"):   
            
            index_y = xclim.indicators.atmos.antecedent_precipitation_index(pr   = loca2_daily()["pr"])
            mask_daily  = np.isnan(loca2_daily()["pr"])
            index_y.values = np.where(mask_daily,  np.nan, index_y)

        elif (input.selected_index() == "Cooling Degree Days"):   
            
            index_y = xclim.indicators.atmos.cooling_degree_days(tas   = loca2_daily()["tasavg"],
                                                                             freq =        'YS')
            index_y.values = np.where(mask_annual,  np.nan, index_y)

        elif (input.selected_index() == "Heating Degree Days"):   
            
            index_y = xclim.indicators.atmos.heating_degree_days(tas   = loca2_daily()["tasavg"],
                                                                             freq =        'YS')
            index_y.values = np.where(mask_annual,  np.nan, index_y)

        elif (input.selected_index() == "Freeze-Thaw Days"):   
            
            index_y = xclim.indicators.atmos.daily_freezethaw_cycles(tasmin = loca2_daily()["tasmin"], 
                                                                      tasmax = loca2_daily()["tasmax"],
                                                                      freq   =        'YS')
            index_y.values = np.where(mask_annual,  np.nan, index_y)








        index_y["time"] = index_y.indexes['time'].to_datetimeindex(time_unit='us')

        index_y = index_y.to_dataframe().reset_index().dropna()

        index_y["Year"]   = index_y["time"].dt.year

        index_y['Scenario'] = pd.Categorical(index_y['Scenario'], 
                                                categories = SSP_Scenarios, 
                                                ordered    = True)

        print(" Annual Dataframe Fields", index_y.columns)

        return index_y

        #
        ###################################

    @reactive.calc
    def index_m():
        ###################################
        #
        # Calculate Monthly Index Dataframe
        #

        mask_monthly = np.isnan(xclim.atmos.precip_accumulation(pr=loca2_daily()["pr"], freq='MS'))


        if (input.selected_index() == "Mean Temperature"):
            
            index_m = loca2_daily()["tasavg"].resample(time="MS").mean(dim="time")
            index_m.values = np.where(mask_monthly,  np.nan, index_m)
            index_m.name   = "tasavg"
            index_m.values = index_m.values - 273.15

        if (input.selected_index() == "Total Precipitation"):
            
            index_m =  xclim.indices.precip_accumulation(loca2_daily()["pr"], freq="MS")
            index_m.values = np.where(mask_monthly,  np.nan, index_m)
            index_m.name   = "pr"
            
        if (input.selected_index() == "Simple Precip Intensity Index (SPII)"):
            
            index_m = xclim.indicators.atmos.daily_pr_intensity(loca2_daily()["pr"], freq="MS")
            index_m.values = np.where(mask_monthly, np.nan, index_m)

        elif (input.selected_index() == "Dry Spell Frequency"):   
            
            index_m = xclim.indicators.atmos.dry_spell_frequency(loca2_daily()["pr"], window=5, freq="MS")
            index_m.values = np.where(mask_monthly, np.nan, index_m)

        elif (input.selected_index() == "Heat Wave Frequency"):   
            
            index_m = xclim.indicators.atmos.heat_wave_frequency(tasmin             = loca2_daily()["tasmin"], 
                                                                 tasmax             = loca2_daily()["tasmax"],
                                                                 freq               =        'MS')
            index_m.values = np.where(mask_monthly, np.nan, index_m)

        elif (input.selected_index() == "Heat Wave Frequency Max Length"):   
            
            index_m = xclim.indicators.atmos.heat_wave_max_length(tasmin             = loca2_daily()["tasmin"], 
                                                                 tasmax             = loca2_daily()["tasmax"],
                                                                 freq               =        'MS')
            index_m.values = np.where(mask_monthly, np.nan, index_m)

        elif (input.selected_index() == "Heat Wave Frequency Total Length"):   
            
            index_m = xclim.indicators.atmos.heat_wave_total_length(tasmin             = loca2_daily()["tasmin"], 
                                                                    tasmax             = loca2_daily()["tasmax"],
                                                                    freq               =        'MS')
            index_m.values = np.where(mask_monthly, np.nan, index_m)

        elif (input.selected_index() == "7-day Anticedant Precipitation Index"):   
            
            index_m = xclim.indicators.atmos.antecedent_precipitation_index(pr   = loca2_daily()["pr"])
            mask_daily  = np.isnan(loca2_daily()["pr"])
            index_m.values = np.where(mask_daily,  np.nan, index_m)

        elif (input.selected_index() == "Cooling Degree Days"):   
            
            index_m = xclim.indicators.atmos.cooling_degree_days(tas   = loca2_daily()["tasavg"],
                                                                             freq =        'MS')
            index_m.values = np.where(mask_monthly, np.nan, index_m)

        elif (input.selected_index() == "Heating Degree Days"):   
            
            index_m = xclim.indicators.atmos.heating_degree_days(tas   = loca2_daily()["tasavg"],
                                                                             freq =        'MS')
            index_m.values = np.where(mask_monthly, np.nan, index_m)

        elif (input.selected_index() == "Freeze-Thaw Days"):   
            
            index_m = xclim.indicators.atmos.daily_freezethaw_cycles(tasmin = loca2_daily()["tasmin"], 
                                                                      tasmax = loca2_daily()["tasmax"],
                                                                      freq   =        'MS')
            index_m.values = np.where(mask_monthly, np.nan, index_m)

        index_m["time"] = index_m.indexes['time'].to_datetimeindex(time_unit='us')

        index_m = index_m.to_dataframe().reset_index().dropna()

        index_m["Year"]   = index_m["time"].dt.year
        index_m["Month"]  = index_m["time"].dt.strftime('%b')

        index_m['Scenario'] = pd.Categorical(index_m['Scenario'], 
                                                categories = SSP_Scenarios, 
                                                ordered    = True)


        print("Monthly Dataframe Fields", index_m.columns)
        return index_m

        #
        ###################################


    @render.plot
    def annual_plot():
        ###################################
        #
        # Create Annual Plot
        #

        my_metadata = df_climdivs[df_climdivs["Climate_Division_Selector"]==input.climdiv_selection()]
        print(my_metadata)

        df_local_index = df_climate_indicies[df_climate_indicies["selected_index"] == input.selected_index()]

        print("**** PLOT ANNUAL: New Plot Crunch ****")
        print("Selected Index: ",input.selected_index())
        df_local_index = df_climate_indicies[df_climate_indicies["selected_index"] == input.selected_index()]
        print(df_local_index)
        varname        = df_local_index["varname"].values[0]
        units          = df_local_index["units"].values[0]
        print("Selected Index: ", varname, " [", units,"]")
        print("**** PLOT ANNUAL: New Plot Crunch ****")



        climdiv_string = "CMIP6-LOCA2 Downscaled Climate Ensembles\n" + \
                         my_metadata["State_Climate_Division"].values[0]       + \
                         ", "                                           + \
                         my_metadata["State"].values[0]    + \
                         " ("                                           + \
                         str(my_metadata["ClimDiv"].values[0]).zfill(4) + \
                         ") NCEI Climate Division"
       
        sns.lineplot(data    = index_y(),
                     y       = varname,
                     x       = "Year",
                     hue     = "Scenario",
                     palette = SSP_Colors_dict)
        plt.ylabel(input.selected_index() + " [" + units + "]")

        plt.title(climdiv_string, loc='left')
        plt.axvspan(xmin  = historical_period[0], 
                    xmax  = historical_period[1], 
                    color = 'lightgrey',
                    alpha = 0.25)
        plt.axvspan(xmin  = future_years[input.period_selection()][0], 
                    xmax  = future_years[input.period_selection()][1], 
                    color = 'lightgrey',
                    alpha = 0.25)
        #
        ###################################


    @render.plot
    def monthly_plot():
        ###################################
        #
        # Create Monthly Plot
        #
        my_metadata = df_climdivs[df_climdivs["Climate_Division_Selector"]==input.climdiv_selection()]


        print("**** PLOT MONTHLY: New Plot Crunch ****")
        print("Selected Index: ",input.selected_index())
        df_local_index = df_climate_indicies[df_climate_indicies["selected_index"] == input.selected_index()]
        print(df_local_index)
        varname        = df_local_index["varname"].values[0]
        units          = df_local_index["units"].values[0]
        print("Selected Index: ", varname, " [", units,"]")
        print("**** PLOT MONTHLY: New Plot Crunch ****")



        climdiv_string = "CMIP6-LOCA2 Downscaled Climate Ensembles " + \
                         "(" + historical_period_string + ") vs (" + input.period_selection() + ")" + \
                         "\n" + \
                         my_metadata["State_Climate_Division"].values[0]          + \
                         ", "                                           + \
                         my_metadata["State"].values[0]    + \
                         " ("                                           + \
                         str(my_metadata["ClimDiv"].values[0]).zfill(4) + \
                         ") NCEI Climate Division"

        index_m0 = index_m()[((index_m()["Year"] >= historical_period[0])                      & (index_m()["Year"] <= historical_period[1])) |
                             ((index_m()["Year"] >= future_years[input.period_selection()][0]) & (index_m()["Year"] <= future_years[input.period_selection()][1])) ]

        sns.lineplot(data     = index_m0,
                     y        = varname,
                     x        = "Month",
                     hue      = "Scenario",
                     palette  = SSP_Colors_dict,
                     errorbar = ("pi", 50))
        plt.title(climdiv_string, loc='left')
        plt.ylabel(input.selected_index() + " [" + units + "]")

        #
        ###################################


    @render.download(filename="loca2_annual_data_export.csv")
    def annual_download_btn():
        # Yield the plain CSV text string directly to the browser
        yield index_y().to_csv(index=False)


    @render.download(filename="loca2_monthly_data_export.csv")
    def monthly_download_btn():
        # Yield the plain CSV text string directly to the browser
        yield index_m().to_csv(index=False)
    

    @render.image
    def state_zone_map():
        ###################################
        #
        # Pull Correct State Image
        #
        
        selected_state = input.state_selection()
        state_key = str(selected_state.split()[0]).zfill(2)
        state_img_file = "./state_climate_division_images/state_"+state_key+".png"
        print("--> state_key:", state_img_file)

        img: ImgData = {"src": state_img_file, "width": "100%"}
        return img

        #
        ###################################



    @render.text
    def index_description():
        ###################################
        #
        # Retrieve Daily LOCA2 Xarray
        #

        print("$$$$ INDEX DESCRIPTION MONTHLY: New Plot Crunch $$$$")
        print("Selected Index: ",input.selected_index())
        df_local_index = df_climate_indicies[df_climate_indicies["selected_index"] == input.selected_index()]
        print(df_local_index)
        index_description = df_local_index["Description"].values[0]
        print("Selected Index: ", index_description)
        print("$$$$ INDEX DESCRIPTION MONTHLY: New Plot Crunch $$$$")

        return index_description

        #
        ###################################



# 
##########################################################     



##########################################################
#
# Execute Webapp
#

app = App(app_ui, server)

# 
##########################################################     
