from threading import Thread
import numpy as np
import random

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
        self.NN_inference = NearestNeighbors(radius=self.infectious_radius, metric="euclidean", n_jobs=-1)

        self._susceptible = None
        self._exposed = None
        self._infectious = None
        self._recovered = None
        self._deceased = None
        self._first_time = True

    def run(self, susceptible, exposed, infectious, recovered, deceased):
        if self._first_time:
            self._first_time = False
            self._susceptible = list(susceptible.keys())
            self._exposed = list(exposed.keys())
            self._infectious = list(infectious.keys())
            self._recovered = list(recovered.keys())
            self._deceased = list(deceased.keys())

        self._bianry_transition(susceptible, exposed, self._susceptible,
                                self._exposed, self.beta, status.Status.EXPOSED)

        list_threads = []
        list_threads.append(Thread(target=self._unary_transition,
                                   args=(recovered, susceptible, self._recovered,
                                         self._susceptible, self.xi, status.Status.SUSCEPTIBLE)))

        list_threads.append(Thread(target=self._unary_transition,
                                   args=(infectious, deceased, self._infectious,
                                         self._deceased, self.mu, status.Status.DECEASED)))

        list_threads.append(Thread(target=self._unary_transition,
                                   args=(infectious, recovered, self._infectious,
                                         self._recovered, self.gamma, status.Status.RECOVERED)))

        list_threads.append(Thread(target=self._unary_transition,
                                   args=(exposed, infectious, self._exposed,
                                         self._infectious, self.eta, status.Status.INFECTIOUS)))

        list_threads.append(Thread(target=self._unary_transition,
                                   args=(susceptible, infectious, self._susceptible,
                                         self._infectious, self.theta, status.Status.INFECTIOUS)))

        for i in range(len(list_threads)):
            list_threads[i].start()

        for i in range(len(list_threads)):
            list_threads[i].join()

    def _bianry_transition(self, source, target, list_source_id, list_target_id, prob, new_status):
        list_sus_geo = np.array([source[id].get_current_geometry_XY() for id in list_source_id])
        list_exp_geo = np.array([target[id].get_current_geometry_XY() for id in list_target_id])

        if list_exp_geo.shape[0] == 0:
            return # No exposed

        self.NN_inference.fit(list_sus_geo)
        unluky_contacted_idxs = self.NN_inference.radius_neighbors(list_exp_geo, return_distance=False)

        for exp_id, unlucky_idxs in zip(list_target_id, unluky_contacted_idxs):
            list_trans_idx = np.random.choice([False, True], size=len(unlucky_idxs),
                                    replace=True, p=[1-prob, prob])
            list_trans_idx_god_selected = unlucky_idxs[list_trans_idx]
            list_trans_uuid = np.array(list_source_id)[list_trans_idx_god_selected].tolist()

            for i, trans_uuid in enumerate(list_trans_uuid):
                list_target_id.append(trans_uuid)

                target[trans_uuid] = source[trans_uuid]
                target[trans_uuid].set_status(new_status)
                target[trans_uuid].set_infectious_root(exp_id)
                del source[trans_uuid]

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
