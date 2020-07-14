import argparse
from PVAlgorithm import PVPredictor, compute_daily_average
import matplotlib.pyplot as plt
from DataParser import load_data
from WebAPI import DataRetriever

# Savona Parameters
LATITUDE_ANGLE = 44.298611
LONGITUDE_ANGLE = 8.448333
STANDARD_MERIDIAN = 15
TILT_ANGLE = 15
AZIMUTH_ANGLE = -30
P_MAX_STC = 80
COEFF_P_MAX = -0.0043
NOC_TEMP = 43


def savona_experiment():
    pv_pred = PVPredictor(tilt=TILT_ANGLE, azimuth=AZIMUTH_ANGLE, latitude=LATITUDE_ANGLE,
                          longitude=LONGITUDE_ANGLE, std_meridian=STANDARD_MERIDIAN, p_max_stc=P_MAX_STC,
                          coeff_p_max=COEFF_P_MAX, noc_temp=NOC_TEMP)

    print('Running the Savona comparative experiment')
    print('-----------------------------------------')
    print('Location:\n\t{lat}° N {lon}° E'.format(lat=LATITUDE_ANGLE, lon=LONGITUDE_ANGLE))
    print('Surface:\n\tTilt = {tilt}°\n\tAzimuth = {azimuth}°'.format(tilt=TILT_ANGLE, azimuth=AZIMUTH_ANGLE))
    print('PV Array:\n\tMax Power = {pmax} kW\n\tNOC Temperature = {noc} °C\n\tMax Power Coefficient = {pmax_coeff} %/°C'.format(
            pmax=P_MAX_STC,
            noc=NOC_TEMP,
            pmax_coeff=COEFF_P_MAX))

    print()

    print('Loading data...')
    data, output = load_data()

    print()

    print('Computing irradiance...')
    daily_pred_avgs = pv_pred.compute_daily_irradiance(data['datetime'], data['irradiance'], hour_range=(10, 16))
    daily_meas_avg = compute_daily_average(output['datetime'], output['radiation'], hour_range=(10, 16))

    dates_pred, pred = list(zip(*daily_pred_avgs))
    dates_meas, meas = list(zip(*daily_meas_avg))

    dae = sum(abs(p - m) for p, m in zip(pred, meas)) / len(meas)
    dae_per = 100 * sum(abs(p - m) for p, m in zip(pred, meas)) / sum(meas)
    yae = abs(sum(pred) - sum(meas)) / len(pred)
    yae_per = 100 * abs(1 - sum(pred) / sum(meas))
    print('Irradiance Daily Average Error:', round(dae, 2), 'W/m^2', '({per} %)'.format(per=round(dae_per, 2)))
    print('Irradiance Yearly Average Error:', round(yae, 2), 'W/m^2', '({per} %)'.format(per=round(yae_per, 2)))

    plt.plot(dates_pred, pred, label='Predicted Irradiance')
    plt.plot(dates_meas, meas, label='Actual Irradiance')
    plt.ylabel('W / m^2')
    plt.legend()
    plt.show()

    print()

    print('Computing power output...')
    daily_pred_avgs = pv_pred.compute_daily_power(data['datetime'], data['irradiance'], data['temp'], hour_range=(10, 16))
    daily_meas_avg = compute_daily_average(output['datetime'], output['power'], hour_range=(10, 16))

    dates_pred, pred = list(zip(*daily_pred_avgs))
    dates_meas, meas = list(zip(*daily_meas_avg))

    dae = sum(abs(p - m) for p, m in zip(pred, meas)) / len(meas)
    dae_per = 100 * sum(abs(p - m) for p, m in zip(pred, meas)) / sum(meas)
    yae = abs(sum(pred) - sum(meas)) / len(pred)
    yae_per = 100 * abs(1 - sum(pred) / sum(meas))
    print('Power Daily Average Error:', round(dae, 2), 'kW', '({per} %)'.format(per=round(dae_per, 2)))
    print('Power Yearly Average Error:', round(yae, 2), 'kW', '({per} %)'.format(per=round(yae_per, 2)))

    plt.plot(dates_pred, pred, label='Predicted Power')
    plt.plot(dates_meas, meas, label='Actual Power')
    plt.ylabel('kW')
    plt.legend()
    plt.show()


