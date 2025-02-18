import googlemaps
from polyline import decode
from geopy.distance import geodesic
import requests
import math
import json
import numpy as np
import os
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class RouteConfig:
    """Configuration settings for route processing"""
    api_key: str
    interval_meters: float = 5
    image_size: str = "640x640"
    zoom_levels: List[int] = (19, 13)
    map_types: List[str] = ("satellite", "hybrid")

class RouteProcessor:
    def __init__(self, config: RouteConfig):
        self.config = config
        self.gmaps = googlemaps.Client(key=config.api_key)
        self._setup_directories()

    def _setup_directories(self) -> None:
        """Create necessary directories for storing images"""
        directories = ['raw'] + [f'maps{i+1}' for i in range(len(self.config.zoom_levels))]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def get_route(self, origin: str, destination: str) -> List[Tuple[float, float]]:
        """Fetch and decode route from Google Maps"""
        directions = self.gmaps.directions(origin=origin, destination=destination, mode="driving")
        if not directions:
            raise ValueError("No route found")
        route_polyline = directions[0]['overview_polyline']['points']
        return decode(route_polyline)

    @staticmethod
    def interpolate_points(point1: Tuple[float, float], point2: Tuple[float, float], 
                          distance_interval: float) -> List[Tuple[float, float]]:
        """Interpolate points between two coordinates at specified intervals"""
        lat1, lon1 = point1
        lat2, lon2 = point2
        total_distance = geodesic(point1, point2).meters

        if total_distance < distance_interval:
            return [point2]

        num_points = int(np.ceil(total_distance / distance_interval))
        latitudes = np.linspace(lat1, lat2, num_points)
        longitudes = np.linspace(lon1, lon2, num_points)
        return list(zip(latitudes, longitudes))

    def sample_route(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Sample route points with interpolation"""
        sampled_points = [points[0]]
        for i in range(1, len(points)):
            interpolated = self.interpolate_points(
                points[i - 1], points[i], self.config.interval_meters
            )
            sampled_points.extend(interpolated)
        return sampled_points

    def snap_to_roads(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Snap points to nearest roads using Google Roads API"""
        snapped_points = []
        for i in range(0, len(points), 100):
            chunk = points[i:i+100]
            path = "|".join(f"{lat},{lon}" for lat, lon in chunk)
            
            snap_url = f"https://roads.googleapis.com/v1/snapToRoads?path={path}&key={self.config.api_key}"
            response = requests.get(snap_url).json()
            
            if 'snappedPoints' not in response:
                print(f"Warning: No snapped points in response chunk {i//100 + 1}")
                continue
                
            snapped_points.extend(
                (point['location']['latitude'], point['location']['longitude'])
                for point in response['snappedPoints']
            )
        return snapped_points

    @staticmethod
    def calculate_heading(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate heading between two points"""
        lat1, lon1 = map(math.radians, point1)
        lat2, lon2 = map(math.radians, point2)
        
        d_lon = lon2 - lon1
        x = math.sin(d_lon) * math.cos(lat2)
        y = (math.cos(lat1) * math.sin(lat2) - 
             math.sin(lat1) * math.cos(lat2) * math.cos(d_lon))
        
        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360

    @staticmethod
    def heading_to_label(heading: float) -> str:
        """Convert heading angle to cardinal direction"""
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        index = int((heading + 22.5) % 360 / 45)
        return directions[index]

    def fetch_images(self, lat: float, lon: float, heading: float, 
                    index: int) -> None:
        """Fetch and save street view and map images"""
        # Street View
        sv_url = (f"https://maps.googleapis.com/maps/api/streetview?"
                 f"size={self.config.image_size}&location={lat},{lon}&"
                 f"heading={heading}&fov=70&key={self.config.api_key}")
        
        sv_response = requests.get(sv_url)
        if sv_response.status_code == 200:
            with open(f'raw/sv_{index:05d}.jpg', 'wb') as f:
                f.write(sv_response.content)

        # Maps at different zoom levels
        for i, (zoom, map_type) in enumerate(zip(self.config.zoom_levels, 
                                               self.config.map_types)):
            label = self.heading_to_label(heading)
            marker = f"color:red|label:{label}|{lat},{lon}"
            map_url = (f"https://maps.googleapis.com/maps/api/staticmap?"
                      f"center={lat},{lon}&maptype={map_type}&zoom={zoom}&"
                      f"size={self.config.image_size}&markers={marker}&"
                      f"key={self.config.api_key}")
            
            map_response = requests.get(map_url)
            if map_response.status_code == 200:
                with open(f'maps{i+1}/map_{index:05d}.png', 'wb') as f:
                    f.write(map_response.content)

    def process_route(self, origin: str, destination: str) -> None:
        """Process entire route and generate images"""
        # Get and process route
        route_points = self.get_route(origin, destination)
        interpolated_points = self.sample_route(route_points)
        snapped_points = self.snap_to_roads(interpolated_points)

        # Generate images for each point
        for i in range(1, len(snapped_points)):
            point1 = snapped_points[i - 1]
            point2 = snapped_points[i]
            heading = self.calculate_heading(point1, point2)
            
            self.fetch_images(*point1, heading, i)
            print(f"Processed point {i}/{len(snapped_points) - 1}")

def main():
    config = RouteConfig(
        api_key="YOUR_API_KEY_HERE",
        interval_meters=5,
        image_size="640x640"
    )
    
    processor = RouteProcessor(config)
    processor.process_route(
        origin="37.7792792,-122.4218166",
        destination="37.7452537,-119.5968016"
    )

if __name__ == "__main__":
    main()
