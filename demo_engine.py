from vamsi_engine import (
    check_environmental_proximity,
    extract_event,
    get_nearby_wells,
    load_events,
)

print("events loaded:", len(load_events()))
print("extract:", extract_event(
    "DDR. OIL-JRJ-805. Encountered Stuck Pipe Incident in Barail Coal-Shale at 4367.2m. Freed after 6 hrs."
))
print("nearby 5 km:", len(get_nearby_wells(27.45, 95.32, 5)))
if get_nearby_wells(27.45, 95.32, 5):
    print("closest:", get_nearby_wells(27.45, 95.32, 5)[0]["well_id"])
print("env 2780 m:", check_environmental_proximity(27.35, 95.32, 2780))
print("env 1200 m:", check_environmental_proximity(27.3525, 95.3180, 1200))
