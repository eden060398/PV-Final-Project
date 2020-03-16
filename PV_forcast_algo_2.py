import math
import datetime

# Savona Parameters
LATITUDE_ANGLE = 44.298611 * math.pi / 180
LONGITUDE_ANGLE = 8.448333 * math.pi / 180
STANDARD_MERIDIAN = 15 * math.pi / 180


# formula 1
# day variable is the day in the year in number from 1 to 365
def extraterrestrial_irradiation(time_data):
    return 1376 * (1 + 0.033 * math.cos((2 * math.pi * (time_data.day / 365))))


# formula 2
# Declination angle is the angle between a plane perpendicular to incoming solar radiation and the rotational axis of
# the earth.
# the equation is calculated in radians
def declination_angle(time_data):
    return 23.45 * math.sin((2 * math.pi * (time_data.day + 240)) / 365)


# formula 3
# hour angle
# time variable is local civil time
def hour_angle(time_data):
    solar_time = local_solar_time(time_data)
    return ((12 - solar_time) / 24) * 2 * math.pi


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
def daylight_saving_correction(time_data):
    start_date = datetime.datetime(2018, 3, 25, 3)
    end_date = datetime.datetime(2018, 10, 28, 2)
    if start_date <= time_data < end_date:
        return 0
    else:
        return 1


def local_solar_time(time_data):
    civil_time = time_data.hour + (time_data.minute + time_data.second / 60) / 60
    return civil_time + (1 / 15) * (STANDARD_MERIDIAN - LONGITUDE_ANGLE) + equation_of_time(time_data) - \
        daylight_saving_correction(time_data)


# formula 5,6
# E- Equation of time [hr]- the difference between local solar time ,LST and the local Civil time,
# LCT is called the time equation- see ahead
def equation_of_time(time_data):
    B = (2 * math.pi * (time_data.day - 81)) / 364
    return 0.165 * math.sin(B) - 0.126 * math.cos(B) - 0.025 * math.sin(B)


# formula 9
# cos(zenith_angle) calculation
def cos_zenith_angle(time_data):
    dec_angle = declination_angle(time_data)
    hr_angle = hour_angle(time_data)
    return math.sin(dec_angle) * math.sin(LATITUDE_ANGLE) + math.cos(dec_angle) * \
        math.cos(LATITUDE_ANGLE) * math.cos(hr_angle)


# formula 10 (and 8)
# clearness index calculation
def clearness_index(time_data, measured_irradiation):
    return measured_irradiation / (extraterrestrial_irradiation(time_data) * cos_zenith_angle(time_data))


