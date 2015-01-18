import math

def line_formula(dot_a, dot_b):
    # what we are actually looking for is the relationship between x and y
    # and then the displacement?
    if dot_a[0] > dot_b[0]:
        dot_a, dot_b = dot_b, dot_a

    if dot_a[0] == dot_b[0]:
        return dot_a[0], None
    else:
        y_ratio = (dot_b[1] - dot_a[1]) * 1.0 / (dot_b[0] - dot_a[0])

    # y = mx + b
    # b = y - mx
    intercept = dot_b[1] - dot_b[0] * y_ratio

    #if y_ratio < 0:
    #    y_ratio, intercept = -y_ratio, -intercept

    return y_ratio, intercept



def intersection(line1, line2):
    if line1[0][0] > line1[1][0]:
        line1 = (line1[1], line1[0])
    if line2[0][0] > line2[1][0]:
        line2 = (line2[1], line2[0])


    ratio1, offset1 = line_formula(*line1)
    ratio2, offset2 = line_formula(*line2)

    def overlap(line1, line2):
        for point in line1 + line2:
            if on_line(point, line1) and on_line(point, line2):
                return point
        return None

    # if both lines are vertical the ratio contains X and we check if these two overlap
    if offset1 is None and offset2 is None:
        if ratio1 == ratio2:
            # if both lines are parallel, any point in the overlap will do
            # if there is one
            return overlap(line1, line2) # if there is no overlap then we are like whatever
        else:
            return None

    # in parallel lines check for overlap
    if ratio1 == ratio2:
        if offset1 == offset2:
            return overlap(line1, line2)
        return None


    # if one of the lines is vertical, we calculate where the other line crosses it
    if offset1 is None or offset2 is None:
        if offset1 is None:
            ratio1, offset1, x = ratio2, offset2, ratio1
            line1, line2 = line2, line1
        else:
            ratio1, offset1, x = ratio1, offset1, ratio2

        y = int(ratio1 * x + offset1)

        if (line1[0][0] <= x <= line1[1][0]) and on_line((x, y), line2):
            return (x, y)
        else:
            return None

    else:
        x = (offset2 - offset1) / (ratio1 - ratio2)



    if (line1[0][0] <= x <= line1[1][0]) and (line2[0][0] <= x <= line2[1][0]):
        return x, ratio1 * x + offset1
    else:
        return None


def chain(poly):
    """links from first to last, add first item as last if you want a full circle"""
    for dot, next_dot in zip(poly, poly[1:]):
        yield dot, next_dot

def lines(poly):
    """returns dict of previous and next nodes for cheaper checks"""
    prevs, nexts = {}, {}
    for prev, next in chain(poly + [poly[0]]):
        prevs[next] = prev
        nexts[prev] = next

    return prevs, nexts


def on_line(dot, poly):
    """checks if x and y is on the line of the given polygons
       and returns the line
    """
    x, y = dot
    for ((prev_x, prev_y), (next_x, next_y)) in zip(poly, poly[1:]):
        if x == prev_x == next_x and (prev_y <= y <= next_y or prev_y >= y >= next_y):
            return (prev_x, prev_y), (next_x, next_y)

        if y == prev_y == next_y and (prev_x <= x <= next_x or prev_x >= x >= next_x):
            return (prev_x, prev_y), (next_x, next_y)

    return None



def cleanup_poly(poly):
    """drop dupe points and remove points that are on the same line"""
    if poly[0] == poly[-1]:
        poly = poly[:-1]

    # start from top-most edge so we have clean poly
    top = None
    for dot in poly:
        if not top or (dot[0] <= top[0] and dot[1] <= top[1]):
            top = dot

    prev_dot = None
    res = []
    for dot in _start_with(top, poly):
        if dot != prev_dot:
            res.append(dot)
        prev_dot = dot

    prevs, nexts = lines(res)
    for dot in list(res):
        line = prevs[dot], nexts[dot]
        if on_line(dot, line):
            res.remove(dot)

    return res + [res[0]]



def prev_dot(dot, poly):
    if poly[0] == poly[-1]:
        poly = poly[:-1]

    idx = poly.index(dot) - 1
    if idx < 0:
        idx = len(poly) - 1
    return poly[idx]

def next_dot(dot, poly):
    if poly[0] == poly[-1]:
        poly = poly[:-1]

    idx = poly.index(dot) + 1
    if idx >= len(poly):
        idx = 0
    return poly[idx]

def _bounding_box(dot1, dot2):
    """construct bounding box of two dots by combining min and max values"""
    (x1, y1), (x2, y2) = box_range((dot1, dot2))
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]

def box_range(dots):
    x1, x2 = min((dot[0] for dot in dots)), max((dot[0] for dot in dots))
    y1, y2 = min((dot[1] for dot in dots)), max((dot[1] for dot in dots))
    return (x1, y1), (x2, y2)





def in_area(dot, rects, on_line=False):
    """checks if the dot is in the area, ignores borders"""
    x, y = int(dot[0]), int(dot[1])
    for rect in rects:
        minx, maxx = min((dot[0] for dot in rect)), max((dot[0] for dot in rect))
        miny, maxy = min((dot[1] for dot in rect)), max((dot[1] for dot in rect))

        if on_line:
            if minx <= x <= maxx and miny <= y <= maxy:
                return True
        else:
            if minx < x < maxx and miny < y < maxy:
                return True


    return False

