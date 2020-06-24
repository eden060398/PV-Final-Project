import math
import datetime
from timezonefinder import TimezoneFinder
import pytz
import dateutil.parser as DP

GROUND_ALBEDO = 0.2

# ---------- GENERAL FUNCTIONS ----------
def sin(deg):
    return math.sin(math.radians(deg))


def cos(deg):
    return math.cos(math.radians(deg))


def asin(x):
    return math.degrees(math.asin(x))


def acos(x):
    return math.degrees(math.acos(x))


# formula 1
# day variable is the day in the year in number from 1 to 365
def _extraterrestrial_irradiance(time_data):
    day_of_year = time_data.timetuple().tm_yday
    return 1376 * (1 + 0.033 * math.cos((2 * math.pi * (day_of_year / 365))))


# formula 2
# Declination angle is the angle between a plane perpendicular to incoming solar radiation and the rotational axis of
# the earth.
def _declination_angle(time_data):
    day_of_year = time_data.timetuple().tm_yday
    return 23.45 * sin((360 * (day_of_year + 284)) / 365)


# formula 4
# LST- local solar time [hr]
# CT- Clock time [hr]
# Lstd- standard meridian for the local time zone [degrees west]- in Savona 150
# Lloc- Longitude of actual location [degrees west]- in Savona 8026'54''E
# E- Equation of time [hr]- the difference between local solar time ,LST and the local Civil time,
# LCT is called the time equation- see ahead
# DT- Daylight saving correction (DT=0 if not on Daylight Saving Time,
# otherwise DT is equal to the number of hours that the time is advanced for Daylight savings time, usually 1hr)-
# in Savona there is daylight saving so depending on the day needs to be taken into account.

# day light saving in Savona 2018: ( taken from https://www.horlogeparlante.com/history-english.html?city=3167022)
# Transition to daylight saving time on Sunday 25 March 2018 - 03 h 00 (GMT + 2 h ) CEST
# Back to standard time on Sunday 28 October 2018 - 02 h 00 (GMT + 1 h ) CET
# we calculated the longitude degree according to https://www.fcc.gov/media/radio/dms-decimal and we got that the
# longitude degree is 8.431667
def _daylight_saving_correction(time_data, timezone):
    if time_data.tzinfo is None or time_data.tzinfo.utcoffset(time_data) is None:
        return timezone.dst(time_data, is_dst=True).total_seconds() / 3600
    else:
        return time_data.dst().total_seconds() / 3600


# formula 5,6
# E- Equation of time [hr]- the difference between local solar time ,LST and the local Civil time,
# LCT is called the time equation- see ahead
def _equation_of_time(time_data):
    day_of_year = time_data.timetuple().tm_yday
    B = (360 * (day_of_year - 81)) / 365
    return 0.165 * sin(2*B) - 0.126 * cos(B) - 0.025 * sin(B)


def compute_daily_average(datetimes, values, hour_range=None):
        daily_avgs = []

        cur_date = None
        prev_time = None
        day_vals = []
        day_deltas = []

        for time_data, val in zip(datetimes, values):
            if hour_range is None or hour_range[0] <= time_data.hour < hour_range[1]:
                if cur_date is None:
                    cur_date = time_data.date()
                elif cur_date != time_data.date():
                    total = sum(delta * (day_vals[i] + day_vals[i+1]) / 2 for i, delta in enumerate(day_deltas))
                    daily_avgs.append((cur_date, total))
                    prev_time = None
                    day_vals = []
                    day_deltas = []
                    cur_date = time_data.date()

                day_vals.append(val)
                if prev_time is not None:
                    day_deltas.append((time_data - prev_time).total_seconds() / 86400)
                prev_time = time_data
        if cur_date is not None:
            total = sum(delta * (day_vals[i] + day_vals[i+1]) / 2 for i, delta in enumerate(day_deltas))
            daily_avgs.append((cur_date, total))

        return daily_avgs


