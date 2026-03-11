import numpy as np
import matplotlib.pyplot as plt


class ElevationProfiler:
    """Create elevation profile graph for evacuation routes."""

    def __init__(self):
        """Initialize ElevationProfiler."""
        pass

    def calculate_distances(self, coordinates):
        """Calculate cumulative distances along a route.

        Args:
            coordinates: List of (x, y) coordinate tuples.

        Returns:
            list: Cumulative distances in meters from the start.
        """
        distances = [0]
        for i in range(1, len(coordinates)):
            x1, y1 = coordinates[i - 1]
            x2, y2 = coordinates[i]

            dist = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            distances.append(distances[-1] + dist)
        return distances

    def plot_profile(self, coordinates, elevations,
                     title="Elevation Profile of Evacuation Route",
                     save_path=None):
        """Create and display an elevation profile graph.

        Args:
            coordinates: List of (x, y) coordinate tuples.
            elevations: List of elevation values in meters.
            title: Graph title string.
            save_path: Optional path to save the figure.

        Returns:
            dict: Route statistics including distance, climb, and elevation data.
        """
        # Convert to numpy arrays
        elevations = np.array(elevations)
        # Calculate distances
        distances = self.calculate_distances(coordinates)
        # Convert to kilometers
        distances_km = [d / 1000 for d in distances]
        # Calculate statistics
        min_elev = np.min(elevations)
        max_elev = np.max(elevations)
        mean_elev = np.mean(elevations)  
        total_distance = distances_km[-1]
        # Calculate total climb
        total_climb = 0
        for i in range(1, len(elevations)):
            if elevations[i] > elevations[i - 1]:
                total_climb += elevations[i] - elevations[i - 1]
        # The highest point index
        highest_index = np.argmax(elevations)
        # Create graph
        plt.figure(figsize=(12, 6))
        ax = plt.gca()
        ax.set_facecolor('#FFFDE7') 
        # Plot elevation profile
        plt.plot(distances_km, elevations, 
                 color='blue', linewidth=2.5,
                 label='Elevation Profile')
        # Fill under the curve (Reference: geodose)
        plt.fill_between(distances_km, elevations, 0, color='#1E88E5', alpha=0.15)
        # Add reference lines (Reference: geodose)
        plt.axhline(y=min_elev, color='green', linestyle='--', 
                   linewidth=1, alpha=0.7, label=f'Min: {min_elev:.1f} m')
        plt.axhline(y=max_elev, color='red', linestyle='--', 
                   linewidth=1, alpha=0.7, label=f'Max: {max_elev:.1f} m')
        plt.axhline(y=mean_elev, color='orange', linestyle='--', 
                   linewidth=1, alpha=0.7, label=f'Avg: {mean_elev:.1f} m')
        # Start point
        plt.scatter(distances_km[0], elevations[0], 
                   c='green', s=150, marker='o', 
                   edgecolors='white', linewidths=2, zorder=5)
        plt.text(distances_km[0] + 0.1, elevations[0] + 5, 
                'Start', fontsize=11, fontweight='bold', color='green')
        # Highest point
        plt.scatter(distances_km[highest_index], elevations[highest_index], 
                   c='red', s=180, marker='^', 
                   edgecolors='white', linewidths=2, zorder=5)
        plt.annotate(f'Route High Point\n({elevations[highest_index]:.1f} m)',
                    xy=(distances_km[highest_index], elevations[highest_index]),
                     xytext=(distances_km[highest_index] + 0.3,
                             elevations[highest_index] + 10),
                    fontsize=10, fontweight='bold', color='red',
                    bbox=dict(boxstyle='round', facecolor='white', edgecolor='red'),
                    arrowprops=dict(arrowstyle='->', color='red'))
        # End point
        plt.scatter(distances_km[-1], elevations[-1], 
                   c='blue', s=150, marker='s', 
                   edgecolors='white', linewidths=2, zorder=5)
        plt.text(distances_km[-1] - 0.1, elevations[-1] + 5, 
                'End', fontsize=11, fontweight='bold', color='blue', ha='right')
        # Graph style
        plt.xlabel('Distance along route (km)', fontsize=12, fontweight='bold')
        plt.ylabel('Elevation (m)', fontsize=12, fontweight='bold')
        plt.title(title, fontsize=14, fontweight='bold', pad=15)
        # Axis limits
        plt.xlim(-0.1, total_distance * 1.05)
        y_range = max_elev - min_elev
        plt.ylim(max(0, min_elev - y_range * 0.15), max_elev + y_range * 0.25)

        plt.grid(True, linestyle='-', alpha=0.3)

        plt.legend(loc='upper left', framealpha=0.95)
        
        # Add stats text box
        stats_text = (
            f"Route Statistics:\n"
            f"─────────────────\n"
            f"Distance: {total_distance:.2f} km\n"
            f"Total Climb: {total_climb:.1f} m\n"
            f"Max Elevation: {max_elev:.1f} m\n"
            f"Min Elevation: {min_elev:.1f} m"
        )
        
        # Add text box at top right
        plt.text(0.98, 0.97, stats_text, 
                transform=ax.transAxes, fontsize=9,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', 
                         edgecolor='gray', alpha=0.9),
                family='monospace')
        
        plt.tight_layout()
        
        # Save image if path provided
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved to: {save_path}")
        
        plt.show()
        
        # Return statistics
        return {
            'total_distance_km': total_distance,
            'total_climb_m': total_climb,
            'max_elevation_m': max_elev,
            'min_elevation_m': min_elev,
            'avg_elevation_m': mean_elev
        }