def distance(dot1, dot2):
    (x1, y1), (x2, y2) = dot1, dot2
    return math.sqrt((x1 - x2) ** 2 + (y1-y2) ** 2)


def total_area(rects):
    res = 0
    for rect in rects:
        minx, maxx = min((dot[0] for dot in rect)), max((dot[0] for dot in rect))
        miny, maxy = min((dot[1] for dot in rect)), max((dot[1] for dot in rect))

        res += (maxx-minx) * (maxy-miny)

    return res




def _valid_box(box, poly):
    # sanity check - the bounding box has to consist of 4 points
    if len(set(box)) < 4:
        return False

    # sanity check - all four dots have to be on the poly line
    if not all((on_line([x, y], poly) for x, y in box)):
        return False

    # sanity check - the box can't cover any dots
    dot1, dot2 = box_range(box)
    for dot in poly:
        if dot1[0] < dot[0] < dot2[0] and dot1[1] < dot[1] < dot2[1]:
            return False

    return True



def triangulate(poly):
    """go mad and draw triangles"""
    for dot1 in poly:
        # we go around the poly and try to create a rectangle by taking
        # the one after the next one dot and doing a bounding box on that
        box = _bounding_box(dot1, next_dot(next_dot(dot1, poly), poly))


        if set(poly) == set(box):
            # just a rect
            return [box + [box[0]]]


        if not _valid_box(box, poly):
            continue

        cut_a, cut_b = None, None

        # if one of the points is new, then we cut from that to the dot it's not on the line
        # if all four dots are in the poly, we cut where there is a dot between
        new_dots = set(box) - set(poly)
        if not new_dots:
            for dot in box:
                if next_dot(dot, box) != next_dot(dot, poly):
                    cut_a, cut_b = dot, next_dot(dot, box)
                    break

        else:
            dot = list(new_dots)[0]
            # sanity check - the prev->prev direction should observe the same direction that the main poly has
            prev = prev_dot(dot, box)
            if prev_dot(prev, box) != prev_dot(prev, poly):
                continue

            #the newcomer can connect to just two dots
            # figure out the other end - it's the one it's not connected to
            dota, dotb = prev_dot(dot, box), next_dot(dot, box)
            other_end = dotb if on_line(dot, [prev_dot(dota, poly), dota, next_dot(dota, poly)]) else dota

            cut_a, cut_b = dot, other_end


        if not cut_a or not cut_b:
            # nothing to cut - move on
            continue


        # check if we have anyone between the proposed cut
        # if so - there can be just one
        # also we will move the cut line then

        inbetweeners = []
        for dot in set(poly) - set([cut_a, cut_b]):
            if on_line(dot, [cut_a, cut_b]):
                inbetweeners.append(dot)

        if inbetweeners:
            if len(inbetweeners) > 1:
                continue
            dot = inbetweeners[0]
            cut_a, cut_b = (cut_a, dot) if cut_a not in poly or (prev_dot(cut_a, poly) != dot and next_dot(cut_a, poly) != dot) else (dot, cut_b)


        small, big = cut_poly(poly, [cut_a, cut_b])
        if set(box) != set(small) and set(box) != set(big):
            continue

        if set(box) != set(small):
            small, big = big, small

        return [box + [box[0]]] + (triangulate(big) or [])


def _start_with(dot, poly):
    # wrap the poly around so it starts with the specified dot
    idx = poly.index(dot)
    return poly[idx:] + poly[:idx]



def cut_poly(big, poly):
    """cuts the poly out of big and returns the result
       the code is rather brute force and hard to chew. good luck
    """
    # find where we start on the line
    connect_start = on_line(poly[0], big)
    connect_end = on_line(poly[-1], big)


    start_idx, end_idx = big.index(connect_start[0]), big.index(connect_end[0])

    # make sure we always go clockwise
    if end_idx < start_idx:
        poly = list(reversed(poly))

    elif end_idx == start_idx:
        # if it's the same line then match the direction of the parent
        (poly_x1, poly_y1), (poly_x2, poly_y2) = poly[0], poly[-1]
        (x1, y1), (x2, y2) = connect_start

        if ((poly_x1 < poly_x2) != (x1 < x2)) or ((poly_y1 < poly_y2) != (y1 < y2)):
            poly = list(reversed(poly))


    end_dot = on_line(poly[0], big)[0]
    start_dot = on_line(poly[-1], big)[1]

    if start_dot == end_dot:
        # we ate a corner and now are all confused
        start_dot = next_dot(start_dot, big)
        end_dot = prev_dot(end_dot, big)
        poly = list(reversed(poly))


    side_a = _start_with(start_dot, big)
    side_a = poly + side_a[:side_a.index(end_dot) + 1]

    inside_dots = set(big) - set(side_a)
    side_b = [dot for dot in _start_with(prev_dot(end_dot, big), big) if dot in inside_dots]
    side_b = side_b + list(reversed(poly))

    return cleanup_poly(side_a), cleanup_poly(side_b)