# ---------- PV Predictor ----------
class PVPredictor:
    def __init__(self, tilt, azimuth, latitude, longitude, std_meridian, p_max_stc, coeff_p_max, noc_temp,
                 ground_albedo=GROUND_ALBEDO):
        self.tilt = tilt
        self.azimuth = azimuth
        self.ground_albedo = ground_albedo
        self.latitude = latitude
        self.longitude = longitude
        self.std_meridian = std_meridian
        self.p_max_stc = p_max_stc
        self.coeff_p_max = coeff_p_max
        self.noc_temp = noc_temp

        self.timezone = pytz.timezone(TimezoneFinder().timezone_at(lng=longitude, lat=latitude))

    # formula 3
    # hour angle
    # time variable is local civil time
    def _hour_angle(self, time_data):
        solar_time = self._local_solar_time(time_data)
        return 15 * (solar_time - 12)

    def _local_solar_time(self, time_data):
        clock_time = time_data.hour + (time_data.minute + time_data.second / 60) / 60
        return clock_time + (1 / 15) * (self.longitude - self.std_meridian) + _equation_of_time(time_data) - \
            _daylight_saving_correction(time_data, self.timezone)

    # formula 9
    # cos(zenith_angle) calculation
    def _cos_zenith_angle(self, time_data):
        dec_angle = _declination_angle(time_data)
        hr_angle = self._hour_angle(time_data)
        return sin(dec_angle) * sin(self.latitude) + cos(dec_angle) * cos(self.latitude) * cos(hr_angle)

    def _sun_azimuth(self, time_data):
        dec_angle = _declination_angle(time_data)
        hr_angle = self._hour_angle(time_data)
        sin_z = math.sin(math.acos(self._cos_zenith_angle(time_data)))
        cos_azimuth = (sin(dec_angle)*cos(self.latitude) - cos(dec_angle)*sin(self.latitude)*cos(hr_angle)) / (-sin_z)
        azimuth = acos(cos_azimuth)
        return azimuth

        # formula 23
    # cos(total_angle) calculation
    def _cos_total_angle(self, time_data):
        # dec_angle = _declination_angle(time_data)
        # return cos(self.latitude - dec_angle - self.tilt)
        cos_z = self._cos_zenith_angle(time_data)
        sun_azimuth = self._sun_azimuth(time_data)
        W = cos(self.tilt) / cos_z
        a = sin(self.tilt)
        b = cos(self.tilt) * math.sin(math.acos(cos_z)) / cos_z
        return 0.5 * (W + (1 - b**2 - a**2) / W) + \
            (a*b/W) * cos(sun_azimuth - self.azimuth)

    # formula 10 (and 8)
    # clearness index calculation
    def _clearness_index(self, time_data, measured_irradiance):
        return measured_irradiance / (_extraterrestrial_irradiance(time_data) * self._cos_zenith_angle(time_data))

    # formula 11
    # diffused irradiance
    def _diffused_irradiance(self, time_data, measured_irradiance):
        return (1 - 1.13 * self._clearness_index(time_data, measured_irradiance)) * measured_irradiance

    # formula 17
    # total irradiance
    def total_irradiance(self, time_data, measured_irradiance):
        diffused_ird = self._diffused_irradiance(time_data, measured_irradiance)
        direct_ird = measured_irradiance - diffused_ird
        cos_tilt = cos(self.tilt)

        return direct_ird * (self._cos_total_angle(time_data) / self._cos_zenith_angle(time_data)) + \
            0.5 * diffused_ird * (1 + cos_tilt) + \
            0.5 * self.ground_albedo * measured_irradiance * (1 - cos_tilt)

    # formula 20
    # total output power [kW]
    def output_power(self, time_data, measured_irradiance, amb_temp):
        total_irradiance = self.total_irradiance(time_data, measured_irradiance)
        cell_temp = ((self.noc_temp - 20) / 800) * total_irradiance + amb_temp

        return self.p_max_stc * (total_irradiance / 1000) * \
            (1 + self.coeff_p_max * (cell_temp - 25))

    def compute_rad_predictions(self, datetimes, irradiances):
        predictions = []
        for time_data, irrad in zip(datetimes, irradiances):
            predictions.append(self.total_irradiance(time_data, irrad))

        return predictions

    def compute_power_predictions(self, datetimes, irradiances, temps):
        predictions = []
        for time_data, irrad, amb_temp in zip(datetimes, irradiances, temps):
            predictions.append(self.output_power(time_data, irrad, amb_temp))

        return predictions

    def compute_daily_irradiance(self, datetimes, irradiances, hour_range=None):
        return compute_daily_average(datetimes, self.compute_rad_predictions(datetimes, irradiances),
                                     hour_range=hour_range)

    def compute_daily_power(self, datetimes, irradiances, temps, hour_range=None):
        return compute_daily_average(datetimes, self.compute_power_predictions(datetimes, irradiances, temps),
                                     hour_range=hour_range)
