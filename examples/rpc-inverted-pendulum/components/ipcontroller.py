import numpy as np
import os, sys
import json
import typing as types


def model_output(model, time_t, state_controller, input_pendulum):
    """
    Inverted Pendulum System -- LQR Gain Matrix
    Taken from
    http://ctms.engin.umich.edu/CTMS/index.php?example=InvertedPendulum&section=ControlDigital#4
    Run at a sampling period Ts = 1/100 s
    :return: K gain matrix
    """
    ss_inv_pend_lqr = np.array(model['xform'])[np.newaxis, :]
    return list(input_pendulum[-1] - (ss_inv_pend_lqr @ np.array(input_pendulum)[:-1, np.newaxis]).flatten())


if __name__ == "__main__":
    while True:
        rawIn = sys.stdin.readline()
        js = json.loads(rawIn)
        if not isinstance(js, types.Mapping):
            print('ERROR: expected a JSON object describing the RPC, but got ' + str(rawIn))
            sys.exit()
        elif not ('function' in js and 'model' in js and 'time' in js and 'state' in js and 'input' in js):
            print('ERROR: expected JSON RPC object to have keys [function, model, time, state, input], but got ' + str(rawIn))
            sys.exit()
        elif js['function'] == 'model_output':
            result = model_output(js['model'], js['time'], js['state'], js['input'])
            sys.stdout.write(json.dumps(result).replace('\n', ' ').replace('\r', ''))
            sys.stdout.write('\n')
            sys.stdout.flush()
        else:
            sys.stdout.write(json.dumps([]).replace('\n', ' ').replace('\r', ''))
            sys.stdout.write('\n')
            sys.stdout.flush()
            