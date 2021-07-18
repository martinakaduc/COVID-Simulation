from map import construct
from movement import moving_manager
from transmission import models
from utils import config_utils, agent_utils, logging_utils

import argparse

def main(args):
    configs = config_utils.read_config(args.config)
    map_region = construct.Region(configs["map_path"])
    number_of_agents = agent_utils.read_init_situation(configs["init_situation"])

    print("GENERATING AGENTS...")
    (susceptible, exposed, infectious, recovered, deceased) = agent_utils.generate_agents(number_of_agents, map_region)
    print("TOTAL POPULATION: %d" % (len(susceptible) + len(exposed) + len(infectious) + len(recovered) + len(deceased)))

    transmission_model = models.SEIRD(configs["seird_params"])
    logging_agent = logging_utils.Logging(configs["logging_path"])
    random_walk_moving = moving_manager.RandomWalk(configs["movement_params"],
                                                   map_region,
                                                   transmission_model)

    print("START SIMULATION...")
    random_walk_moving.run_moving(susceptible, exposed, infectious, recovered, deceased,
                                    steps=configs["moving_steps"],
                                    clear_freq=configs["processing_steps"],
                                    logging_agent=logging_agent)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='Config file.', type=str, default="configs/default.json")
    args = parser.parse_args()

    main(args)
