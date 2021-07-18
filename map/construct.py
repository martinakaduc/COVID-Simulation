from shapely.geometry import Point
from rtree.index import Index
import geopandas as gpd

class Region:
    def __init__(self, map_path=None):
        self.map_frame = None
        self._polygon_union = None
        self._mapping_ward_id = {}
        self._llist_adjacent_ward = {}

        if map_path != None:
            self.map_frame = gpd.read_file(map_path)
            # sefl.map_frame.to_crs("EPSG:4326")
            self._polygon_union = self.map_frame.unary_union
            self._construct_adjacent_ward()

    def is_point_in_map(self, point):
        return self._polygon_union.within(point)

    def is_point_in_ward(self, ward_id, point):
        return self.map_frame.loc[self._get_mapping_ward_id(ward_id)].geometry.contains(point)

    def get_adjacent_wards(self, maphuong):
        return self._llist_adjacent_ward[maphuong]

    def validate_moving(self, list_ward_ids, point):
        for ward_id in list_ward_ids:
            if self.is_point_in_ward(ward_id, point):
                return True, ward_id
        return False, None

    def _construct_adjacent_ward(self):
        index = Index()
        for f in self.map_frame.itertuples():
            self._mapping_ward_id[f.maphuong] = f.Index
            index.insert(f.Index, f.geometry.bounds)

        for ward in self.map_frame.itertuples():
            geom = ward.geometry
            maphuong = ward.maphuong
            self._llist_adjacent_ward[maphuong] = []
            intersecting_ids = index.intersection(geom.bounds)

            for intersecting_id in intersecting_ids:
                intersect_ward = self.map_frame.loc[intersecting_id]
                # ward != intersect_ward and
                if (not intersect_ward.geometry.disjoint(geom)):
                    self._llist_adjacent_ward[maphuong].append(intersect_ward.maphuong)

    def _get_mapping_ward_id(self, ward_id):
        return self._mapping_ward_id[ward_id]

    def __len__(self):
        return len(self.map_frame)

    def  __getitem__(self, idx):
        return self.map_frame[idx]
