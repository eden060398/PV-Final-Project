
# ---------- IMPORTS ----------
import DataParser
import PV_algorithm
import matplotlib.pyplot as plt


def optimal_angle():
    pv_pred = PV_algorithm.PVPredictor()
    data, output = DataParser.load_data()
    initial_tilt = 15
    dates = data['datetime']
    radiations = data['irradiance']
    temperatures = data['temp']
    mean_per_angle = {}
    length = len(data['temp'])
    zipped = list(zip(dates,radiations,temperatures))
    x = []
    y = []
    for angle in range(initial_tilt-15,initial_tilt+15+1):
        sum_pv_output = 0
        for date, radiation, temp in zipped:
            pv_pred.tilt = angle
            print(pv_pred.tilt)
            sum_pv_output += pv_pred.output_power(date, radiation, temp)
        mean_per_angle[angle] = sum_pv_output/length
        x.append(angle)
        y.append(mean_per_angle[angle])

    plt.plot(x, y, label='tilt')
    plt.legend()
    plt.show()




optimal_angle()