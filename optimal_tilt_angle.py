
# ---------- IMPORTS ----------
import DataParser
import PV_algorithm
import matplotlib.pyplot as plt


def optimal_angle_by_output():
    pv_pred = PV_algorithm.PVPredictor()
    data, output = DataParser.load_data()
    initial_tilt = 15
    dates = data['datetime']
    irradiances = data['irradiance']
    temperatures = data['temp']
    mean_per_angle = {}
    length = len(data['temp'])
    zipped = list(zip(dates,irradiances,temperatures))
    x = []
    y = []
    for angle in range(initial_tilt-15,initial_tilt+15+1):
        sum_pv_output = 0
        for date, irradiance, temp in zipped:
            pv_pred.tilt = angle
            sum_pv_output += pv_pred.output_power(date, irradiance, temp)
        mean_per_angle[angle] = sum_pv_output/length
        x.append(angle)
        y.append(mean_per_angle[angle])
    print(y.index(max(y)))

    plt.plot(x, y, label='tilt_output')
    plt.legend()
    plt.show()




def optimal_angle_by_irradiance():
    pv_pred = PV_algorithm.PVPredictor()
    data, output = DataParser.load_data()
    initial_tilt = 15
    dates = data['datetime']
    irradiances = data['irradiance']
    mean_per_angle = {}
    length = len(data['temp'])
    zipped = list(zip(dates,irradiances))
    x = []
    y = []
    for angle in range(initial_tilt-15,initial_tilt+15+1):
        sum_pv_irradiance = 0
        for date, irradiance in zipped:
            pv_pred.tilt = angle
            sum_pv_irradiance += pv_pred.total_irradiance(date, irradiance)
        mean_per_angle[angle] = sum_pv_irradiance/length
        x.append(angle)
        y.append(mean_per_angle[angle])
    print(y.index(max(y)))

    plt.plot(x, y, label='tilt_ird')
    plt.legend()
    plt.show()

optimal_angle_by_output()