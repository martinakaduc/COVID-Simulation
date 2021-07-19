from .status import Status

class Agent(object):
    def __init__(self, id, init_ward, status, geometry):
        self.id = id
        self.status = status
        self.geometry = geometry
        self.ward = init_ward
        self.histories = []
        self.infectious_root = None

        self.append_history(init_ward, geometry)

    def get_id(self):
        return self.id

    def set_infectious_root(self, id):
        self.infectious_root = id

    def set_status(self, new_status):
        self.status = new_status

    def get_status(self):
        return self.status

    def get_current_ward(self):
        return self.ward

    def get_current_geometry(self):
        return self.geometry

    def get_current_geometry_XY(self):
        return [self.geometry.x, self.geometry.y]

    def clear_history(self):
        del self.histories
        self.append_history(self.ward, self.geometry)

    def move_agent(self, ward, point):
        self.append_history(ward, point)

    def append_history(self, ward, point):
        self.ward = ward
        self.geometry = point
        self.histories.append((ward, point))
