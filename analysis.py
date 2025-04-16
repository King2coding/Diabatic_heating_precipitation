#%%
import os
import pandas as pd
import numpy as np

import xarray as xr
from rasterio.warp import Resampling
from pyproj import CRS
import sys
from datetime import date
import matplotlib.pyplot as plt


# Specify the directory containing the .py file
directory = r'/ra1/pubdat/AVHRR_CloudSat_proj/codes'
# Add the directory to the system path
sys.path.append(directory)

from utils_precipitation_comparison import* 


#%%
# fuctions

def load_ascii_data(file_path):
    # Load ASCII data
    data = np.loadtxt(file_path)
    
    # Handle -999 as NaN
    data[data == -999] = np.nan
    
    return data
#------------------------------------------------------------

def zonal_compute(arr, prdt):
    print(prdt)
    if 'x' in arr.dims and 'y' in arr.dims:
        arr = arr.rename({'x': 'lon', 'y': 'lat'})

    grpby = 'time' if prdt == 'gpcp' else 'nm'
    # Calculate combined zonal mean
    combined_zonal_mean = arr.groupby('lat').mean(dim=[grpby, 'lon'])
    
    # Mask land and ocean data using the land-sea mask (assuming 1 for land, 0 for ocean)
    land_data = arr.where(lsm.data == 1)
    ocean_data = arr.where(lsm.data == 0)
    
    # Calculate zonal mean for land and ocean data
    land_zonal_mean = land_data.groupby('lat').mean(dim=[grpby, 'lon'])
    ocean_zonal_mean = ocean_data.groupby('lat').mean(dim=[grpby, 'lon'])
    
    return combined_zonal_mean, land_zonal_mean, ocean_zonal_mean
#------------------------------------------------------------

def plot_zonal_means(zonal_means, ylabel='Zonal mean', xlabel='Latitude', filename=None):
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharex=True, sharey=True)

    # Define the titles for each subplot
    titles = ['COMBINED', 'OCEAN', 'LAND']

    # Define the specific ticks for the x-axis (latitude)
    lat_ticks = [-90, -75, -60, -45, -30, -15, 0, 15, 30, 45, 60, 75, 90]

    # Define the styles for each product
    product_styles = {
        'GPCP': {'color': 'grey', 'linestyle': '--'},
        'Diabatic precip_heating': {'color': 'black', 'linestyle': '-.'},
        'CMIP6': {'color': 'green', 'linestyle': ':'},
        'AMIP6': {'color': 'orange', 'linestyle': '-.'}
    }

    # Loop through each region (COMBINED, OCEAN, LAND)
    for j, region in enumerate(titles):
        ax = axes[j]

        # Plot each product's data for the current region
        for product_name, data in zonal_means.items():
            print(product_name)
            # Select the appropriate data variable based on the product name
            if product_name == 'GPCP':
                data_var = 'sat_gauge_precip'
            elif product_name == 'Diabatic precip_heating':
                data_var = 'precip_heating'
            else:     
                data_var = 'zonal_mean_precip'

            # Get the style for the current product
            style = product_styles.get(product_name, {'color': 'blue', 'linestyle': '-'})

            ax.plot(data[region].coords['lat'], data[region][data_var], 
                    linestyle=style['linestyle'], color=style['color'], label=product_name)

        # Set the title and labels with the desired font sizes
        ax.set_title(f"{region}", fontsize=20)
        ax.set_xlabel(xlabel, fontsize=15)
        if j == 0:
            ax.set_ylabel(ylabel, fontsize=15)

        # Set the range for the latitude (x-axis) from -90 to 90
        ax.set_xlim([-90, 90])
        ax.set_xticks(lat_ticks)

        # Customize ticks and gridlines
        ax.tick_params(axis='both', which='major', labelsize=15)
        ax.grid(True, linestyle='--')

        # Add legend to only the first subplot
        if j == 0:
            ax.legend(fontsize=15, frameon=False,ncol=2)

    # Adjust layout and save the figure if a filename is provided
    fig.tight_layout()
    if filename:
        plt.savefig(filename,bbox_inches='tight')
    plt.show()
