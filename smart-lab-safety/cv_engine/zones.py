def point_in_polygon(x: int, y: int, polygon: list[list[int]]) -> bool:
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        # Check if edge straddles the horizontal line at y
        above1 = (y1 > y)
        above2 = (y2 > y)
        if above1 != above2:
            # Compute intersection x coordinate
            xinters = (y - y1) * (x2 - x1) / (y2 - y1 + 1e-6) + x1
            if xinters > x:
                inside = not inside
    return inside

def centroid_of_box(box) -> tuple[int, int]:
    x1, y1, x2, y2 = box
    return int((x1 + x2) / 2), int((y1 + y2) / 2)

def check_zones_for_point(centroid, zones: list[dict]) -> list[dict]:
    cx, cy = centroid
    inside = []
    for z in zones:
        poly = z.get("polygon", [])
        if len(poly) >= 3 and point_in_polygon(cx, cy, poly):
            inside.append(z)
    return inside
