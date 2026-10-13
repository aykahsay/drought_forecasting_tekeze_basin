Now that you have cloned the code onto the new 13th Gen machine, the very first step before we can run any models or build the dashboard is to get the massive historical climate datasets (Temperature, Soil Moisture, and Precipitation) onto that computer.

Since we are building a state-of-the-art ML model, we need the gold-standard data from the European Space Agency's **Copernicus Climate Data Store (CDS)** (for ERA5 soil/temp data) and **CHIRPS** (for rainfall). 

Here is exactly how to download the data directly onto your new machine:

### Step 1: Create a Copernicus Account (Free)
1. Go to the [Copernicus Climate Data Store (CDS)](https://cds.climate.copernicus.eu/user/register) and create a free account.
2. Once logged in, go to your **Profile** (top right) to find your **Personal API Key** and your **UID**.

### Step 2: Install the CDS API Key on the New Machine
Your Python scripts need this key to talk to the satellite servers. On your new machine:
1. Create a file in your home directory. 
   * **Windows:** `C:\Users\YourUsername\.cdsapirc`
   * **Mac/Linux:** `~/.cdsapirc`
2. Open that file and paste your credentials exactly like this:
```text
url: https://cds.climate.copernicus.eu/api/v2
key: YOUR_UID:YOUR_API_KEY
```

### Step 3: Run the Ingestion Script
We already have ingestion scripts built into the AI-DREWS architecture! Open the VS Code terminal on the new machine and make sure your virtual environment is activated (`venv\Scripts\activate`). 

You can run a Python script to trigger the automated download of the NetCDF data for Ethiopia. (You can create a quick script called `download_data.py` on that machine to pull the ERA5 data):

```python
# Create download_data.py and run it
import cdsapi

c = cdsapi.Client()

print("Downloading 40-years of Ethiopia Soil Moisture & Temperature (ERA5)...")
c.retrieve(
    'reanalysis-era5-land',
    {
        'variable': [
            'volumetric_soil_water_layer_1',
            'skin_temperature',
        ],
        'year': [str(y) for y in range(1981, 2024)],
        'month': [str(i).zfill(2) for i in range(1, 13)],
        'day': [str(i).zfill(2) for i in range(1, 32)],
        'time': '12:00', # Daily noon snapshot
        # Bounding box for Ethiopia: North, West, South, East
        'area': [15.0, 33.0, 3.0, 48.0],
        'format': 'netcdf',
    },
    'data/raw/ethiopia_historical_climate.nc')
print("Download complete!")
```

*(Note: Depending on your internet speed, downloading 40 years of daily satellite NetCDF data could take several hours!)*

### Step 4: CHIRPS Rainfall Data
For precipitation, you don't need an API key. You can download the CHIRPS Africa NetCDF files directly from the UCSB Climate Hazards Group FTP server:
* Go to: `ftp://ftp.chg.ucsb.edu/pub/org/chg/products/CHIRPS-2.0/africa_daily/netcdf/`
* Download the `.nc` files and put them in your `data/raw/` folder.

Once you kick off that download on the new machine, what task would you like to focus on here on this machine while we wait? We can start building the gorgeous **HTML Dashboard** so the UI is ready!