#------------------------------------------------------------
def plot_mean_maps(gpcp_data, dhp_data, gpcp_var='sat_gauge_precip', dhp_var='precip_heating', vmin=0, vmax=20, filename=None):
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), subplot_kw={'projection': ccrs.PlateCarree()}, sharey=True)

    # Plot GPCP data
    gpcp_plot = gpcp_data[gpcp_var].plot(
        ax=axes[0],
        transform=ccrs.PlateCarree(),
        cmap='jet',
        add_colorbar=False,
        vmin=vmin,
        vmax=vmax,
    )
    axes[0].set_title('GPCP Mean Map', fontsize=18)
    axes[0].coastlines()
    axes[0].add_feature(cfeature.BORDERS, linestyle=':')
    gl0 = axes[0].gridlines(draw_labels=True, linestyle='--', x_inline=False, y_inline=False)
    
    # Remove top x-axis and right y-axis labels for ax[0]
    gl0.right_labels = False
    gl0.top_labels = False
    axes[0].yaxis.set_label_position("left")
    axes[0].xaxis.set_label_position("bottom")
    
    # Plot Diabatic precip_heating data
    dhp_plot = dhp_data[dhp_var].plot(
        ax=axes[1],
        transform=ccrs.PlateCarree(),
        cmap='jet',
        add_colorbar=False,
        vmin=vmin,
        vmax=vmax,
    )
    axes[1].set_title('Diabatic Precipitation Heating Mean Map', fontsize=18)
    axes[1].coastlines()
    axes[1].add_feature(cfeature.BORDERS, linestyle=':')
    gl1 = axes[1].gridlines(draw_labels=True, linestyle='--', x_inline=False, y_inline=False)
    
    # Adjust labels for ax[1]
    gl1.left_labels = False  # No y-label on the left side for ax[1]
    gl1.right_labels = True
    gl1.top_labels = False
    axes[1].xaxis.set_label_position("bottom")

    # Increase font sizes for x and y tick labels
    axes[0].tick_params(axis='both', which='major', labelsize=18)
    axes[1].tick_params(axis='both', which='major', labelsize=18)

    # Add a single color bar below the plots
    cbar = fig.colorbar(gpcp_plot, ax=axes, orientation='horizontal', fraction=0.046, pad=0.1)
    cbar.set_label('Mean Precipitation (mm/day)', fontsize=15)
    cbar.ax.tick_params(labelsize=15)  # Increase font size of colorbar tick labels

    # Save the figure if a filename is provided
    if filename:
        plt.savefig(filename,bbox_inches='tight')
    plt.show()

#------------------------------------------------------------

# def calculate_area_weighted_mean(precip_data, lat_var, precip_var):
#     """
#     Calculate the area-weighted mean precipitation using cosine of latitude.

#     Parameters:
#     precip_data (xarray.Dataset): The dataset containing latitude and precipitation variables.
#     lat_var (str): The name of the latitude variable in the dataset. Default is 'lat'.
#     precip_var (str): The name of the precipitation variable in the dataset. Default is 'sat_gauge_precip'.

#     Returns:
#     float: The area-weighted mean precipitation.
#     """
#     # Extract latitude values and precipitation data
#     latitudes = precip_data[lat_var].values
#     precipitation = precip_data[precip_var].values

#     # Calculate the weights based on the cosine of the latitude
#     weights = np.cos(np.deg2rad(latitudes))

#     # Apply the weights to the precipitation data
#     weighted_precip = precipitation * weights

#     # Calculate the area-weighted mean precipitation
#     area_weighted_mean = np.nansum(weighted_precip) / np.nansum(weights)

#     return area_weighted_mean
    
# def calculate_area_weighted_mean_with_fraction(precip_data, lat_var, precip_var, area_fraction):
#     """
#     Calculate the area-weighted mean precipitation using cosine of latitude and area fractions.

