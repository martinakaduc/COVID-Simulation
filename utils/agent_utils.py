import os
import functools
import random
import uuid

from multiprocessing import Process, Manager, Lock
from shapely.geometry import Point
from agent import agent, status

def read_init_situation(init_file):
    situation_initiate = {}

    with open(init_file, "r", encoding="utf-8") as f:
        data_read = f.read()
        first_line = True
        id_label_mapping = {}
        for line in data_read.split("\n"):
            if first_line:
                names = line.split(",")
                for idx, name in enumerate(names):
                    id_label_mapping[idx] = name
                    if idx > 1:
                        situation_initiate[name] = {}

                first_line = False
            else:
                elements = line.split(",")
                current_ward_id = ""
                for idx, element in enumerate(elements):
                    current_label = id_label_mapping[idx]

                    if current_label == "maphuong":
                        current_ward_id = element
                    elif idx > 1:
                        situation_initiate[current_label][current_ward_id] = int(element)

    return situation_initiate

def generate_agents(number_agents, wards):
    number_of_wards = len(wards)
    batch_size = int(number_of_wards / os.cpu_count()) + 1
    start_idx = 0
    list_threads = []

    manager = Manager()

    susceptible = manager.dict()
    exposed = manager.dict()
    infectious = manager.dict()
    recovered = manager.dict()
    deceased = manager.dict()

    for i in range(os.cpu_count()):
        list_threads.append(Process(target=generate_agents_batch_wards,
                                    args=(wards[start_idx:start_idx+batch_size],
                                            number_agents, susceptible, exposed,
                                            infectious, recovered, deceased)))

        start_idx += batch_size

    for i in range(os.cpu_count()):
        list_threads[i].start()

    for i in range(os.cpu_count()):
        list_threads[i].join()

    return susceptible, exposed, infectious, recovered, deceased

def generate_agents_batch_wards(batch_wards, init_situation,
                                susceptible, exposed, infectious, recovered, deceased):
    for ward in batch_wards.itertuples():
        ward_geometry = ward.geometry
        ward_bbox = ward_geometry.bounds
        ward_id = ward.maphuong
        # district_id = ward.attribute("maquan")

        susceptible_people = init_situation["susceptible"][ward_id]
        susceptible.update(generate_agent(ward_id,
                                            ward_geometry,
                                            ward_bbox,
                                            susceptible_people//100,
                                            status.Status.SUSCEPTIBLE))

        exposed_people = init_situation["exposed"][ward_id]
        exposed.update(generate_agent(ward_id,
                                            ward_geometry,
                                           ward_bbox,
                                           exposed_people,
                                           status.Status.EXPOSED))

        infectious_people = init_situation["infectious"][ward_id]
        infectious.update(generate_agent(ward_id,
                                            ward_geometry,
                                           ward_bbox,
                                           infectious_people,
                                           status.Status.INFECTIOUS))

        recovered_people = init_situation["recovered"][ward_id]
        recovered.update(generate_agent(ward_id,
                                            ward_geometry,
                                            ward_bbox,
                                            recovered_people,
                                            status.Status.RECOVERED))

        deceased_people = init_situation["deceased"][ward_id]
        deceased.update(generate_agent(ward_id,
                                            ward_geometry,
                                           ward_bbox,
                                           deceased_people,
                                           status.Status.DECEASED))

def generate_agent(ward_id, ward_geometry, bbox, people, status):
    output = {}
    x_min, y_min, x_max, y_max = bbox

    for _ in range(people):
        agent_x = random.uniform(x_min, x_max)
        agent_y = random.uniform(y_min, y_max)

        while not ward_geometry.contains(Point(agent_x, agent_y)):
            agent_x = random.uniform(x_min, x_max)
            agent_y = random.uniform(y_min, y_max)

        aid = uuid.uuid4()
        while aid in output:
            aid = uuid.uuid4()

        output[aid] = agent.Agent(aid,
                            ward_id,
                            status,
                            Point(agent_x, agent_y))

    return output
