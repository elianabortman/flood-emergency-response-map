class OrientationChecker:

    @staticmethod
    def orientation(p, q, r):  # Triplet Orientation
        """
        Determines the orientation of an ordered triplet of points (p, q, r).
        Points are x, y coordinates.

        0 -> Collinear
        >0 -> Clockwise turn
        <0 -> Counterclockwise turn
        """

        val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)

        return val