#     Parameters:
#     precip_data (numpy.array): Precipitation data array.
#     lat_var (str): The name of the latitude variable in the dataset. Default is 'lat'.
#     precip_var (str): The name of the precipitation variable in the dataset. Default is 'sat_gauge_precip'.
#     area_fraction (numpy.array): Array of area fractions (land or ocean) corresponding to each grid cell.

#     Returns:
#     float: The area-weighted mean precipitation considering area fractions.
#     """
#     latitudes = precip_data[lat_var].values
#     precipitation = precip_data[precip_var].values
#     # Calculate the weights based on the cosine of the latitude
#     weights = np.cos(np.deg2rad(latitudes)) # 

#     # Apply the weights and area fractions to the precipitation data
#     weighted_precip = precipitation * weights * area_fraction

#     # Calculate the area-weighted mean precipitation
#     mean_precipitation = np.nansum(weighted_precip) / np.nansum(weights* area_fraction ) #

#     return mean_precipitation
    
def calculate_area_weighted_mean(precip_data, latitudes_vals, area_fraction,typ): # 
    # Compute cosine latitude weights
    weights = np.cos(np.deg2rad(latitudes_vals))       

    if typ == 'cmb':
        # Apply the weights to the precipitation data
        weighted_precip = precip_data * weights

        # Calculate the area-weighted mean precipitation
        area_weighted_mean = np.nansum(weighted_precip) / np.nansum(weights)   

    else:
        # Apply weights and area fractions to precipitation data
        weighted_precip = precip_data * weights * area_fraction
        
        # Calculate area-weighted mean precipitation
        area_weighted_mean = np.nansum(weighted_precip) / np.nansum(weights * area_fraction)

    return area_weighted_mean
#------------------------------------------------------------

def load_ascii_data_to_xr(file_path):
    # Load the ASCII data into a 1D NumPy array
    data_1d = load_ascii_data(file_path)
    # data_1d = np.loadtxt(file_path)
    # data_1d = np.where(data_1d == -999, np.nan, data_1d)

    prdt = os.path.basename(file_path).split('_')[0]
    if prdt == 'amip6' and os.path.basename(file_path).endswith('_l'):
        prdt_nme = 'AMIP6-land'

    elif prdt == 'amip6' and os.path.basename(file_path).endswith('_o'):
        prdt_nme = 'AMIP6-ocean'

    elif prdt == 'amip6' and os.path.basename(file_path).endswith('_lo'):
        prdt_nme = 'AMIP6-combined'

    elif prdt == 'cmip6' and os.path.basename(file_path).endswith('_l'):
        prdt_nme = 'CMIP6-land'

    elif prdt == 'cmip6' and os.path.basename(file_path).endswith('_o'):
        prdt_nme = 'CMIP6-ocean'

    elif prdt == 'cmip6' and os.path.basename(file_path).endswith('_lo'):
        prdt_nme = 'CMIP6-combined'

    # Latitude array from south to north (as per the 2.5-degree grid resolution)
    lat = np.arange(-90 + 2.5 / 2, 90, 2.5)

    # Ensure the data and lat arrays have the correct size
    assert data_1d.size == lat.size, "Data size does not match the latitude grid size."

    # Create an xarray Dataset
    ds = xr.Dataset(
        {
            "zonal_mean_precip": (["lat"], data_1d)
        },
        coords={
            "lat": lat
        }
    )

    # ds = ds.reindex(lat=ds['lat'][::-1])


    return ds, prdt_nme
#%%
data_path = r'/ra1/pubdat/diabatic_heating_precipitation_200101_201812/data'
gpcp_data_path = r'/ra1/pubdat/AVHRR_CloudSat_proj/diabatic_heating_precipitation_200101_201812/data/GPCP_200101_201812/'
path_to_put_plots = r'/ra1/pubdat/diabatic_heating_precipitation_200101_201812/results/plots'

#%%
cde_run_dte = str(date.today().strftime('%Y%m%d'))

# Open the dataset and select the land-sea mask data
land_sea_mask_path = '/ra1/pubdat/AVHRR_CloudSat_proj/IMERG/ancillary_imerg_data/GPM_IMERG_LandSeaMask.2.nc4'
lsm_ds = xr.open_dataset(land_sea_mask_path)
lsm_arr = lsm_ds['landseamask']

