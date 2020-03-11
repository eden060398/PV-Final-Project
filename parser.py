# ---------- IMPORTS ----------
import csv
import datetime


# ---------- FUNCTIONS ----------
def parse_csv(filename):
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        titles = next(reader)
        line_count = 0
        datalists = [[] for _ in range(len(titles))]
        for line in reader:
            line_count += 1
            for i in range(len(line)):
                datalists[i].append(line[i])
        data = {title: datalist for title, datalist in zip(titles, datalists)}
        data['line_count'] = line_count

        return data


def load_data():
    data_2018 = parse_csv('data/2018.csv')
    parsed_data_2018 = {'datetime': [], 'temp': [], 'humidity': [], 'pressure': [],
                        'irradiance': [], 'rainfall': []}
    for i in range(data_2018['line_count']):
        datetime_str = data_2018['Date'][i] + ' ' + data_2018['Hour'][i]
        parsed_data_2018['datetime'].append(datetime.datetime.strptime(datetime_str,
                                                                       '%d/%m/%Y %H:%M'))
        parsed_data_2018['temp'].append(float(data_2018['Temp_C_'][i]))
        parsed_data_2018['humidity'].append(float(data_2018['Rel_Umidity___'][i]))
        parsed_data_2018['pressure'].append(float(data_2018['pressure_mbar_'][i]))
        parsed_data_2018['irradiance'].append(float(data_2018['GlobalRadiation_w_m_2_'][i]))
        parsed_data_2018['rainfall'].append(float(data_2018['Rainfall_mm_'][i]))

    data_2018_2 = parse_csv('data/DATA2_of_2018.csv')
    parsed_data_2018_2 = {'datetime': [], 'radiation': [], 'power': []}
    for i in range(data_2018['line_count']):
        datetime_str = data_2018_2['Date'][i] + ' ' + data_2018_2['Time'][i]
        parsed_data_2018_2['datetime'].append(datetime.datetime.strptime(datetime_str,
                                                                         '%d/%m/%Y %H:%M:%S'))
        parsed_data_2018_2['radiation'].append(float(data_2018_2['PV_rad'][i]))
        parsed_data_2018_2['power'].append(float(data_2018_2['PV_Pel'][i]))

    return parsed_data_2018, parsed_data_2018_2

load_data()