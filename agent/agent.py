from .status import Status

class Agent():
    def __init__(self, id, init_ward, status, geometry):
        self._id = id
        self._status = status
        self._geometry = geometry
        self._ward = init_ward
        self._histories = []
        self._infectious_root = None

        self._append_history(init_ward, geometry)

    def get_id(self):
        return self._id

    def set_infectious_root(self, id):
        self._infectious_root = id

    def set_status(self, new_status):
        self._status = new_status

    def get_status(self):
        return self._status

    def get_current_ward(self):
        return self._ward

    def get_current_geometry(self):
        return self._geometry

    def get_current_geometry_XY(self):
        return [self._geometry.x, self._geometry.y]

    def clear_history(self):
        del self._histories
        self._append_history(self._ward, self._geometry)

    def move(self, ward, point):
        self._append_history(ward, point)

    def _append_history(self, ward, point):
        self._ward = ward
        self._geometry = point
        self._histories.append((ward, point))