# Transpose the data to get longitude on the x-axis
lsm_transposed = lsm_arr.transpose('lat', 'lon')

# Flip the latitude axis so that latitude is displayed south to north
lsm_flipped = lsm_transposed.isel(lat=slice(None, None, -1))

# Apply the land-sea mask condition
lsm = xr.where(lsm_flipped < 25, 1, 0)

cc = CRS.from_authority(code=4326,auth_name='EPSG')

lsm.rio.write_crs(cc.to_string(), inplace=True)

lsm = lsm.rio.reproject(lsm.rio.crs, 
                        shape=(72, 144), # set the shape as the autosnow data shape
                        resampling=Resampling.mode,)

lsm = lsm.rename({'x': 'lon', 'y': 'lat'})

# Assuming the mask variable is named 'mask' and it contains percentage values from 0 to 100
land_sea_mask = lsm_ds['landseamask']  # Replace 'mask' with the actual variable name if different
land_sea_mask.rio.write_crs(cc.to_string(), inplace=True)
land_sea_mask = land_sea_mask.transpose('lat', 'lon')

land_sea_mask = land_sea_mask.rio.reproject(land_sea_mask.rio.crs, 
                        shape=(72, 144), # set the shape as the autosnow data shape
                        resampling=Resampling.mode,)
# Apply the 75% threshold for ocean
# >= 75% means ocean, < 75% means land
ocean_mask = land_sea_mask >= 75
land_mask = land_sea_mask < 75

# Calculate the total number of grid cells per latitude band (assuming 'lon' is the longitude dimension)
total_cells_per_lat = land_sea_mask.shape[-1]  # This corresponds to the number of longitude points

# Calculate the area fraction for ocean and land for each latitude band
ocean_area_fraction = ocean_mask.sum(dim='x') / total_cells_per_lat
land_area_fraction = land_mask.sum(dim='x') / total_cells_per_lat

# Convert these to numpy arrays if needed
ocean_area_fraction = ocean_area_fraction.values
land_area_fraction = land_area_fraction.values
#%%
dhp_file = os.path.join(data_path,'diabatic_heating_precipitation_200101_201812.v2.nc')

dhp_data = xr.open_dataset(dhp_file)
# dhp_data_sel = dhp_data.sel(nm=0)
# Extract the latitude and longitude values
lat_values = dhp_data['latitude'].values
lon_values = dhp_data['longitude'].values

# Flip the latitude values
flipped_lat_values = lat_values[::-1]

# Flip the corresponding data variables (precip_heating in this case)
flipped_data = dhp_data['precip_heating'][:, ::-1, :]

# Extract the data arrays explicitly using the .data property
flipped_data_array = flipped_data.data
flipped_lat_array = flipped_lat_values

# Create a new dataset with flipped latitudes and data, with lon and lat as dimensions
aligned_dhp_data = xr.Dataset(
    {
        "precip_heating": (["nm", "lat", "lon"], flipped_data_array)
    },
    coords={
        "lat": (["lat"], flipped_lat_array),
        "lon": (["lon"], lon_values),
        "year": dhp_data["year"].data,
        "month": dhp_data["month"].data,
    }
)

aligned_dhp_data = aligned_dhp_data.where(aligned_dhp_data > 0)

aligned_dhp_data_sel = aligned_dhp_data.sel(nm=0)
aligned_dhp_data = aligned_dhp_data/29
aligned_dhp_data_sel = aligned_dhp_data.sel(nm=0)


aligned_dhp_data.rio.write_crs(cc.to_string(), inplace=True)

aligned_dhp_data = aligned_dhp_data.rename({'lon':'x', 'lat':'y'})

aligned_dhp_data = aligned_dhp_data.rio.reproject(aligned_dhp_data.rio.crs, 
                        shape=(72, 144), # set the shape as the autosnow data shape
                        resampling=Resampling.average,)


aligned_dhp_data_mean = aligned_dhp_data.mean(dim='nm',skipna=True)