def main():
    parser = argparse.ArgumentParser(description='PV output predictor')
    parser.add_argument('-lat', '--latitude', type=float,
                        help='Latitude coordinate of location (default=32.1133)', default=32.1133)
    parser.add_argument('-lon', '--longitude', type=float,
                        help='Longitude coordinate of location (default=34.8044)', default=34.8044)
    parser.add_argument('-tilt', '--tilt-angle', type=float,
                        help='Tilt angle of plane (tilt and azimuth are optimized if either isn\'t given)', default=None)
    parser.add_argument('-azimuth', '--azimuth-angle', type=float,
                        help='Azimuth angle of plane (tilt and azimuth are optimized if either isn\'t given)', default=None)
    parser.add_argument('-Pmax', '--p-max-stc', type=float, help='Maximum power at STC [kW] (default = 1)', default=1)
    parser.add_argument('-noc', '--noc-temp', type=float,
                        help='NOC temperature [°C] (default = {default})'.format(default=NOC_TEMP), default=NOC_TEMP)
    parser.add_argument('-Pcoeff', '--p-max-coeff', type=float,
                        help='Temperature coefficient of maximum power [%%/°C] (default = {default})'.format(default=COEFF_P_MAX), default=COEFF_P_MAX)
    parser.add_argument('-exp', '--experiment', action='store_true',
                        help='Whether to run the comparative Savona experiment')

    args = parser.parse_args()

    if args.experiment:
        savona_experiment()
    else:
        dr = DataRetriever(args.latitude, args.longitude, tilt=args.tilt_angle, azimuth=args.azimuth_angle)
        data, tilt, azimuth, std_meridain = dr.get_data()

        pv_pred = PVPredictor(tilt=tilt, azimuth=azimuth, latitude=args.latitude, longitude=args.longitude,
                              std_meridian=std_meridain, p_max_stc=args.p_max_stc,
                              coeff_p_max=args.p_max_coeff, noc_temp=args.noc_temp)

        print('Location:\n\t{lat}° N {lon}° E'.format(lat=args.latitude, lon=args.longitude))
        print('Surface:\n\tTilt = {tilt}°\n\tAzimuth = {azimuth}°'.format(tilt=tilt, azimuth=azimuth))
        print('PV Array:\n\tMax Power = {pmax} kW\n\tNOC Temperature = {noc} °C\n\tMax Power Coefficient = {pmax_coeff} %/°C'.format(pmax=args.p_max_stc,
                                                                                                                                     noc=args.noc_temp,
                                                                                                                                     pmax_coeff=args.p_max_coeff))
        print()

        print('Computing irradiance...')
        daily_pred_avgs = pv_pred.compute_daily_irradiance(data['datetime'], data['irradiance'])
        dates_pred, pred = list(zip(*daily_pred_avgs))

        print('Irradiance Daily Average:', round(sum(pred) / len(pred), 2), 'W/m^2')

        plt.plot(dates_pred, pred, label='Predicted Irradiance')
        plt.ylabel('W / m^2')
        plt.legend()
        plt.show()

        print()

        print('Computing power output...')
        daily_pred_avgs = pv_pred.compute_daily_power(data['datetime'], data['irradiance'], data['temp'])
        dates_pred, pred = list(zip(*daily_pred_avgs))

        print('Power Daily Average:', round(sum(pred) / len(pred), 2), 'kW')

        plt.plot(dates_pred, pred, label='Predicted Power')
        plt.ylabel('kW')
        plt.legend()
        plt.show()


if __name__ == '__main__':
    main()
