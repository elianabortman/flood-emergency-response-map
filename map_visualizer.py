import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show, plotting_extent
import numpy as np
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as fm
from matplotlib.patches import Rectangle
from matplotlib.patches import Circle


class MapVisualizer:
    def __init__(self, background_path, elevation_path):
        self.background_path = background_path
        self.elevation_path = elevation_path

    def plot_map(self, user_point, high_point, route_coords,
                 end_node_point=None):
        """
        ArcGIS Pro-like map with 20km x 20km extent centered on user location.
        """
        fig, ax = plt.subplots(figsize=(12, 10))
        ax.set_title("Emergency Flood Response: Route to High Ground", fontsize=14, pad=12)


        with rasterio.open(self.background_path) as bg:
            show(bg, ax=ax)

        # draw transparent elevation raster overlay
 
        with rasterio.open(self.elevation_path) as elev:
            elev_data = elev.read(1)
            nodata = elev.nodata
            if nodata is not None:
                elev_data = np.ma.masked_where(elev_data == nodata, elev_data)

            elev_img = ax.imshow(
                elev_data,
                extent=plotting_extent(elev),
                cmap="terrain",
                alpha=0.45,
                zorder=2
            )
            cbar = plt.colorbar(elev_img, ax=ax, fraction=0.035, pad=0.02)
            cbar.set_label("Elevation (m)")

        # plot layers (points + route)
        
        ax.scatter(user_point.x, user_point.y, c="red", marker="X", s=180,
                   edgecolor="white", linewidth=1.2, label="User Start", zorder=5)

        ax.scatter(high_point.x, high_point.y, c="blue", marker="^", s=180,
                   edgecolor="white", linewidth=1.2, label="Highest Point", zorder=5)
        # Add in the end node on plot
        if end_node_point is not None:
            ax.scatter(end_node_point.x, end_node_point.y, c="orange",
                       marker="o", s=160,
                       edgecolor="white", linewidth=1.2, label="End ITN Node",
                       zorder=6)

        if route_coords:
            route_x, route_y = zip(*route_coords)
            ax.plot(route_x, route_y, color="black", linewidth=2.8,
                    label="Quickest Path", zorder=4)

        # Set 20km x 20km view centered on user

        ax.set_xlim(user_point.x - 10000, user_point.x + 10000)
        ax.set_ylim(user_point.y - 10000, user_point.y + 10000)
        ax.set_aspect("equal", adjustable="box")

        self.add_neatline(ax)
        self.add_north_arrow(ax)
        self.add_scale_bar(ax, length_m=2000, label="2 km")

        ax.grid(True, linewidth=0.4, alpha=0.35)

        # Legend styled
        leg = ax.legend(loc="upper left", frameon=True, framealpha=0.95, edgecolor="black")
        for t in leg.get_texts():
            t.set_fontsize(10)

        ax.set_xlabel("Easting (m)")
        ax.set_ylabel("Northing (m)")

        plt.tight_layout()
        plt.show()

    def add_neatline(self, ax):
        """Adds a neatline/map frame like ArcGIS Pro."""
        rect = Rectangle((0, 0), 1, 1, transform=ax.transAxes,
                         fill=False, linewidth=1.4, edgecolor="black", zorder=10)
        ax.add_patch(rect)

    def add_north_arrow(self, ax):
        """North arrow positioned at upper-right (ArcGIS Pro style)."""
        x, y = 0.93, 0.92  # upper-right in axes fraction
        ax.annotate(
            "N",
            xy=(x, y),
            xytext=(x, y - 0.08),
            xycoords="axes fraction",
            textcoords="axes fraction",
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", lw=2.0, color="black")
        )

    def add_scale_bar(self, ax, length_m=2000, label="2 km"):
        """Adds a scale bar in map units (meters)."""
        fontprops = fm.FontProperties(size=10)
        scalebar = AnchoredSizeBar(
            ax.transData,
            length_m,
            label,
            loc="lower right",
            pad=0.6,
            color="black",
            frameon=True,
            size_vertical=40,
            fontproperties=fontprops
        )
        ax.add_artist(scalebar)