#%%
gpcp_files = [os.path.join(gpcp_data_path,x) for x in os.listdir(gpcp_data_path) if x.endswith('.nc4')]

data_vals = []
for i in gpcp_files:
    gpcp_data = xr.open_dataset(i) 

    gpcp_data_time = pd.to_datetime(gpcp_data.coords['time'].values[0]).to_pydatetime().date()

    gpcp_data_ = gpcp_data.copy()

    gpcp_data_ = gpcp_data_.rename({'lon':'x', 'lat':'y'})

    # Write the CRS to the dataset
    gpcp_data_ = gpcp_data_.rio.write_crs(cc.to_string(), inplace=True)

    # Exclude non-spatial variables before reprojection
    spatial_vars = [var for var in gpcp_data_.data_vars if 'x' in gpcp_data_[var].dims and 'y' in gpcp_data_[var].dims]
    gpcp_data_spatial = gpcp_data_[spatial_vars]

    # Reproject the data to match the desired shape
    gpcp_data_spatial = gpcp_data_spatial.rio.reproject(
        gpcp_data_spatial.rio.crs, 
        shape=(72, 144),  # Set the shape as the desired shape
        resampling=Resampling.average,
    )

    # Combine the reprojected spatial data back with non-spatial data if needed
    gpcp_data_ = xr.merge([gpcp_data_spatial, gpcp_data_.drop_vars(spatial_vars)])

    gpcp_data_spatial = gpcp_data_spatial.rename({'x':'lon', 'y':'lat'})

    data_vals.append(gpcp_data_spatial)

# lon,lat  = gpcp_data_spatial.lon.values, gpcp_data_spatial.lat.values

gpcp_xr_data = xr.concat(data_vals, dim='time')

gpcp_data_mean = gpcp_xr_data.mean(dim='time',skipna=True)

# xt = gpcp_xr_data.groupby('lat').mean(dim=['time', 'lon'])

#%%
# zonal mean claculate
# Extract the time coordinate from gpcp_xr_data
time_coord = gpcp_xr_data.coords['time']

# Assign the time coordinate to aligned_dhp_data
aligned_dhp_data_with_time = aligned_dhp_data.assign_coords(time=time_coord)

dat_arr = [('precip_heating',aligned_dhp_data_with_time),('GPCP', gpcp_xr_data)]

gpcp_xr_data_sel = gpcp_xr_data.sel(time='2001-01-01')



# Example usage
nme = os.path.join(path_to_put_plots,'mean_maps_' + cde_run_dte + '.png')
plot_mean_maps(gpcp_data_mean, aligned_dhp_data_mean, filename=nme)


#%%
# AMIP6 and CIMP6 analysis
# Function to load the data into a NumPy array

path_to_amip_cimp_data = r'/ra1/pubdat/diabatic_heating_precipitation_200101_201812/data/zonalmeanprecip_AMIP6_CMIP6'

amip_cimp_files = [os.path.join(path_to_amip_cimp_data,d) for d in os.listdir(path_to_amip_cimp_data)]



# Load all files into a list of NumPy arrays
data_arrays = [load_ascii_data_to_xr(file_path) for file_path in amip_cimp_files]

cmip6_dats = [x for x in data_arrays if x[1].startswith('CMIP6')]
amip6_dats = [x for x in data_arrays if x[1].startswith('AMIP6')]

# zonal means 
dhp_znl_cmb, dhp_znl_lnd, dhp_znl_oc = zonal_compute(aligned_dhp_data_with_time,'dhp')
gpcp_znl_cmb, gpcp_znl_lnd, gpcp_znl_oc = zonal_compute(gpcp_xr_data,'gpcp')

zonal_means = {}
zonal_means['GPCP'] = {
        'COMBINED': gpcp_znl_cmb,
        'LAND': gpcp_znl_lnd,
        'OCEAN': gpcp_znl_oc,}

zonal_means['Diabatic precip_heating'] = {
        'COMBINED': dhp_znl_cmb,
        'LAND': dhp_znl_lnd,
        'OCEAN': dhp_znl_oc,}

