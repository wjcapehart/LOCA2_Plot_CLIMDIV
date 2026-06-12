


##########################################################
#
# Libraries
#

import seaborn           as sns
import pyreadr           as pyreadr
import pandas            as pd 
import matplotlib.pyplot as plt
import numpy as np
import io
import urllib.request
import calendar
import socket



from   shiny.types   import ImgData
from   shiny         import reactive, App, render, ui  

#
##########################################################



hostname = socket.gethostname()
if (hostname == "kyrill"):
    use_url = False
else:
    use_url = True
print("===============")
print(" hostname :", hostname)
print("  use_url :", use_url)
print("===============")




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
# Abbreviation vs Human Name LUT
#

variable_name_to_abbr_dict = {"Min 2-m Air Temp":     "tasmin",
                              "Mean 2-m Air Temp":    "tasavg",
                              "Max 2-m Air Temp":     "tasmax",
                              "Precipitation Amount":     "pr"}

variable_names = list(variable_name_to_abbr_dict)
print(variable_names)

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

        ui.input_select(id       = "loca_var_longname", 
                        label    = "LOCA2 Plotting Variable", 
                        choices  = variable_names,
                        selected = "Mean 2-m Air Temp"),

        ui.input_switch("use_metric", "Metric Units", True),

        ui.input_select(id       = "period_selection", 
                        label    = "Select Future Period", 
                        choices  = list(future_years.keys()), 
                        selected = "2036-2065"),
        ui.output_plot(id        = "state_zone_map"),

    ),

    ui.output_plot("annual_plot"),


    ui.output_plot("monthly_plot"),

    ui.p("Download as a comma-delimited file (CSV), Metric units only"),

    ui.download_button(id = "annual_download_btn", 
                       label = "Download Annual Data (CSV)"),
    ui.download_button(id = "monthly_download_btn", 
                      label = "Download Monthly Data (CSV)"),
    ui.p(ui.br()),
    ui.h1("About This Display"),

    ui.p("This display shows a a series of climate simulations from the CMIP6 Climate Model Ensembles ",
         "and are a collection of the best simulations from each center's model participating in CMIP6.",ui.br(),ui.br()),

    ui.p("The output from these models were 'downscaled' from the global to regional scale using the ",
         "Localized Constructed Analog Method (LOCA) by ",
           ui.tags.a("Pierce et al. (2014)." ,href='https://journals.ametsoc.org/view/journals/hydr/15/6/jhm-d-14-0082_1.xml'),ui.br(),ui.br()),

    ui.p("The results for the downscaling have been averaged over State Climate Divisions chosen by the user.",ui.br(),ui.br()),

    ui.p("The user may select a variable from the pulldown menus, and also select a future ",
         "30-year period by which to view the monthly trends and compare them to a fixed historical period (1981-2010).",ui.br(),ui.br()),


    ui.p("For both the annual and monthly plots, the solid lines represent the ensemble means, while the shading ",
         "represents the middle 50% range of the collected ensembles.",ui.br(),ui.br()),


    title="CMIP6-LOCA2 Ensemble Plotting",
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
    def df_loca2_monthy():
        ###################################
        #
        # Retrieve Monthly LOCA2 DataFrame
        #

        selected_climdiv = input.climdiv_selection()
        climdiv_key = selected_climdiv.split()[0]


        if (use_url):
            url = "https://thredds.ias.sdsmt.edu:8443/thredds/fileServer/LOCA2/Specific_Regional_Aggregate_Sets/NCEI_Climate_Divisions/R_Monthly_Files/LOCA2_V1_nCLIMDIV_MONTHLY_" + climdiv_key + ".RData"#?raw=true"

            print("===============") 
            print(" hostname :", hostname)
            print("  use_url :", use_url)
            print("      url :", url)
            print("===============")
 
            response = urllib.request.urlopen(url)
            result = pyreadr.read_r(io.BytesIO(response.read()))
        else:
            filename = "/data/DATASETS/LOCA_MACA_Ensembles/LOCA2/LOCA2_CONUS/Specific_Regional_Aggregate_Sets/NCEI_Climate_Divisions/R_Monthly_Files/LOCA2_V1_nCLIMDIV_MONTHLY_" + climdiv_key + ".RData"
            print("===============")
            print(" hostname :", hostname)
            print("  use_url :", use_url)
            print(" filename :", filename)
            print("===============")
            result = pyreadr.read_r(path = filename)


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
        
        df_loca2_monthy.rename(columns  = {"Division":"State_Climate_Division_Code"}, inplace= True)


        df_loca2_monthy["Model_Member"] = df_loca2_monthy["Model"].astype(str) + "__" + df_loca2_monthy["Member"].astype(str)

        df_loca2_monthy = df_loca2_monthy.groupby(["State_Climate_Division_Code",
                                                   "Scenario",
                                                   "Month",
                                                   "Model_Member"]).agg({'tasmax':'mean',
                                                                  'tasavg':'mean',
                                                                   'tasmin':'mean',
                                                                   'pr':    'mean'}).reset_index()

        historical_string = "(" + historical_period_string + ")"
        future_string     = "(" + input.period_selection() + ")"

        df_loca2_monthy["Period"] = np.where(df_loca2_monthy['Scenario'].astype(str) == "Historical", 
                                             historical_string, future_string)



        df_loca2_monthy                 = df_loca2_monthy[["State_Climate_Division_Code",
                                                           "Month", 
                                                           "Scenario",
                                                           "Period",
                                                           "Model_Member",
                                                           "tasmin",
                                                           "tasavg",
                                                           "tasmax",
                                                           "pr"]]

                                                        
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

        if (use_url):
            url      = "https://thredds.ias.sdsmt.edu:8443/thredds/fileServer/LOCA2/Specific_Regional_Aggregate_Sets/NCEI_Climate_Divisions/R_Annual_Files/LOCA2_V1_nCLIMDIV_ANNUAL_" + climdiv_key + ".RData"#?raw=true"
            print("===============")
            print(" hostname :", hostname)
            print("  use_url :", use_url)
            print("      url :", url)
            print("===============")
            response = urllib.request.urlopen(url)
            result   = pyreadr.read_r(io.BytesIO(response.read()))
        else:
            filename = "/data/DATASETS/LOCA_MACA_Ensembles/LOCA2/LOCA2_CONUS/Specific_Regional_Aggregate_Sets/NCEI_Climate_Divisions/R_Annual_Files/LOCA2_V1_nCLIMDIV_ANNUAL_" + climdiv_key + ".RData"
            print("===============")
            print(" hostname :", hostname)
            print("  use_url :", use_url)
            print(" filename :", filename)
            print("===============")
            result   = pyreadr.read_r(path = filename)

        df_loca2_annual = result['loca2_annual']
        df_loca2_annual = df_loca2_annual[df_loca2_annual["Percentile"]=="MEAN"]
        df_loca2_annual['Scenario'] = pd.Categorical(df_loca2_annual['Scenario'], 
                                                     categories = SSP_Scenarios, 
                                                     ordered    =   True)

        df_loca2_annual["tasavg"] = (df_loca2_annual["tasmax"] + df_loca2_annual["tasmin"]) /2

        df_loca2_annual.rename(columns  = {"Division":"State_Climate_Division_Code"}, inplace= True)
        df_loca2_annual["Model_Member"] = df_loca2_annual["Model"].astype(str) + "__" + df_loca2_annual["Member"].astype(str)
        df_loca2_annual                 = df_loca2_annual[["State_Climate_Division_Code",
                                                           "Year", 
                                                           "Scenario",
                                                           "Model_Member",
                                                           "tasmin",
                                                           "tasavg",
                                                           "tasmax",
                                                           "pr"]]

        return df_loca2_annual

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

        climdiv_string = "CMIP6-LOCA2 Downscaled Climate Ensembles\n" + \
                         my_metadata["State_Climate_Division"].values[0]       + \
                         ", "                                           + \
                         my_metadata["State"].values[0]    + \
                         " ("                                           + \
                         str(my_metadata["ClimDiv"].values[0]).zfill(4) + \
                         ") NCEI Climate Division"

        df_loca2_annual_units = df_loca2_annual().copy()

        if input.use_metric():
            yaxes_labels = {"Max 2-m Air Temp":     "2-m Mean Daily Maximum Temperature (°C)",
                            "Mean 2-m Air Temp":    "2-m Mean Temperature (°C)",
                            "Min 2-m Air Temp":     "2-m Mean Daily Minimum Temperature (°C)",
                            "Precipitation Amount": "Annual Total Precipitation (mm)"}
        else:
            yaxes_labels = {"Max 2-m Air Temp":     "2-m Mean Daily Maximum Temperature (°F)",
                            "Mean 2-m Air Temp":    "2-m Mean Temperature (°F)",
                            "Min 2-m Air Temp":     "2-m Mean Daily Minimum Temperature (°F)",
                            "Precipitation Amount": "Annual Total Precipitation (in)"}  

            df_loca2_annual_units["tasmax"] = df_loca2_annual_units["tasmax"] * 9./5. + 32
            df_loca2_annual_units["tasavg"] = df_loca2_annual_units["tasavg"] * 9./5. + 32
            df_loca2_annual_units["tasmin"] = df_loca2_annual_units["tasmin"] * 9./5. + 32
            df_loca2_annual_units["pr"]     = df_loca2_annual_units["pr"]     / 25.4 
           


        sns.lineplot(data     = df_loca2_annual_units,
                     y        = variable_name_to_abbr_dict[input.loca_var_longname()],
                     x        = "Year",
                     hue      = "Scenario",
                     palette  = SSP_Colors_dict,
                     errorbar = ("pi", 50))
        plt.title(climdiv_string, loc='left')
        plt.ylabel(yaxes_labels[input.loca_var_longname()])
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


        climdiv_string = "CMIP6-LOCA2 Downscaled Climate Ensembles " + \
                         "(" + historical_period_string + ") vs (" + input.period_selection() + ")" + \
                         "\n" + \
                         my_metadata["State_Climate_Division"].values[0]          + \
                         ", "                                           + \
                         my_metadata["State"].values[0]    + \
                         " ("                                           + \
                         str(my_metadata["ClimDiv"].values[0]).zfill(4) + \
                         ") NCEI Climate Division"

        df_loca2_monthy_units = df_loca2_monthy().copy()

        if input.use_metric():
            yaxes_labels = {"Max 2-m Air Temp":      "2-m Mean Daily Maximum Temperature (°C)",
                            "Mean 2-m Air Temp":     "2-m Mean Temperature (°C)",
                            "Min 2-m Air Temp":      "2-m Mean Daily Minimum Temperature (°C)",
                            "Precipitation Amount" : "Monthly Total Precipitation (mm)"}
        else:
            yaxes_labels = {"Max 2-m Air Temp":      "2-m Mean Daily Maximum Temperature (°F)",
                            "Mean 2-m Air Temp":     "2-m Mean Temperature (°F)",
                            "Min 2-m Air Temp":      "2-m Mean Daily Minimum Temperature (°F)",
                            "Precipitation Amount" : "Monthly Total Precipitation (in)"}

            df_loca2_monthy_units["tasmax"] = df_loca2_monthy_units["tasmax"] * 9./5. + 32
            df_loca2_monthy_units["tasavg"] = df_loca2_monthy_units["tasavg"] * 9./5. + 32
            df_loca2_monthy_units["tasmin"] = df_loca2_monthy_units["tasmin"] * 9./5. + 32
            df_loca2_monthy_units["pr"]     = df_loca2_monthy_units["pr"]     / 25.4 
           



        sns.lineplot(data     = df_loca2_monthy_units,
                     y        = variable_name_to_abbr_dict[input.loca_var_longname()],
                     x        = "Month",
                     hue      = "Scenario",
                     palette  = SSP_Colors_dict,
                     errorbar = ("pi", 50))
        plt.title(climdiv_string, loc='left')
        plt.ylabel(yaxes_labels[input.loca_var_longname()])
        #
        ###################################


    @render.download(filename="loca2_annual_data_export.csv")
    def annual_download_btn():
        # Yield the plain CSV text string directly to the browser
        yield df_loca2_annual().to_csv(index=False)


    @render.download(filename="loca2_monthly_data_export.csv")
    def monthly_download_btn():
        # Yield the plain CSV text string directly to the browser
        yield df_loca2_monthy().to_csv(index=False)
    
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

# 
##########################################################     



##########################################################
#
# Execute Webapp
#

app = App(app_ui, server)

# 
##########################################################     
