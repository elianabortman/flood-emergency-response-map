from orientation import OrientationChecker
import pandas as pd
from point import Point


class ConvexHullGenerator:
    def __init__(self):
        self.checker = OrientationChecker()

    def read_csv(self, filepath):
        df = pd.read_csv(filepath)
        points = []
        for _, row in df.iterrows():
            p = Point(row["x"], row["y"])
            p.id = row["id"]
            points.append(p)
        return points

    def compute_hull(self, points):
        n = len(points)
        if n < 3:
            return points

        hull = []

        l = 0
        for i in range(1, n):
            if points[i].x < points[l].x:
                l = i
            elif points[i].x == points[l].x:
                if points[i].y < points[l].y:
                    l = i
        point_on_hull = points[l]

        while True:
            hull.append(point_on_hull)
            endpoint = points[0]
            for j in range(1, n):
                orientation = self.checker.orientation(point_on_hull, points[j], endpoint)
                if (endpoint == point_on_hull) or (orientation < 0):
                    endpoint = points[j]
            point_on_hull = endpoint
            if endpoint == hull[0]:
                break
        return hull

    def write_csv(self, hull_points, output_path):
        """Write CSV with columns id, x, y"""
        data = {
            'id': [p.id for p in hull_points],
            'x': [p.x for p in hull_points],
            'y': [p.y for p in hull_points]
        }
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        print(f"Convex Hull saved to {output_path}")