zonal_means['CMIP6'] = {
        'COMBINED': [x for x in cmip6_dats if 'combined' in x[1]][0][0],
        'LAND': [x for x in cmip6_dats if 'land' in x[1]][0][0],
        'OCEAN': [x for x in cmip6_dats if 'ocean' in x[1]][0][0],}

zonal_means['AMIP6'] = {
        'COMBINED': [x for x in amip6_dats if 'combined' in x[1]][0][0],
        'LAND': [x for x in amip6_dats if 'land' in x[1]][0][0],
        'OCEAN': [x for x in amip6_dats if 'ocean' in x[1]][0][0],}



nme = os.path.join(path_to_put_plots,'zonal_mean_maps_' + cde_run_dte + '.png')

plot_zonal_means(zonal_means, ylabel="Mean Precipitation (mm/day)", xlabel="Latitude",filename=nme)



#%%
mean_df = pd.DataFrame(columns=['GPCP', 'Diabatic precip_heating', 'AMIP6', 'CMIP6'],
                       index=['Combined', 'Land', 'Ocean'])


# Load the land-sea mask
ls_msk = r'/ra1/pubdat/AVHRR_CloudSat_proj/IMERG/ancillary_imerg_data/GPM_IMERG_LandSeaMask.2.nc4'

mask_data = xr.open_dataset(ls_msk)
land_sea_mask = mask_data['landseamask']


land_sea_mask.rio.write_crs(cc.to_string(), inplace=True)
land_sea_mask = land_sea_mask.transpose('lat', 'lon')

land_sea_mask_ = land_sea_mask.rio.reproject(land_sea_mask.rio.crs, 
                        shape=(72, 144), # set the shape as the autosnow data shape
                        resampling=Resampling.bilinear,)

# Ensure latitudes are from south to north to match ASCII file
land_sea_mask_ = land_sea_mask_.sortby('y', ascending=True)

land_sea_mask_bin = xr.where(land_sea_mask_ < 25,1,0).astype(float)
land_mask_ = (land_sea_mask_bin == 1).astype(float)
ocean_mask_ = (land_sea_mask_bin == 0).astype(float)

# Define the latitude array (assuming it's 2.5-degree resolution from south to north)
latitudes = np.arange(-90 + 2.5 / 2, 90, 2.5) #np.linspace(-90, 90, 72)#[::-1]

# Reshape or interpolate the mask data to match the ASCII data resolution if necessary
land_mask = (land_sea_mask_ < 75).astype(float)  # Convert boolean mask to float for multiplication
ocean_mask = (land_sea_mask_ >= 75).astype(float)

# Ensure that masks have the correct latitudinal order
ocean_mask = ocean_mask.sortby('y', ascending=True)
land_mask = land_mask.sortby('y', ascending=True)

# Calculate the area fraction for each latitude band
land_fraction = land_mask.mean(dim='x')
ocean_fraction = ocean_mask.mean(dim='x')

# Print to check the area fractions
# print("Land Area Fraction per Latitude Band:", land_fraction.values)
# print("Ocean Area Fraction per Latitude Band:", ocean_fraction.values)



# Load data
amip6_land_file = r'/ra1/pubdat/diabatic_heating_precipitation_200101_201812/data/zonalmeanprecip_AMIP6_CMIP6/amip6_28model_m_1979_2014_y_l'
amip6_ocean_file = r'/ra1/pubdat/diabatic_heating_precipitation_200101_201812/data/zonalmeanprecip_AMIP6_CMIP6/amip6_28model_m_1979_2014_y_o'
amip6_lo_file = r'/ra1/pubdat/diabatic_heating_precipitation_200101_201812/data/zonalmeanprecip_AMIP6_CMIP6/amip6_28model_m_1979_2014_y_lo'


