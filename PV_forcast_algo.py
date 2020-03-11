
import math
import datetime
from datetime import datetime


#get the day from a date


def day_number(date):
    return datetime(date).timetuple().tm_yday
#formula 1
# day variable is the day in the year in number from 1 to 365
def calc_extraterrestrial_irradiation(day):
    return 1376*(1+0.033*math.cos((2*math.pi*(day/365))))

#formula 2
#Declination angle is the angle between a plane perpendicular to incoming solar radiation and the rotational axis of the earth.
# the equation is calculated in radians

def clac_declination_angle(day):
    return 23.45*math.sin((360(day+240))/365)


#formula 3
#hour angle
#time variable is local civil time
def calc_hour_angle (time):
    return ((12-time)/24)*360

#formula 4
# LST- local solar time [hr]
# CT- Clock time [hr]
# Lstd- standard meridian for the local time zone [degrees west]- in Savona 150
# Lloc- Longitude of actual location [degrees west]- in Savona 8026'54''E
# E- Equation of time [hr]- the difference between local solar time ,LST and the local Civil time, LCT is called the time equation- see ahead
#  DT- Daylight saving correction (DT=0 if not on Daylight Saving Time, otherwise DT is equal to the number of hours that the time is advanced for Daylight savings time, usually 1hr)- in Savona there is daylight saving so depending on the day needs to be taken into account.

# day light saving in Savona 2018: ( taken from https://www.horlogeparlante.com/history-english.html?city=3167022)
# Transition to daylight saving time on Sunday 25 March 2018 - 03 h 00 (GMT + 2 h ) CEST
# Back to standard time on Sunday 28 October 2018 - 02 h 00 (GMT + 1 h ) CET
# we calculated the logitude degree according to https://www.fcc.gov/media/radio/dms-decimal and we got that the logitude degree is 8.431667

def calc_DT(date):
    start_date=datetime.date(2018,3,25)
    end_date=datetime.date(2018,10,28)
    if (date > start_date and date < end_date):
        return 0
    else:
        return 1



def calc_LST(clock_time,DT,day):
    L_std=15
    L_loc=8.431667

    return clock_time+ (1/15)*(L_std-L_loc)+calc_E(day)-calc_DT(DT)

# formula 5,6
# E- Equation of time [hr]- the difference between local solar time ,LST and the local Civil time, LCT is called the time equation- see ahead
def calc_E(day):
    B=(360(day-81))/364
    return 0.165*math.sin(B)-0.126*math.cos(B)-0.025*math.sin(B)


#formula 8
# clearness index calculation


def calc_Zenith_angle(declimation_angle,latitude_angle,hour_angle):
    return math.sin(declimation_angle)*math.sin(latitude_angle)+math.cos(declimation_angle)*math.cos(latitude_angle)*math.cos(hour_angle)

def calc_I_ot(day,declimation_angle,latitude_angle,hour_angle):
    return calc_extraterrestrial_irradiation(day)*calc_Zenith_angle(declimation_angle,latitude_angle,hour_angle)

def calc_clearness_index(Iot,Ighi):
    index=Ighi/Iot
    return index

def diffused_irradiance(clearness_index,Ighi):
    return (1-1.13*clearness_index)*Ighi

def direct_irradiance(Ighi,Idiffused):
    return Ighi-Idiffused

def total_angle(latitude_angle,zenith_angle,tilt_angle):
    return latitude_angle-zenith_angle-tilt_angle

#the direct irradiance at the tilted surface is calculated as follows

def direct_irradiance_at_surface(total_angle,zenith_angle,direct_irradiance):
    return direct_irradiance*(math.cos(total_angle)/math.cos(zenith_angle))

def diffused_irradiance_tilt(diffused_irradiance,tilt_angle):
    return 0.5*diffused_irradiance*(1+math.cos(tilt_angle))

#ρ is the ground albedo: usually 0.2 but can reach up to 0.8 in snow and ice
def diffused_irradiance_ground_reflection(Ighi,tilt_angle,p):
    return 0.5*p*Ighi*(1-math.cos(tilt_angle))

def total_irradiance(I_ground_reflection,I_tilt,I_direct):
    return I_ground_reflection+I_tilt+I_direct


