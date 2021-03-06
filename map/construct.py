from shapely.geometry import Point
from rtree.index import Index
import geopandas as gpd

class Region:
    def __init__(self, map_path=None):
        self.map_frame = None
        self._polygon_union = None
        self._mapping_ward_id = {}
        self._llist_adjacent_ward = {}
        self._tracking_in_out = {}

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

    def validate_moving(self, maphuong, point):
        for ward_id in self._llist_adjacent_ward[maphuong]:
            if self.is_point_in_ward(ward_id, point):
                if maphuong != ward_id:
                    self._tracking_in_out[maphuong]["out"] += 1
                    self._tracking_in_out[ward_id]["in"] += 1
                return True, ward_id
        return False, None

    def get_mobility(self):
        mobility_by_ward = []
        for maphuong, mobi in self._tracking_in_out.items():
            mobility_by_ward.append((maphuong,
                                     str(mobi["in"]),
                                     str(mobi["out"])))

        return mobility_by_ward

    def reset_mobility(self):
        for maphuong in self._tracking_in_out:
            self._tracking_in_out[maphuong]["in"] = 0
            self._tracking_in_out[maphuong]["out"] = 0

    def _construct_adjacent_ward(self):
        index = Index()
        for f in self.map_frame.itertuples():
            self._mapping_ward_id[f.maphuong] = f.Index
            self._tracking_in_out[f.maphuong] = {"in": 0, "out":0}
            index.insert(f.Index, f.geometry.bounds)

        for ward in self.map_frame.itertuples():
            geom = ward.geometry
            maphuong = ward.maphuong
            self._llist_adjacent_ward[maphuong] = [maphuong]
            intersecting_ids = index.intersection(geom.bounds)

            for intersecting_id in intersecting_ids:
                intersect_ward = self.map_frame.loc[intersecting_id]

                if maphuong != intersect_ward.maphuong and (not intersect_ward.geometry.disjoint(geom)):
                    self._llist_adjacent_ward[maphuong].append(intersect_ward.maphuong)

    def _get_mapping_ward_id(self, ward_id):
        return self._mapping_ward_id[ward_id]

    def __len__(self):
        return len(self.map_frame)

    def  __getitem__(self, idx):
        return self.map_frame[idx]
