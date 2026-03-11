import json

import numpy as np
import rasterio
import rasterio.features
from shapely.geometry import Point as ShapelyPoint
import networkx as nx
from rtree import index


class ElevationModel:
    def __init__(self, elevation_path):
        self.elevation_path = elevation_path

    def get_elevation(self, x, y):
        with rasterio.open(self.elevation_path) as src:
            for val in src.sample([(x, y)]):
                return float(val[0])
            return None

    def find_highest_point(self, user_point):
        with rasterio.open(self.elevation_path) as src:
            shapely_user = ShapelyPoint(user_point.x, user_point.y)
            buffer_5km = shapely_user.buffer(5000)
           # Get the window (rectangular bounding box of the circle)
            window = rasterio.features.geometry_window(src, [buffer_5km])
            
            # Read elevation data with nodata handling
            array = src.read(1, window=window)
            nodata = src.nodata
            
            # Get the transform for this window
            window_transform = rasterio.windows.transform(window, src.transform)
            
            # Create a circular mask to exclude points outside 5km radius
            from rasterio.features import geometry_mask
            circular_mask = geometry_mask(
                [buffer_5km],
                out_shape=array.shape,
                transform=window_transform,
                invert=True  # True inside the circle
            )
            
            # Create a combined mask: inside circle and valid data
            if nodata is not None:
                valid_data_mask = (array != nodata)
                combined_mask = circular_mask & valid_data_mask
            else:
                combined_mask = circular_mask
            
            # Check if there are any valid pixels inside the circle
            if not np.any(combined_mask):
                raise ValueError("No valid elevation data found within 5km radius")
            
            # Apply the mask: set invalid values to -inf so they won't be max
            masked_array = np.where(combined_mask, array.astype(float), -np.inf)
            
            # Find the highest point within the valid circular area
            max_idx = np.unravel_index(masked_array.argmax(), masked_array.shape)
            row, col = max_idx
            
            # Use masked_array for the elevation value (consistent with max finding)
            max_elevation = masked_array[max_idx]
            
            x, y = rasterio.transform.xy(window_transform, row, col)
            return ShapelyPoint(x, y), float(max_elevation)


class RoutePlanner:
    PROFILES = {
        "standard": {"label": "Standard Adult", "speed_kmh": 5.0, "min_per_10m": 1.0},
        "child":    {"label": "Child / Group", "speed_kmh": 3.5, "min_per_10m": 1.5},
        "elderly":  {"label": "Elderly / Impaired", "speed_kmh": 3.0, "min_per_10m": 2.0},
    }

    def __init__(self, itn_json_path, elevation_model, profile_key="standard"):
        self.elevation_model = elevation_model
        self.graph = self._load_graph(itn_json_path)
        self.set_profile(profile_key)
        self.node_elevations = {}
        self.cache_node_elevations()
        self.update_weights_naismith()
        self.idx = self._build_rtree()

    def set_profile(self, profile_key: str):
        if profile_key not in self.PROFILES:
            raise ValueError(f"Unknown profile_key: {profile_key}")

        p = self.PROFILES[profile_key]
        self.profile_key = profile_key
        self.profile_label = p["label"]
        self.speed_kmh = float(p["speed_kmh"])
        self.min_per_10m = float(p["min_per_10m"])

    def apply_flood_penalty(self, flood_level_m: float,
                            penalty_factor: float = 5.0):
        if flood_level_m is None:
            return

        self.update_weights_naismith()

        for u, v, data in self.graph.edges(data=True):
            elev_u = self.node_elevations[u]
            elev_v = self.node_elevations[v]

            underwater = (elev_u < flood_level_m) or (
                    elev_v < flood_level_m)
            if underwater:
                data["weight"] = float(data["weight"]) * float(
                    penalty_factor)

    def _load_graph(self, json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)

        G = nx.Graph()

        for node_id, node_info in data['roadnodes'].items():
            G.add_node(node_id, position=(float(node_info['coords'][0]), float(node_info['coords'][1])))

        for link_id, link_info in data['roadlinks'].items():
            u = link_info['start']
            v = link_info['end']
            length = float(link_info.get('length', 0))
            if u in G and v in G:
                G.add_edge(u, v, length=length)
        return G

    def _build_rtree(self):
        idx_property = index.Property()
        node_items = (
            (i, (d['position'][0], d['position'][1], d['position'][0],
                 d['position'][1]), n)
            for i, (n, d) in enumerate(self.graph.nodes(data=True))
        )
        return index.Index(node_items, properties=idx_property)

    def get_nearest_node(self, x, y):
        nearest_gen = self.idx.nearest((x, y, x, y), 1, objects=True)
        return next(nearest_gen).object

    def calculate_naismith_distance(self, u, v, edge_data):
        distance_m = edge_data["length"]

        speed_m_per_min = (self.speed_kmh * 1000.0) / 60.0
        time_walk = distance_m / speed_m_per_min

        elev_u = self.node_elevations[u]
        elev_v = self.node_elevations[v]
        ascent = max(0.0, elev_v - elev_u)

        time_climb = (ascent / 10.0) * self.min_per_10m

        return time_walk + time_climb

    ### Optimised: no pre-loop over edges
    def find_shortest_path(self, start_node, end_node):
        return nx.shortest_path(self.graph, start_node, end_node,
                                weight="weight",
                                method="dijkstra")

    def cache_node_elevations(self):

        ### Optimized: cache elevation for all graph nodes using a single raster sampling call (much faster than per-node sampling).
        self.node_elevations = {}

        # Collect node IDs and coordinates in a stable order
        node_ids = []
        coords = []

        for node_id, data in self.graph.nodes(data=True):
            node_ids.append(node_id)
            coords.append(data["position"])

        # Batch-sample elevations
        with rasterio.open(self.elevation_model.elevation_path) as src:
            for node_id, val in zip(node_ids, src.sample(coords)):
                self.node_elevations[node_id] = float(val[0])

    def update_weights_naismith(self):
        dg = self.graph.to_directed()

        for u, v, data in dg.edges(data=True):
            data["weight"] = self.calculate_naismith_distance(u, v, data)
        self.graph = dg

# difficulty score
    def calculate_route_stats(self, path_nodes):
        total_distance = 0
        total_elevation_gain = 0

        for u, v in zip(path_nodes[:-1], path_nodes[1:]):
            edge = self.graph.edges[u, v]
            total_distance += edge['length']

            elev_u = self.node_elevations[u]
            elev_v = self.node_elevations[v]

            if elev_v > elev_u:
                total_elevation_gain += elev_v - elev_u

        return total_distance / 1000, total_elevation_gain # km and meters

    def calculate_difficulty_score(self, distance_km, elevation_gain_m, weather):
        distance_time = distance_km / 5
        elevation_time = elevation_gain_m / 600
        nais_time = distance_time + elevation_time

        wind_factor = 1 + (weather["wind_speed"] / 10)
        rain_factor = 1 + (weather["precipitation"] / 10)
        temp_factor = 1
        if weather["temperature"] > 35:
            temp_factor += 0.2
        elif weather["temperature"] < 5:
            temp_factor += 0.3

        difficulty_score = nais_time * wind_factor * temp_factor * rain_factor

        if difficulty_score <= 3:
            return difficulty_score, "Easy: Suitable for most walkers"
        elif difficulty_score <= 6:
            return difficulty_score, "Moderate: Expect some challenge along the route"
        else:
            return difficulty_score, "Difficult: Prepare for tough conditions"
