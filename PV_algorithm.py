import math
import datetime
import matplotlib.pyplot as plt
from DataParser import load_data

# Savona Parameters
LATITUDE_ANGLE = 44.298611
LONGITUDE_ANGLE = 8.448333
STANDARD_MERIDIAN = 15

TILT_ANGLE = 15
AZIMUTH_ANGLE = -30
GROUND_ALBEDO = 0.2
P_MAX_STC = 240
COEFF_P_MAX = -0.0043
NOC_TEMP = 43


# ---------- GENERAL FUNCTIONS ----------
def sin(deg):
    return math.sin(math.radians(deg))


def cos(deg):
    return math.cos(math.radians(deg))


# formula 1
# day variable is the day in the year in number from 1 to 365
def _extraterrestrial_irradiance(time_data):
    day_of_year = time_data.timetuple().tm_yday
    return 1376 * (1 + 0.033 * math.cos((2 * math.pi * (day_of_year / 365))))


# formula 2
# Declination angle is the angle between a plane perpendicular to incoming solar radiation and the rotational axis of
# the earth.
# the equation is calculated in radians
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
def _daylight_saving_correction(time_data):
    start_date = datetime.datetime(2018, 3, 25, 3)
    end_date = datetime.datetime(2018, 10, 28, 2)
    if start_date <= time_data < end_date:
        return 0
    else:
        return 1


# formula 5,6
# E- Equation of time [hr]- the difference between local solar time ,LST and the local Civil time,
# LCT is called the time equation- see ahead
def _equation_of_time(time_data):
    day_of_year = time_data.timetuple().tm_yday
    B = (360 * (day_of_year - 81)) / 365
    return 0.165 * sin(2*B) - 0.126 * cos(B) - 0.025 * sin(B)


# ---------- PV Predictor ----------
class PVPredictor(object):
    def __init__(self, tilt=TILT_ANGLE, azimuth=AZIMUTH_ANGLE, ground_albido=GROUND_ALBEDO, latitude=LATITUDE_ANGLE,
                 longitude=LONGITUDE_ANGLE, std_meridian=STANDARD_MERIDIAN, p_max_stc=P_MAX_STC,
                 coeff_p_max=COEFF_P_MAX, noc_temp=NOC_TEMP):
        self.tilt = tilt
        self.azimuth = azimuth
        self.ground_albido = ground_albido
        self.latitude = latitude
        self.longitude = longitude
        self.std_meridian = std_meridian
        self.p_max_stc = p_max_stc
        self.coeff_p_max = coeff_p_max
        self.noc_temp = noc_temp

    # formula 3
    # hour angle
    # time variable is local civil time
    def _hour_angle(self, time_data):
        solar_time = self._local_solar_time(time_data)
        return 15 * (solar_time - 12)

    def _local_solar_time(self, time_data):
        clock_time = time_data.hour + (time_data.minute + time_data.second / 60) / 60
        return clock_time + (1 / 15) * (self.longitude - self.std_meridian) + _equation_of_time(time_data) - \
            _daylight_saving_correction(time_data)

    # formula 9
    # cos(zenith_angle) calculation
    def _cos_zenith_angle(self, time_data):
        dec_angle = _declination_angle(time_data)
        hr_angle = self._hour_angle(time_data)
        return sin(dec_angle) * sin(self.latitude) + cos(dec_angle) * cos(self.latitude) * cos(hr_angle)

    # formula 23
    # cos(total_angle) calculation
    def _cos_total_angle(self, time_data):
        cos_z = self._cos_zenith_angle(time_data)
        W = cos(self.tilt) / cos_z
        a = sin(self.tilt)
        b = cos(self.tilt) * math.sin(math.acos(cos_z)) / cos_z
        return 0.5 * (W + (1/W) - (b**2/W) - (a**2/W)) + \
            (a*b/W) * cos(self.azimuth - self.tilt)

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
            0.5 * self.ground_albido * measured_irradiance * (1 - cos_tilt)

    # formula 20
    # total output power
    def output_power(self, time_data, measured_irradiance, amb_temp):
        total_irradiance = self.total_irradiance(time_data, measured_irradiance)
        cell_temp = ((self.noc_temp - 20) / 800) * total_irradiance + amb_temp

        return self.p_max_stc * (total_irradiance / 1000) * \
            (1 + self.coeff_p_max * (cell_temp - 25))


def main():
    # A few tests
    pv_pred = PVPredictor()

    print()
    data, output = load_data()

    n = len(data['datetime'])
    x = []
    pred = []
    out = []
    prev_percent = 0
    for i in range(0, n, 100):
        x.append(365 * i / n)
        percent = int(100 * i / n)
        if percent > prev_percent:
            print(percent)
            prev_percent = percent
        pred.append(pv_pred.total_irradiance(data['datetime'][i], data['irradiance'][i]))
        j = min(list(range(len(output['datetime']))),
                key=lambda x: abs(output['datetime'][x] - data['datetime'][i]))
        out.append(output['radiation'][j])

    plt.plot(x, pred, label='Predicted Radiation')
    plt.plot(x, out, label='Actual Radiation')
    plt.ylim(-100, 2000)
    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()
