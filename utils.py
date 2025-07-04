from collections import deque
from dataclasses import dataclass
from typing import Generator, NamedTuple, TypedDict, Callable
import matplotlib
matplotlib.use('TkAgg')
from matplotlib import patches
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.patches import Circle as PltCircle
from shapely import Polygon
import shapely
import math

OKABE_COLORS = ['#000000', '#E69F00', '#56B4E9', '#009E73', '#F0E442', '#0072B2', '#D55E00', '#CC79A7']
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=OKABE_COLORS) # type: ignore

class Circle(NamedTuple):
    x: float
    y: float
    r: float

class Square(NamedTuple):
    x: float
    y: float
    side_length: float

class HorizontalLine(NamedTuple):
    start: float
    end: float

class CirclesPlotKwargs(TypedDict, total=False):
    title: str | None
    p: float
    c: float
    cpu_time: float

UNIT_CIRCLE = Circle(0.0, 0.0, 1.0)

@dataclass
class Precision:
    precision: int = 7
    epsilon: float = 1e-3
    unit_circle_polygon: Polygon = shapely.Point(0.0, 0.0).buffer(1.0)

    def __post_init__(self):
        self.unit_circle_polygon = self.get_circle_polygon(UNIT_CIRCLE)

    def set_precision(self, precision: int) -> None:
        if precision == self.precision:
            return

        self.precision = precision
        self.epsilon = 1 / 10 ** (precision // 2)
        self.unit_circle_polygon = self.get_circle_polygon(UNIT_CIRCLE)

    def get_circle_polygon(self, circle: Circle) -> Polygon:
        quad_segs = min(math.ceil(circle.r * math.pi / 2 / self.epsilon), 2 ** 20)

        return shapely.Point(circle.x, circle.y).buffer(circle.r, quad_segs=quad_segs)

PRECISION = Precision()

def get_circles_plot(circles: list[Circle], *,
                    title: str | None = None,
                    p: float | None = None,
                    c: float | None = None,
                    ct: float | None = None,
                    cpu_time: float | None = None,
                    ax: Axes | None = None,
                    squares: list[Square] = [],
                    polygons: list[Polygon] = []):
    """Plot circles on either a new figure or an existing axes."""
    if ax is None:
        _, ax = plt.subplots(1, 1) # type: ignore
    else:
        _ = ax.figure
    
    # Draw unit circle with dashed lines in black
    ax.add_patch(PltCircle((0, 0), 1, fill=False, linestyle='--', color='black'))

    # Draw the circles
    for i, circle in enumerate(circles):
        color = OKABE_COLORS[(i + 1) % len(OKABE_COLORS)]
        ax.add_patch(PltCircle((circle.x, circle.y), circle.r, fill=False, color=color))
        ax.text(circle.x, circle.y, str(i + 1), # type: ignore
                horizontalalignment='center', verticalalignment='center',
                color=color, fontsize=18)
        
    for square in squares:
        ax.add_patch(patches.Rectangle((square.x, square.y), square.side_length, square.side_length, fill=False, color='black'))

    for polygon in polygons:
        x, y = polygon.exterior.xy
        ax.plot(x, y, color='black', linewidth=0.5) # type: ignore

    # Set plot limits and aspect ratio
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect('equal')
    
    # Add title and information
    if title:
        ax.set_title(title) # type: ignore
    
    stat_text: list[str] = []
    if p is not None:
        stat_text.append(f"p = {float(p):.3f}")
    if c is not None:
        stat_text.append(f"T(n) = {float(c):.3f} log n")
    if ct is not None:
        # D(n) = ct * n
        stat_text.append(f"D(n) = {float(ct):.3f} n")
    if cpu_time is not None:
        stat_text.append(f"done in {cpu_time:.2f}s")

    if stat_text:
        ax.set_xlabel(", ".join(stat_text), fontsize=10) # type: ignore
    
    return ax

def draw_circles(circles: list[Circle], *,
                title: str | None = None,
                p: float | None = None,
                c: float | None = None,
                ct: float | None = None,
                cpu_time: float | None = None,
                squares: list[Square] = [],
                polygons: list[Polygon] = []) -> None:
    """Draw a single set of circles."""
    get_circles_plot(circles, title=title, p=p, c=c, ct=ct, cpu_time=cpu_time, squares=squares, polygons=polygons)
    plt.show() # type: ignore

def get_horizontal_line(circle: Circle, y: float) -> HorizontalLine | None:
    """Get the horizontal line that intersects the circle at y."""
    if abs(y - circle.y) > circle.r:
        return None

    delta = (circle.r ** 2 - (y - circle.y) ** 2) ** 0.5
    return HorizontalLine(circle.x - delta, circle.x + delta)

def get_line_union(lines: list[HorizontalLine]) -> list[HorizontalLine]:
    """Merge horizontal lines into a minimal set of non-overlapping lines."""
    if not lines:
        return []

    # Sort by start coordinate
    sorted_lines = sorted(lines, key=lambda line: line.start)
    merged_lines: list[HorizontalLine] = []
    current = sorted_lines[0]

    for line in sorted_lines[1:]:
        if line.start <= current.end:
            # Lines overlap, update end point
            current = HorizontalLine(current.start, max(current.end, line.end))
        else:
            # No overlap, add current line and start new one
            merged_lines.append(current)
            current = line

    merged_lines.append(current)
    return merged_lines

def do_circles_cover_unit_circle(circles: list[Circle], y: float) -> bool:
    lines = [line for circle in circles for line in [get_horizontal_line(circle, y)] if line is not None]
    union = get_line_union(lines)

    unit_circle_line = get_horizontal_line(UNIT_CIRCLE, y)

    if unit_circle_line is None:
        return True
    
    return any(union_line.start <= unit_circle_line.start and union_line.end >= unit_circle_line.end for union_line in union)

def covers_unit_circle_2(circles: list[Circle]) -> bool:
    y = -1.0
    while y < 1:
        if not do_circles_cover_unit_circle(circles, y):
            return False
        y += PRECISION.epsilon

    return True

def is_point_covered(circle: Circle, x: float, y: float) -> bool:
    return (x - circle.x) ** 2 + (y - circle.y) ** 2 <= circle.r ** 2

def is_point_covered_by_any(circles: list[Circle], x: float, y: float) -> bool:
    return any(is_point_covered(circle, x, y) for circle in circles)

def is_fully_covered(square: Square, circle: Circle) -> bool:
    return is_point_covered(circle, square.x, square.y) and \
            is_point_covered(circle, square.x + square.side_length, square.y) and \
            is_point_covered(circle, square.x, square.y + square.side_length) and \
            is_point_covered(circle, square.x + square.side_length, square.y + square.side_length)

def is_square_covered(circles: list[Circle], square: Square) -> bool:
    x, y = square.x, square.y
    side_length = square.side_length
    corners = [(x, y), (x + side_length, y), (x, y + side_length), (x + side_length, y + side_length)]
    
    num_outside_unit_circle = sum(1 for corner in corners if not is_point_covered(UNIT_CIRCLE, *corner))
    
    if num_outside_unit_circle == 4:
        return True
        
    # Check if any point inside unit circle is not covered
    for corner in corners:
        if is_point_covered(UNIT_CIRCLE, *corner) and not is_point_covered_by_any(circles, *corner):
            return False
            
    # Check if square is entirely covered by any circle
    if any(is_fully_covered(square, circle) for circle in circles):
        return True

    # Recurse into four sub-quadrants
    new_side_length = square.side_length / 2

    if new_side_length < PRECISION.epsilon:
        return True

    subsquares = [
        Square(x, y, new_side_length),
        Square(x + new_side_length, y, new_side_length),
        Square(x, y + new_side_length, new_side_length),
        Square(x + new_side_length, y + new_side_length, new_side_length)
    ]
    return all(is_square_covered(circles, subsquare) for subsquare in subsquares)

def get_all_uncovered_squares(circles: list[Circle]) -> Generator[Square, None, None]:
    def get_uncovered_squares(square: Square) -> Generator[Square, None, None]:
        x, y = square.x, square.y
        side_length = square.side_length
        corners = [(x, y), (x + side_length, y), (x, y + side_length), (x + side_length, y + side_length)]

        num_outside_unit_circle = sum(1 for corner in corners if not is_point_covered(UNIT_CIRCLE, *corner))

        if num_outside_unit_circle == 4:
            return
        
        num_uncovered_corners = sum(1 for corner in corners if is_point_covered(UNIT_CIRCLE, *corner) and not is_point_covered_by_any(circles, *corner))

        if num_uncovered_corners > 3:
            yield square
            return

        if num_uncovered_corners == 0 and any(is_fully_covered(square, circle) for circle in circles):
            return

        new_side_length = square.side_length / 2

        if new_side_length < PRECISION.epsilon:
            return

        subsquares = [
            Square(x, y, new_side_length),
            Square(x + new_side_length, y, new_side_length),
            Square(x, y + new_side_length, new_side_length),
            Square(x + new_side_length, y + new_side_length, new_side_length)
        ]
        for subsquare in subsquares:
            yield from get_uncovered_squares(subsquare)

    yield from get_uncovered_squares(Square(-1.0, -1.0, 1.0))
    yield from get_uncovered_squares(Square(-1.0, 0.0, 1.0))
    yield from get_uncovered_squares(Square(0.0, -1.0, 1.0))
    yield from get_uncovered_squares(Square(0.0, 0.0, 1.0))

def get_biggest_uncovered_square(circles: list[Circle]):
    # use BFS instead of DFS, first square found is guaranteed to be the biggest

    q = deque([Square(-1.0, -1.0, 1.0), Square(-1.0, 0.0, 1.0),
               Square(0.0, -1.0, 1.0), Square(0.0, 0.0, 1.0)])
    
    while q:
        square = q.popleft()

        x, y = square.x, square.y
        side_length = square.side_length
        corners = [(x, y), (x + side_length, y), (x, y + side_length), (x + side_length, y + side_length)]

        num_outside_unit_circle = sum(1 for corner in corners if not is_point_covered(UNIT_CIRCLE, *corner))

        if num_outside_unit_circle == 4:
            continue

        num_uncovered_corners = sum(1 for corner in corners if is_point_covered(UNIT_CIRCLE, *corner) and not is_point_covered_by_any(circles, *corner))

        if num_uncovered_corners > 3:
            return square
        
        if num_uncovered_corners == 0 and any(is_fully_covered(square, circle) for circle in circles):
            continue

        new_side_length = square.side_length / 2

        if new_side_length < PRECISION.epsilon:
            continue

        subsquares = [
            Square(x, y, new_side_length),
            Square(x + new_side_length, y, new_side_length),
            Square(x, y + new_side_length, new_side_length),
            Square(x + new_side_length, y + new_side_length, new_side_length)
        ]

        q.extend(subsquares)

    return None

def get_biggest_semicovered_square(circles: list[Circle]):
    # use BFS instead of DFS, first square found is guaranteed to be the biggest

    q = deque([Square(-1.0, -1.0, 1.0), Square(-1.0, 0.0, 1.0),
               Square(0.0, -1.0, 1.0), Square(0.0, 0.0, 1.0)])
    
    while q:
        square = q.popleft()

        x, y = square.x, square.y
        side_length = square.side_length
        corners = [(x, y), (x + side_length, y), (x, y + side_length), (x + side_length, y + side_length)]

        num_outside_unit_circle = sum(1 for corner in corners if not is_point_covered(UNIT_CIRCLE, *corner))

        if num_outside_unit_circle == 4:
            continue

        num_uncovered_corners = sum(1 for corner in corners if is_point_covered(UNIT_CIRCLE, *corner) and not is_point_covered_by_any(circles, *corner))

        if num_uncovered_corners > 0:
            return square
        
        if num_uncovered_corners == 0 and any(is_fully_covered(square, circle) for circle in circles):
            continue

        new_side_length = square.side_length / 2

        if new_side_length < PRECISION.epsilon:
            continue

        subsquares = [
            Square(x, y, new_side_length),
            Square(x + new_side_length, y, new_side_length),
            Square(x, y + new_side_length, new_side_length),
            Square(x + new_side_length, y + new_side_length, new_side_length)
        ]

        q.extend(subsquares)

    return None

def covers_unit_circle(circles: list[Circle]) -> bool:
    # (x, y) are the bottom left coordinates of the square
    return all(is_square_covered(circles, Square(x, y, 1.0)) 
              for x, y in [(-1.0, -1.0), (-1.0, 0.0), (0.0, -1.0), (0.0, 0.0)])

def binary_search(
    start: float,
    end: float,
    evaluator: Callable[[float], tuple[bool, list[Circle]]],
    debug: bool = False,
) -> tuple[float, list[Circle]]:
    """Binary search for the smallest value that works."""

    # Keep track of the largest failure and smallest success
    largest_failure: float | None = None
    smallest_success: float | None = None
    smallest_success_circles: list[Circle] | None = None

    # Run binary search
    while end - start > PRECISION.epsilon:
        p = (start + end) / 2
        success, circles = evaluator(p)

        if success:
            end = p
            if smallest_success is None or p < smallest_success:
                smallest_success = p
                smallest_success_circles = circles
                if debug:
                    print(f'p = {p} succeeded')
        else:
            start = p
            if largest_failure is None or p > largest_failure:
                largest_failure = p
                if debug:
                    print(f'p = {p} failed')

    if smallest_success_circles is None or smallest_success is None:
        raise ValueError('No solution found')

    return smallest_success, smallest_success_circles

def covers_unit_circle_3(circles: list[Circle]) -> bool:
    circle_polygons = [PRECISION.get_circle_polygon(circle) for circle in circles]
    diff = PRECISION.unit_circle_polygon.difference(shapely.union_all(circle_polygons)) # type: ignore

    return diff.area < PRECISION.epsilon

def get_distance_traveled(circles: list[Circle], debug: bool = False):
    # D(n) = max(dist to get to kth circle + D(r_k * n))
    # max(d_k / (1 - r_k))

    # circles.sort(key=lambda circle: circle.r, reverse=True)
    distance = 0
    current_point = (0, 0)

    max_ct = 0

    for circle in circles:
        x, y, r = circle
        distance_to_circle: float = math.sqrt((x - current_point[0]) ** 2 + (y - current_point[1]) ** 2)
        
        if circle == circles[-1]:
            # Don't need to necessarily travel to center of the last circle, since we are guaranteed that it is there.
            # Only need to travel to first probe point of the next layer

            # -1 * sqrt(x^2 + y^2) * r is for getting to the first probe of the next guy.
            # the second sqrt(x^2 + y^2) * r is for the next layer not needing to
            # traverse that distance to get to its first probe
            distance_to_circle -= 2 * math.sqrt(circles[0].x**2 + circles[0].y**2) * r


        distance += distance_to_circle

        ct = distance / (1 - r)

        if debug:
            print(f"Circle {circles.index(circle) + 1}: {distance}, {r} => {ct}") 

        max_ct = max(max_ct, ct)
        current_point = (x, y)

    return max_ct

def print_latex_circles(circles: list[Circle]):
    """Print circles in a LaTeX-friendly format that can be copy-pasted."""
    for i, circle in enumerate(sorted(circles, key=lambda c: c.r, reverse=True)):
        print(f"    {{{circle.x}/{circle.y}/{circle.r}}}", end="")
        if i == len(circles) - 1:
            print("%")
        else:
            print(",")

def get_intersections(circle1: Circle, circle2: Circle):
    """Calculate the intersection points of two circles.
    Returns tuple of (x3,y3,x4,y4) representing the two intersection points,
    or None if the circles don't intersect properly."""
    x0, y0, r0 = circle1.x, circle1.y, circle1.r
    x1, y1, r1 = circle2.x, circle2.y, circle2.r

    # Calculate distance between circle centers
    d = math.sqrt((x1-x0)**2 + (y1-y0)**2)
    
    # Check intersection conditions
    if d > r0 + r1:  # Non intersecting
        return None
    if d < abs(r0-r1):  # One circle within other
        return None
    if d == 0 and r0 == r1:  # Coincident circles
        return None

    # Calculate intersection points
    a = (r0**2 - r1**2 + d**2)/(2*d)
    h = math.sqrt(r0**2 - a**2)
    
    x2 = x0 + a*(x1-x0)/d   
    y2 = y0 + a*(y1-y0)/d   
    
    x3 = x2 + h*(y1-y0)/d     
    y3 = y2 - h*(x1-x0)/d 

    x4 = x2 - h*(y1-y0)/d
    y4 = y2 + h*(x1-x0)/d
    
    return ((x3, y3), (x4, y4))

def rotate_circles(circles: list[Circle]):
    # rotate the circles such that the first circle intersects (1, 0)

    first_circle = circles[0]
    intersection_with_unit_circle = get_intersections(first_circle, UNIT_CIRCLE)
    if intersection_with_unit_circle is None:
        return circles
    
    # get the upper intersection point
    x, y = max(intersection_with_unit_circle, key=lambda point: point[1])
    
    # get angle to rotate, angle from x y to origin
    angle = math.atan2(y, x)

    rotated_circles: list[Circle] = []
    for circle in circles:
        x, y = circle.x, circle.y
        r = circle.r

        new_x = x * math.cos(angle) - y * math.sin(angle)
        new_y = x * math.sin(angle) + y * math.cos(angle)

        rotated_circles.append(Circle(new_x, -new_y, r))
    
    return rotated_circles
