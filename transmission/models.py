from threading import Thread
import numpy as np
import random
import os

from sklearn.neighbors import NearestNeighbors
from agent import status

class SEIRD:
    def __init__(self, seird_params):
        self.beta = seird_params["beta"]
        self.eta = seird_params["eta"]
        self.theta = seird_params["theta"]
        self.gamma = seird_params["gamma"]
        self.mu = seird_params["mu"]
        self.xi = seird_params["xi"]

        self.infectious_radius = seird_params["infectious_radius"]

        self._susceptible = None
        self._exposed = None
        self._infectious = None
        self._recovered = None
        self._deceased = None
        self._first_time = True
        self.cpu_count = os.cpu_count()

    def run(self, susceptible, exposed, infectious, recovered, deceased):
        if self._first_time:
            self._first_time = False
            self._susceptible = list(susceptible.keys())
            self._exposed = list(exposed.keys())
            self._infectious = list(infectious.keys())
            self._recovered = list(recovered.keys())
            self._deceased = list(deceased.keys())

        print("Pandemic infecting...")
        self._bianry_transition(susceptible, exposed, self._susceptible,
                                self._exposed, self.beta, status.Status.EXPOSED)

        self._unary_transition(recovered, susceptible, self._recovered,
                                         self._susceptible, self.xi, status.Status.SUSCEPTIBLE)

        self._unary_transition(infectious, deceased, self._infectious,
                                         self._deceased, self.mu, status.Status.DECEASED)

        self._unary_transition(infectious, recovered, self._infectious,
                                         self._recovered, self.gamma, status.Status.RECOVERED)

        self._unary_transition(exposed, infectious, self._exposed,
                                         self._infectious, self.eta, status.Status.INFECTIOUS)

        self._unary_transition(susceptible, infectious, self._susceptible,
                                         self._infectious, self.theta, status.Status.INFECTIOUS)

    def _bianry_transition(self, source, target, list_source_id, list_target_id, prob, new_status):
        list_sus_geo = np.array([source[id].get_current_geometry_XY() for id in list_source_id])
        list_exp_geo = np.array([target[id].get_current_geometry_XY() for id in list_target_id])

        if list_exp_geo.shape[0] == 0:
            return # No exposed

        NN_inference = NearestNeighbors(radius=self.infectious_radius, metric="euclidean", n_jobs=self.cpu_count)
        NN_inference.fit(list_sus_geo)

        unluky_contacted_idxs = NN_inference.radius_neighbors(list_exp_geo, return_distance=False)
        tobe_infectious = []

        for exp_id, unlucky_idxs in zip(list_target_id, unluky_contacted_idxs):
            list_trans_idx = np.random.choice([False, True], size=len(unlucky_idxs),
                                    replace=True, p=[1-prob, prob])
            list_trans_idx_god_selected = unlucky_idxs[list_trans_idx]
            list_trans_uuid = np.array(list_source_id)[list_trans_idx_god_selected].tolist()

            for i, trans_uuid in enumerate(list_trans_uuid):
                if trans_uuid in tobe_infectious:
                    continue

                list_target_id.append(trans_uuid)

                target[trans_uuid] = source[trans_uuid]
                target[trans_uuid].set_status(new_status)
                target[trans_uuid].set_infectious_root(exp_id)
                del source[trans_uuid]

                tobe_infectious.append(trans_uuid)

        for trans_uuid in tobe_infectious:
            list_source_id.remove(trans_uuid)

    def _unary_transition(self, source, target, list_source_id, list_target_id, prob, new_status):
        list_trans_idx = np.random.choice([False, True], size=len(list_source_id),
                                replace=True, p=[1-prob, prob])
        list_trans_uuid = np.array(list_source_id)[list_trans_idx]

        for i, trans_uuid in enumerate(list_trans_uuid):
            list_target_id.append(trans_uuid)

            target[trans_uuid] = source[trans_uuid]
            target[trans_uuid].set_status(new_status)
            del source[trans_uuid]

            list_source_id.remove(trans_uuid)
