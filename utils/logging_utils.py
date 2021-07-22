import os
import time
import _ctypes
from datetime import datetime
from threading import Thread
from multiprocessing import Process

def get_ref(obj_id):
    return _ctypes.PyObj_FromPtr(obj_id)

class Logging:
    def __init__(self, logging_path):
        self.logging_path = logging_path
        self.log_count = 0
        self.sub_path = os.path.join(logging_path, datetime.now().strftime("%Y%m%d-%H%M%S"))

        if not os.path.exists(self.logging_path):
            os.makedirs(self.logging_path)

        os.mkdir(self.sub_path)
        os.mkdir(os.path.join(self.sub_path, "susceptible"))
        os.mkdir(os.path.join(self.sub_path, "exposed"))
        os.mkdir(os.path.join(self.sub_path, "infectious"))
        os.mkdir(os.path.join(self.sub_path, "recovered"))
        os.mkdir(os.path.join(self.sub_path, "deceased"))

    def run(self, susceptible, exposed, infectious, recovered, deceased, save_ward=False):
        print("Writing to file...")
        list_threads = []
        list_threads.append(Process(target=self._write_log,
                                        args=("susceptible", id(susceptible), save_ward)))

        list_threads.append(Process(target=self._write_log,
                                        args=("exposed", id(exposed), save_ward)))

        list_threads.append(Process(target=self._write_log,
                                        args=("infectious", id(infectious), save_ward)))

        list_threads.append(Process(target=self._write_log,
                                        args=("recovered", id(recovered), save_ward)))

        list_threads.append(Process(target=self._write_log,
                                        args=("deceased", id(deceased), save_ward)))


        for i in range(len(list_threads)):
            list_threads[i].start()

        for i in range(len(list_threads)):
            list_threads[i].join()

        self.log_count += 1

    def _write_log(self, name, agents_obj_id, save_ward=False):
        agents = get_ref(agents_obj_id)
        with open(os.path.join(self.sub_path, name, "batch_" + str(self.log_count) + ".txt"), "w", encoding="utf-8") as f:
            if not save_ward:
                for aid, agent in agents.items():
                    f.write(aid + ",\"" + str(agent.get_current_geometry_XY()) + "\"\n")
            else:
                for aid, agent in agents.items():
                    f.write(aid + "," + agent.get_current_ward() + ",\"" + str(agent.get_current_geometry_XY()) + "\"\n")

    def log_mobility(self, map_region):
        mobility = map_region.get_mobility()
        with open(os.path.join(self.sub_path, "mobility_" + str(self.log_count-1) + ".txt"), "w", encoding="utf-8") as f:
            for mobi in mobility:
                f.write(",".join(mobi) + "\n")
