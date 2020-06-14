import requests
from timezonefinder import TimezoneFinder
import pytz
import dateutil.parser as DP
import datetime


class DataRetriever:
    def __init__(self, latitude, longitude, compute_optimal=True):
        self.latitude = latitude
        self.longitude = longitude
        self.compute_optimal = 1 if compute_optimal else 0

        self.timezone = pytz.timezone(TimezoneFinder().timezone_at(lng=longitude, lat=latitude))

    def get_data(self, year=2016):
        params = {'lat': self.latitude,
                  'lon': self.longitude,
                  'outputformat': 'json',
                  'startyear': year,
                  'endyear': year,
                  'optimalangles': self.compute_optimal}
        r = requests.get('https://re.jrc.ec.europa.eu/api/seriescalc', params=params)

        if not r.ok:
            return None

        raw_data = r.json()
        datetimes = [pytz.utc.localize(DP.isoparse(dp['time']), is_dst=None).astimezone(self.timezone)
                     for dp in raw_data['outputs']['hourly']]
        irradiances = [dp['G(i)'] for dp in raw_data['outputs']['hourly']]
        temps = [dp['T2m'] for dp in raw_data['outputs']['hourly']]

        return {'datetime': datetimes, 'irradiance': irradiances, 'temp': temps}


dr = DataRetriever(45, 8)
dr.get_data()
