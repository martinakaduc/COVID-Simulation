import os
import _ctypes
import random
import numpy as np
from shapely.geometry import Point
from multiprocessing import Process, Manager
from threading import Thread

def get_ref(obj_id):
    return _ctypes.PyObj_FromPtr(obj_id)

class RandomWalk:
    def __init__(self, movement_params, map_region, transmission_model=None):
        self.cpu_count = os.cpu_count()
        self._move_mode = 0 # 0: all, 1: separate
        self.map_region = map_region
        self.moving_steps = 0
        self.transmission_model = transmission_model
        self.wanna_move = movement_params["wanna_move"]

        if "all" in movement_params:
            self.step_mean = movement_params["all"]["mean"]
            self.step_std = movement_params["all"]["std"]
        else:
            self._move_mode = 1
            self.step_mean = {k: k["mean"] for k in movement_params}
            self.step_std = {k: k["std"] for k in movement_params}

    def run_moving(self, susceptible, exposed, infectious, recovered, deceased,
                    steps, clear_freq=None, logging_agent=None):
        print("Susceptible: %d - Exposed: %d - Infectious: %d - Recovered: %d - Deceased: %d" % (
              len(susceptible), len(exposed), len(infectious), len(recovered), len(deceased)
        ))

        while True:
            self.moving_steps += 1
            print("STEP %d:" % self.moving_steps)
            print("All agents start moving...")

            # a = list(susceptible.keys())[0]
            # print(susceptible[a].get_current_geometry_XY())
            self._move_agents(susceptible)
            # print(susceptible[a].get_current_geometry_XY())
            self._move_agents(exposed)
            self._move_agents(recovered)

            self.transmission_model.run(susceptible, exposed, infectious, recovered, deceased)

            print("Susceptible: %d - Exposed: %d - Infectious: %d - Recovered: %d - Deceased: %d" % (
                  len(susceptible), len(exposed), len(infectious), len(recovered), len(deceased)
            ))

            if clear_freq != None and self.moving_steps % clear_freq == 0:
                self._clear_agent_history(susceptible)
                self._clear_agent_history(exposed)
                self._clear_agent_history(infectious)
                self._clear_agent_history(recovered)
                self._clear_agent_history(deceased)

            if self.moving_steps > steps:
                break

    def _clear_agent_history(self, agents):
            for i in range(len(agents)):
                agents[i].clear_history()

    def _move_agents(self, agents):
        number_of_agents = len(agents)
        batch_size = int(number_of_agents / self.cpu_count) + 1
        start_idx = 0
        list_threads = []

        agent_ids = list(agents.keys())

        for i in range(self.cpu_count):
            list_threads.append(Process(target=self._move_batch_agents,
                                        args=(id(agents),
                                        agent_ids[start_idx:start_idx+batch_size])))

            start_idx += batch_size

        for i in range(self.cpu_count):
            list_threads[i].start()

        for i in range(self.cpu_count):
            list_threads[i].join()

    def _move_batch_agents(self, agents_obj_id, agent_ids):
    #     split_point = int(len(agent_ids) / 2) + 1
    #
    #     list_threads = []
    #     list_threads.append(Thread(target=self._generate_batch_pos,
    #                                 args=(agents_obj_id,
    #                                 agent_ids[:split_point])))
    #
    #     list_threads.append(Thread(target=self._generate_batch_pos,
    #                                 args=(agents_obj_id,
    #                                 agent_ids[split_point:])))
    #
    #     for i in range(len(list_threads)):
    #         list_threads[i].start()
    #
    #     for i in range(len(list_threads)):
    #         list_threads[i].join()
    #
    # def _generate_batch_pos(self, agents_obj_id, agent_ids):
        agents = get_ref(agents_obj_id)
        wanna_mode_prob = np.random.choice([False, True], size=len(agent_ids),
                                replace=True, p=[1-self.wanna_move, self.wanna_move]).tolist()

        for idx, to_move in zip(agent_ids, wanna_mode_prob):
            if not to_move:
                continue
            agents[idx] = self._generate_new_pos(agents[idx])
            # get_ref(id(agents[idx])).move_agent(*self._generate_new_pos(agents[idx]))

    def _generate_new_pos(self, agent):
        x_coor, y_coor = agent.get_current_geometry_XY()
        maphuong = agent.get_current_ward()

        step_mean = 0
        step_std = 0

        if self._move_mode == 0:
            step_mean = self.step_mean
            step_std = self.step_std
        elif self._move_mode == 1:
            step_mean = self.step_mean[maphuong]
            step_std = self.step_std[maphuong]

        x_direction = random.gauss(step_mean, step_std) * random.randint(-1, 1)
        y_direction = random.gauss(step_mean, step_std)* random.randint(-1, 1)
        new_position = Point(x_coor + x_direction, y_coor + y_direction)
        new_maphuong = maphuong

        while True:
            valid, new_maphuong = self.map_region.validate_moving(maphuong, new_position)
            if valid:
                break
            else:
                x_direction = random.gauss(step_mean, step_std) * random.randint(-1, 1)
                y_direction = random.gauss(step_mean, step_std)* random.randint(-1, 1)
                new_position = Point(x_coor + x_direction, y_coor + y_direction)

        agent.move_agent(new_maphuong, new_position)
        return agent
        # return maphuong, new_position
