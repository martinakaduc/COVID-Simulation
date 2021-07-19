import os
import random
from shapely.geometry import Point
from multiprocessing import Process, Manager

class RandomWalk:
    def __init__(self, movement_params, map_region, transmission_model=None):
        self.cpu_count = os.cpu_count()
        self._move_mode = 0 # 0: all, 1: separate
        self.map_region = map_region
        self.moving_steps = 0
        self.transmission_model = transmission_model

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
            print("Step %d:" % self.moving_steps)

            self._move_agents(susceptible)
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
        batch_size = int(number_of_agents / os.cpu_count()) + 1
        start_idx = 0
        list_threads = []

        agent_ids = list(agents.keys())

        for i in range(self.cpu_count):
            list_threads.append(Process(target=self._move_batch_agents,
                                        args=(agents,
                                        agent_ids[start_idx:start_idx+batch_size])))

            start_idx += batch_size

        for i in range(self.cpu_count):
            list_threads[i].start()

        for i in range(self.cpu_count):
            list_threads[i].join()

    def _move_batch_agents(self, agents, agent_ids):
        list_new_agents = {}
        list_new_agents_pos = {}

        for id in agent_ids:
            maphuong, posision = self._generate_new_pos(agents[id])
            list_new_agents_pos[id] = (maphuong, posision)

        for id, pos in list_new_agents_pos.items():
            maphuong, posision = pos
            agent_replication = agents[id]
            agent_replication.move(maphuong, posision)
            list_new_agents[id] = agent_replication

        agents.update(list_new_agents)

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

        list_consider_ward_ids = self.map_region.get_adjacent_wards(maphuong)

        x_direction = random.gauss(step_mean, step_std) * random.randint(-1, 1)
        y_direction = random.gauss(step_mean, step_std)* random.randint(-1, 1)
        new_position = Point(x_coor + x_direction, y_coor + y_direction)
        new_maphuong = maphuong

        while True:
            valid, new_maphuong = self.map_region.validate_moving(list_consider_ward_ids, new_position)
            if valid:
                break
            else:
                x_direction = random.gauss(step_mean, step_std) * random.randint(-1, 1)
                y_direction = random.gauss(step_mean, step_std)* random.randint(-1, 1)
                new_position = Point(x_coor + x_direction, y_coor + y_direction)

        return new_maphuong, new_position
