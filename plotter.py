import matplotlib.pyplot as plt


class Plotter:
    def __init__(self, points, hull, title="Convex Hull Visualization"):
        self.points = points
        self.hull = hull
        self.title = title

    def plot(self):
        # Unpack points into x and y coordinates for easy plotting
        x_points = [p.x for p in self.points]
        y_points = [p.y for p in self.points]

        # Create the hull's x and y coordinates, making sure to close the hull by connecting the last point to the first
        hull_points = self.hull + [self.hull[0]]
        x_hull = [p.x for p in hull_points]
        y_hull = [p.y for p in hull_points]

        # Create the plot
        plt.figure(figsize=(8, 8))
        plt.scatter(x_points, y_points, label="Points", color='blue')
        plt.plot(x_hull, y_hull, 'r-', label="Convex Hull", lw=2)  # Plot the hull

        # Annotate each point with its coordinates
        for i, point in enumerate(self.points):
            plt.annotate(f"({int(point.x)},{int(point.y)})", (point.x, point.y), textcoords="offset points", xytext=(0,5), ha='center')

        # Title and labels
        plt.title(self.title)
        plt.xlabel('X')
        plt.ylabel('Y')

        # Show a legend and grid
        plt.legend()
        plt.grid(True)

        # Display the plot
        plt.show()
