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
P_MAX_STC = 80
COEFF_P_MAX = -0.0043
NOC_TEMP = 43


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


def compute_daily_average(datetimes, values):
        daily_avgs = []
        cur_date = None
        total = 0
        count = 0
        for time_data, val in zip(datetimes, values):
            if 10 <= time_data.hour < 16:
                if cur_date is None:
                    cur_date = time_data.date()
                elif cur_date != time_data.date():
                    daily_avgs.append((cur_date, total / count))
                    total = 0
                    count = 0
                    cur_date = time_data.date()
                total += val
                count += 1
        if cur_date is not None:
            daily_avgs.append((cur_date, total / count))

        return daily_avgs


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

    def _sun_azimuth(self, time_data):
        dec_angle = _declination_angle(time_data)
        hr_angle = self._hour_angle(time_data)
        sin_z = math.sin(math.acos(self._cos_zenith_angle(time_data)))
        cos_azimuth = (sin(dec_angle)*cos(self.latitude) - cos(dec_angle)*sin(self.latitude)*cos(hr_angle)) / (-sin_z)
        azimuth = acos(cos_azimuth)
        # if hr_angle > 0:
        #     azimuth = 360 - azimuth
        return azimuth

        # formula 23
    # cos(total_angle) calculation
    def _cos_total_angle(self, time_data):
        dec_angle = _declination_angle(time_data)
        return cos(self.latitude - dec_angle - self.tilt)
        # cos_z = self._cos_zenith_angle(time_data)
        # sun_azimuth = self._sun_azimuth(time_data)
        # W = cos(self.tilt) / cos_z
        # a = sin(self.tilt)
        # b = cos(self.tilt) * math.sin(math.acos(cos_z)) / cos_z
        # return 0.5 * (W + (1 - b**2 - a**2) / W) + \
        #     (a*b/W) * cos(sun_azimuth - self.azimuth)

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

    def compute_daily_irradiance(self, datetimes, irradiances):
        return compute_daily_average(datetimes, self.compute_rad_predictions(datetimes, irradiances))

    def compute_daily_power(self, datetimes, irradiances, temps):
        return compute_daily_average(datetimes, self.compute_power_predictions(datetimes, irradiances, temps))


def main():
    # A few tests
    pv_pred = PVPredictor()

    data, output = load_data()

    daily_pred_avgs = pv_pred.compute_daily_irradiance(data['datetime'], data['irradiance'])
    daily_meas_avg = compute_daily_average(output['datetime'], output['radiation'])

    dates_pred, pred = list(zip(*daily_pred_avgs))
    dates_meas, meas = list(zip(*daily_meas_avg))

    mae = 100 * sum(abs(a - b) / b for a, b in zip(pred, meas) if b > 200) / len(meas)
    print('Irradiance MAE:', round(mae, 2), '%')

    plt.plot(dates_pred, pred, label='Predicted Radiation')
    plt.plot(dates_meas, meas, label='Actual Radiation')
    # plt.ylim(-100, 2000)
    plt.legend()
    plt.show()

    daily_pred_avgs = pv_pred.compute_daily_power(data['datetime'], data['irradiance'], data['temp'])
    daily_meas_avg = compute_daily_average(output['datetime'], output['power'])

    dates_pred, pred = list(zip(*daily_pred_avgs))
    dates_meas, meas = list(zip(*daily_meas_avg))

    mae = 100 * sum(abs(a - b) / b for a, b in zip(pred, meas) if b > 10) / len(meas)
    print('Power MAE:', round(mae, 2), '%')

    plt.plot(dates_pred, pred, label='Predicted Power')
    plt.plot(dates_meas, meas, label='Actual Power')
    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()
