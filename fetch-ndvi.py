import geemap ### packge for google earth engine analysis 

import ee ### packge neccsary for using geemap
import os 

import ee
import geemap
import datetime

from seleniumbase import SB

with SB(uc=True) as sb:
    # sb.open("https://www.google.com/gmail/about/")
    sb.open('https://accounts.google.com/o/oauth2/v2/auth/oauthchooseaccount?access_type=offline&client_id=522309567947-3h37mfqnb5uuglmuqo1vv3qhngmkorrk.apps.googleusercontent.com&enable_granular_consent=true&login_hint=your_gmail%40gmail.com&prompt=consent&redirect_uri=https%3A%2F%2Fcolab.research.google.com%2Ftun%2Fm%2Fauth-user-ephem&response_type=none%20gsession&scope=openid%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive&state=%7B%22token%22%3A%22WjoFIpEElC2vGdEric7WrQMUxao%3A1715106703679%22%2C%22endpoint%22%3A%22m-s-1hslxdoqsngqw%22%2C%22scopes%22%3A%5B%22openid%22%2C%22https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email%22%2C%22https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform%22%2C%22https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive%22%5D%7D&service=lso&o2v=2&ddm=0&flowName=GeneralOAuthFlow')
    # sb.click('a[data-action="sign in"]')
    sb.click('button:contains("Next")')
    sb.sleep(8)
    sb.type('input[type="password"]', 'please insert your pass')
    sb.click('button:contains("Next")')
    sb.sleep(8)
    sb.click('/html/body/div[1]/div[1]/div[2]/c-wiz/div/div[3]/div/div/div[2]/div/div/button/div[1]')
    sb.sleep(8)
    sb.click('/html/body/div[1]/div[1]/div[2]/div/div/div[3]/div/div[1]/div[2]/div/div/button/div[3]')
    sb.sleep(8)
    sb.open('https://colab.research.google.com/drive/1fp3XeJQKmaazhodfENi3p0pHxg_tXMmz#scrollTo=3Yb18zUWaaSh')
    sb.sleep(5)    
    try:
        ee.Authenticate() ### authenticate to google earth engine
        # map = geemap.Map()

        ee.Initialize(project='ee-hamoazni2')

        geemap.ee_initialize()
        # Create a list of extents
        extents = [
            {
                'name': 'bi',
                'geometry': ee.Geometry.Polygon([[[-154.668, 18.849],[-154.668, 20.334],[-156.243, 20.334],[-156.243, 18.849]]]),
            },
            {
                'name': 'ka',
                'geometry': ee.Geometry.Polygon([[[-159.2512, 21.819],[-159.2512, 22.269],[-159.816, 22.269],[-159.816, 21.819]]]),
            },
            {
                'name': 'mn',
                'geometry': ee.Geometry.Polygon([[[-155.9257, 20.343],[-155.9257, 21.32175],[-157.35, 21.32175],[-157.35, 20.343]]]),
            },
            {
                'name': 'oa',
                'geometry': ee.Geometry.Polygon([[[-157.602, 21.18],[-157.602, 21.7425],[-158.322, 21.7425],[-158.322, 21.18]]]),
            }
        ]

        # Loop through each extent
        for extent in extents:
            # Create a Map for visualization
            Map = geemap.Map()
            Map.centerObject(extent['geometry'])
            Map.addLayer(extent['geometry'], {'color': 'red'}, extent['name'])

            # Load MODIS data
            modis = ee.ImageCollection('MODIS/061/MOD09GA')

            # # Define date range and other parameters
            # startDate = ee.Date('2023-08-29')
            # endDate = ee.Date('2023-09-19')

# Get today's date
            today = datetime.date.today()

            # Calculate the date 70 days before today
            days_before = 70
            start_date = today - datetime.timedelta(days=days_before)

            # Convert dates to strings in the format Earth Engine expects
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = today.strftime('%Y-%m-%d')

            # Create Earth Engine Date objects
            startDate = ee.Date(start_date_str)
            endDate = ee.Date(end_date_str)
                     
            interval = 16
            dates = ee.List.sequence(startDate.millis(), endDate.millis(), interval * 24 * 60 * 60 * 1000)

            # Loop over the dates
            date_list = dates.getInfo()
            for dateMillis in date_list:
                date = ee.Date(dateMillis)

                # Filter the collection for the current date and extent
                filtered = modis.filterDate(date, date.advance(interval, 'day')).filterBounds(extent['geometry'])

                # Cloud masking function
                def maskMODISclouds(image):
                    qa = image.select('state_1km')
                    cloudBitMask = 1 << 10
                    mask = qa.bitwiseAnd(cloudBitMask).eq(0)
                    return image.updateMask(mask)

                filtered1 = filtered.map(maskMODISclouds)

                # NDVI calculation function
                def addNDVI(image):
                    ndvi = image.normalizedDifference(['sur_refl_b02', 'sur_refl_b01']).rename('ndvi')
                    return image.addBands(ndvi)

                withNdvi = filtered1.map(addNDVI)

                # Gap-filling function
                def fill(image):
                    ima = image.focal_mean(1, 'square', 'pixels', 20)
                    return ima.blend(image)

                filled = withNdvi.map(fill)

                # Clip NDVI based on the extent
                NDVIsen = filled.median().clip(extent['geometry'])
        # Create a folder based on the extent's name
                folder_name = extent['name']
                out_dir = os.path.expanduser(f'./{end_date_str}/NDVI final/{folder_name}')
                
                # Ensure the folder exists or create it if not
                os.makedirs(out_dir, exist_ok=True)

                # Export the image to the folder with a unique name
                file_name = f'{extent["name"]}_NDVI_{date.format("YYYYMMdd").getInfo()}.tif'
                file_path = os.path.join(out_dir, file_name)

                geemap.ee_export_image(NDVIsen.select('ndvi'), filename=file_path, scale=250, region=extent['geometry'])
    except:
        print('error')