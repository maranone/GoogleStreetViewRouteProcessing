import googlemaps
from polyline import decode
from geopy.distance import geodesic
import requests
import math
import json

#API_KEY = '555'  # Your API Key

# Initialize client
gmaps = googlemaps.Client(key=API_KEY)

# Fetch route directions
directions = gmaps.directions(
    origin="37.7792792,-122.4218166",
    destination="37.7452537,-119.5968016",
    mode="driving"
)

# Extract polyline
from geopy.distance import geodesic
import numpy as np

# Function to interpolate points between two lat/lon pairs based on distance
def interpolate_points(point1, point2, distance_interval):
    """
    Interpolates points between two given points (lat/lon) at a specified interval (in meters).
    """
    lat1, lon1 = point1
    lat2, lon2 = point2

    # Calculate total distance between the two points
    total_distance = geodesic(point1, point2).meters

    # If the distance is less than the interval, just return point2
    if total_distance < distance_interval:
        return [point2]

    # Calculate how many intermediate points we need
    num_points = int(np.ceil(total_distance / distance_interval))

    # Generate the latitudes and longitudes of the interpolated points
    latitudes = np.linspace(lat1, lat2, num_points)
    longitudes = np.linspace(lon1, lon2, num_points)

    return list(zip(latitudes, longitudes))

# Function to sample and interpolate along the route
def sample_route_with_interpolation(points, interval_meters=5):
    sampled_points = [points[0]]  # Start with the first point
    
    for i in range(1, len(points)):
        interpolated = interpolate_points(points[i - 1], points[i], interval_meters)
        sampled_points.extend(interpolated)
    
    return sampled_points


route_polyline = directions[0]['overview_polyline']['points']
# Decode the polyline (you are already doing this)
route_points = decode(route_polyline)

# Use the decoded polyline points and interpolate along the route
interpolated_route_points = sample_route_with_interpolation(route_points, interval_meters=5)


# Function to calculate the heading (bearing) between two lat/lon points
def calculate_heading(point1, point2):
    lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
    lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])
    
    d_lon = lon2 - lon1

    x = math.sin(d_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)

    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    bearing = (initial_bearing + 360) % 360  # Normalize to 0-360

    return bearing

# Function to sample points along the route at a set interval
def sample_route(points, interval_meters=5):
    sampled_points = [points[0]]  # Start with the first point
    accumulated_distance = 0
    
    for i in range(1, len(points)):
        dist = geodesic(points[i-1], points[i]).meters
        accumulated_distance += dist

        # Sample a point every 'interval_meters'
        if accumulated_distance >= interval_meters:
            sampled_points.append(points[i])
            accumulated_distance = 0  # Reset distance after sampling

    return sampled_points

# Use the decoded polyline points
sampled_route_points = sample_route(interpolated_route_points, interval_meters=5)

# Snap points to roads using Google Roads API
def snap_to_roads(points, api_key):
    snapped_points = []

    # Split the points into chunks of 100 or fewer
    for i in range(0, len(points), 100):
        chunk = points[i:i+100]  # Take a chunk of max 100 points

        # Prepare the path parameter for the current chunk
        path = "|".join([f"{lat},{lon}" for lat, lon in chunk])
        print(f"Snapping points: {path}")
        # Make a request to the Roads API for the current chunk
        snap_url = f"https://roads.googleapis.com/v1/snapToRoads?path={path}&key={api_key}"
        snap_response = requests.get(snap_url).json()

        if 'snappedPoints' in snap_response:
            # Extract snapped points from the current chunk
            for point in snap_response['snappedPoints']:
                location = point['location']
                snapped_points.append((location['latitude'], location['longitude']))
        else:
            print(f"Error: 'snappedPoints' not found in response: {snap_response}")

    return snapped_points


# Snapped points along the road
snapped_route_points = snap_to_roads(sampled_route_points, API_KEY)



def heading_to_label(heading):
    if 337.5 <= heading < 22.5:
        return "N"
    elif 22.5 <= heading < 67.5:
        return "NE"
    elif 67.5 <= heading < 112.5:
        return "E"
    elif 112.5 <= heading < 157.5:
        return "SE"
    elif 157.5 <= heading < 202.5:
        return "S"
    elif 202.5 <= heading < 247.5:
        return "SW"
    elif 247.5 <= heading < 292.5:
        return "W"
    elif 292.5 <= heading < 337.5:
        return "NW"
    return "N"  # Default label

def get_static_map(lat, lon, heading, zoom=10, size="640x640", color="red", map_type="hybrid", api_key=None):
    label = heading_to_label(heading)  # Set label based on heading
    marker = f"color:{color}|label:{label}|{lat},{lon}"
    map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}&maptype={map_type}&zoom={zoom}&size={size}&markers={marker}&key={api_key}"
    
    # Fetch the map with the directional label
    map_response = requests.get(map_url)
    
    if map_response.status_code == 200:
        return map_response.content  # Return raw image content for saving/display
    else:
        print(f"Error fetching map: {map_response.status_code}")
        return None







import os

# Check if 'raw' directory exists, if not, create it
if not os.path.exists('raw'):
    os.makedirs('raw')


size = '640x640'  # Max resolution



# Initialize index for file naming
index = 1

# Directory for map images
if not os.path.exists('maps1'):
    os.makedirs('maps1')
# Directory for map images
if not os.path.exists('maps2'):
    os.makedirs('maps2')

# Main loop to save street view, map, and description
for i in range(1, len(snapped_route_points)):
    point1 = snapped_route_points[i - 1]
    point2 = snapped_route_points[i]
    
    # Calculate heading
    heading = calculate_heading(point1, point2)
    
    lat, lon = point1
    streetview_url = f"https://maps.googleapis.com/maps/api/streetview?size={size}&location={lat},{lon}&heading={heading}&fov=70&key={API_KEY}"
    
    # Fetch street view image
    sv_response = requests.get(streetview_url)
    
    if sv_response.status_code == 200:
        # Save street view image
        filename = f'raw/sv_{index:05d}.jpg'
        with open(filename, 'wb') as file:
            file.write(sv_response.content)
    
        # Fetch map image
        map_image = get_static_map(lat, lon, heading, zoom=19, map_type="satellite", api_key=API_KEY)
        if map_image:
            map_filename = f'maps1/map_{index:05d}.png'
            with open(map_filename, 'wb') as map_file:
                map_file.write(map_image)
        map_image2 = get_static_map(lat, lon, heading, zoom=13, map_type="hybrid", api_key=API_KEY)
        if map_image2:
            map_filename2 = f'maps2/map_{index:05d}.png'
            with open(map_filename2, 'wb') as map_file2:
                map_file2.write(map_image2)
        print(f"Processed point {index}/{len(interpolated_route_points) - 1}")
        index += 1  # Increment index for next image

