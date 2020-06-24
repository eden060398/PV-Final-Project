import requests
from timezonefinder import TimezoneFinder
import pytz
import dateutil.parser as DP
import datetime


class DataRetriever:
    def __init__(self, latitude, longitude, tilt=None, azimuth=None):
        self.latitude = latitude
        self.longitude = longitude
        self.tilt = tilt
        self.azimuth = azimuth

        self.timezone = pytz.timezone(TimezoneFinder().timezone_at(lng=longitude, lat=latitude))

    def get_data(self, year=2014):
        params = {'lat': self.latitude,
                  'lon': self.longitude,
                  'outputformat': 'json',
                  'startyear': year,
                  'endyear': year}
        if self.tilt is not None and self.azimuth is not None:
            params['angle'] = self.tilt
            params['aspect'] = self.azimuth
        else:
            params['optimalangles'] = 1
        r = requests.get('https://re.jrc.ec.europa.eu/api/seriescalc', params=params)

        if not r.ok:
            return None

        raw_data = r.json()
        datetimes = [pytz.utc.localize(DP.isoparse(dp['time']), is_dst=None).astimezone(self.timezone)
                     for dp in raw_data['outputs']['hourly']]
        irradiances = [dp['G(i)'] for dp in raw_data['outputs']['hourly']]
        temps = [dp['T2m'] for dp in raw_data['outputs']['hourly']]

        data = {'datetime': datetimes, 'irradiance': irradiances, 'temp': temps}
        tilt = raw_data['inputs']['mounting_system']['fixed']['slope']['value']
        azimuth = raw_data['inputs']['mounting_system']['fixed']['azimuth']['value']

        dt = datetime.datetime(year, 1, 1)
        utc_offset = self.timezone.utcoffset(dt) - self.timezone.dst(dt)
        std_meridian = (utc_offset.total_seconds() / 3600) * 15

        return data, tilt, azimuth, std_meridian
