import sys

from pyproj import Transformer

from point import Point
from route_planner import ElevationModel, RoutePlanner
from map_visualizer import MapVisualizer
from convex_hull import ConvexHullGenerator
from weather import WeatherService
from elevation_profiler import ElevationProfiler

class EmergencyResponseApp:
    def __init__(self):
        self.elev_path = "geospatial-programming-2025-26-lemur/data/elevation/SZ.asc"
        self.bg_path = "geospatial-programming-2025-26-lemur/data/background/raster-50k_2724246.tif"
        self.itn_path = "geospatial-programming-2025-26-lemur/data/itn/solent_itn.json"

    def run(self):
        try:
            easting = float(input("Enter Easting: "))
            northing = float(input("Enter Northing: "))
        except ValueError:
            print("Invalid input. Please enter numbers.")
            return

        if not (430000 <= easting <= 465000 and 80000 <= northing <= 95000):
            print("Location is outside emergency zone. Quitting application.")
            sys.exit()

        print("Location accepted.")
        user_point = Point(easting, northing)

        # highest point
        print("Finding highest elevation...")
        elevation_model = ElevationModel(self.elev_path)
        high_pt, max_elev = elevation_model.find_highest_point(user_point)
        print(f"Highest point found at: {high_pt.x}, {high_pt.y} ({max_elev}m)")

        chg = ConvexHullGenerator()
        pts = chg.read_csv("input.csv")
        hull_points = chg.compute_hull(pts)
        chg.write_csv(hull_points, "output.csv")

        # route planning
        # Let user choose a walking profile.
        print("Choose walking profile:")
        print("  1) Standard Adult (5.0 km/h, 1 min/10m)")
        print("  2) Child / Group (3.5 km/h, 1.5 min/10m)")
        print("  3) Elderly / Impaired (3.0 km/h, 2 min/10m)")

        choice = input("Enter 1/2/3: ").strip()
        profile_key = {"1": "standard", "2": "child", "3": "elderly"}.get(
            choice, "standard")

        route_planner = RoutePlanner(self.itn_path, elevation_model,
                                     profile_key=profile_key)
        print(f"Profile selected: {route_planner.profile_label}")

        # Let user choose a flood level.
        flood_in = input(
            "Enter flood level in meters (blank for none): ").strip()
        flood_level = float(flood_in) if flood_in else None

        if flood_level is not None:
            route_planner.apply_flood_penalty(flood_level, penalty_factor=5.0)
            print(f"Flood level set to {flood_level} m (penalty applied).")

        print("Calculating route...")

        # Find nearest ITN nodes
        start_node = route_planner.get_nearest_node(user_point.x, user_point.y)
        end_node = route_planner.get_nearest_node(high_pt.x, high_pt.y)


        # Get ITN node coordinates and elevations
        start_coords = route_planner.graph.nodes[start_node]['position']
        end_coords = route_planner.graph.nodes[end_node]['position']
        end_node_point = Point(end_coords[0], end_coords[1])
        start_elev = route_planner.node_elevations[start_node]
        end_elev = route_planner.node_elevations[end_node] 
         # Display ITN node information
        print(f"Nearest ITN node to user: ({start_coords[0]:.1f}, {start_coords[1]:.1f}), elevation: {start_elev:.1f}m")
        print(f"Nearest ITN node to highest point: ({end_coords[0]:.1f}, {end_coords[1]:.1f}), elevation: {end_elev:.1f}m")

        path_nodes = route_planner.find_shortest_path(start_node, end_node)
        route_coords = [route_planner.graph.nodes[n]['position'] for n in path_nodes]

        # difficulty score
        transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(high_pt.x, high_pt.y)
        weather_service = WeatherService(api_key="d16c5932e8b6bfd3c878ec08baed21c9")
        weather = weather_service.get_weather(lat, lon)
        distance_km, elevation_gain = route_planner.calculate_route_stats(path_nodes)
        score, message = route_planner.calculate_difficulty_score(distance_km, elevation_gain, weather)
        print(f"Route difficulty: {score:.2f}")
        print(message)

        print("Generating map...")
        map_vis = MapVisualizer(self.bg_path, self.elev_path)
        map_vis.plot_map(user_point, high_pt, route_coords,
                         end_node_point=end_node_point)

        # elevation profile
        print("Generating elevation profile...")
        # Get elevation for each node on the path
        path_elevations = [route_planner.node_elevations[n] for n in path_nodes]
        profiler = ElevationProfiler()
        profiler.plot_profile(
            coordinates=route_coords,
            elevations=path_elevations,
            title="Elevation Route Profile",
        )

        # End of application
        print("Process completed.")


if __name__ == "__main__":
    app = EmergencyResponseApp()
    app.run()