cmip6_land_file = r'/ra1/pubdat/diabatic_heating_precipitation_200101_201812/data/zonalmeanprecip_AMIP6_CMIP6/cmip6_28model_m_1979_2014_y_l'
cmip6_ocean_file = r'/ra1/pubdat/diabatic_heating_precipitation_200101_201812/data/zonalmeanprecip_AMIP6_CMIP6/cmip6_28model_m_1979_2014_y_o'
cmip6_lo_file = r'/ra1/pubdat/diabatic_heating_precipitation_200101_201812/data/zonalmeanprecip_AMIP6_CMIP6/cmip6_28model_m_1979_2014_y_lo'

amip6_precip_data_land = load_ascii_data(amip6_land_file)
amip6_precip_data_ocean = load_ascii_data(amip6_ocean_file)
amip6_precip_data_lo = load_ascii_data(amip6_lo_file)

cmip6_precip_data_land = load_ascii_data(cmip6_land_file)
cmip6_precip_data_ocean = load_ascii_data(cmip6_ocean_file)
cmip6_precip_data_lo = load_ascii_data(cmip6_lo_file)

mean_df.loc['Combined', 'GPCP'] = calculate_area_weighted_mean(gpcp_znl_cmb['sat_gauge_precip'],gpcp_znl_cmb.lat.values,
                                                              None,'cmb').round(2)

# arrange the lat values to conform to land_area_fraction
gpcp_znl_lnd_ = gpcp_znl_lnd.sortby('lat', ascending=True)

mean_df.loc['Land', 'GPCP'] = calculate_area_weighted_mean(gpcp_znl_lnd['sat_gauge_precip'],gpcp_znl_lnd.lat.values,
                                                               land_area_fraction,'l').round(2)

gpcp_znl_o_ = gpcp_znl_oc.sortby('lat', ascending=True)

mean_df.loc['Ocean', 'GPCP'] = calculate_area_weighted_mean(gpcp_znl_oc['sat_gauge_precip'],gpcp_znl_oc.lat.values,
                                                               ocean_area_fraction,'o').round(2)
#---------------------------
mean_df.loc['Combined', 'Diabatic precip_heating'] = calculate_area_weighted_mean(dhp_znl_cmb['precip_heating'],dhp_znl_cmb.lat.values,
                                                              None,'cmb').round(2)

# arrange the lat values to conform to land_area_fraction
dhp_znl_lnd_ = dhp_znl_lnd.sortby('lat', ascending=True)

mean_df.loc['Land', 'Diabatic precip_heating'] = calculate_area_weighted_mean(dhp_znl_lnd['precip_heating'],dhp_znl_lnd.lat.values,
                                                               land_area_fraction,'l').round(2)

dhp_znl_o_ = dhp_znl_oc.sortby('lat', ascending=True)

mean_df.loc['Ocean', 'Diabatic precip_heating'] = calculate_area_weighted_mean(dhp_znl_oc['precip_heating'],dhp_znl_oc.lat.values,
                                                               ocean_area_fraction,'o').round(2)

# Define latitudes
# latitudes = np.linspace(-90, 90, 72)

# Calculate weighted means
mean_df.loc['Land', 'AMIP6'] = calculate_area_weighted_mean(amip6_precip_data_land, latitudes, land_fraction,'l').round(2)
mean_df.loc['Ocean', 'AMIP6'] = calculate_area_weighted_mean(amip6_precip_data_ocean, latitudes, ocean_fraction,'o').round(2)
mean_df.loc['Combined', 'AMIP6'] = calculate_area_weighted_mean(amip6_precip_data_lo, latitudes, None,'cmb').round(2)


mean_df.loc['Land', 'CMIP6'] = calculate_area_weighted_mean(cmip6_precip_data_land, latitudes, land_fraction,'l').round(2)
mean_df.loc['Ocean', 'CMIP6'] = calculate_area_weighted_mean(cmip6_precip_data_ocean, latitudes, ocean_fraction,'o').round(2)
mean_df.loc['Combined', 'CMIP6'] = calculate_area_weighted_mean(cmip6_precip_data_lo, latitudes, None,'cmb').round(2)

nme = '_'.join(['mean_df', cde_run_dte]) + '.csv'
nme = os.path.join(r'/ra1/pubdat/diabatic_heating_precipitation_200101_201812/results/', nme)
mean_df.to_csv(nme)
