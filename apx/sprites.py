# - coding: utf-8 -
# Copyright (C) 2013-2014 Toms Bauģis <toms.baugis at gmail.com>

import math
import random

from gi.repository import GObject as gobject

from .lib import graphics
from .lib.pytweener import Easing

from .lib import game_utils
from .lib import layout

from . import colors

class Label(layout.Label):
    def __init__(self, *args, **kwargs):
        layout.Label.__init__(self, *args, **kwargs)
        self.font_desc = "04b03 %d" % (kwargs.get("size") or 18)
        self.color = kwargs.get("color") or "#eee"
        self.cache_as_bitmap=True

class ScoreLabel(Label):
    """a label that takes a score attribute that can be tweened because it's
    a number"""
    def __init__(self, template="%d", score=0, *args, **kwargs):
        Label.__init__(self, *args, **kwargs)
        self.template = template
        self.score = score

    def __setattr__(self, name, val):
        Label.__setattr__(self, name, val)
        if name == "score":
            self.markup = self.template % val



class Cubic(graphics.Sprite):
    def __init__(self, color=None, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self._speeds = {
            "fast": 4,
            "slow": 2,
        }
        self.drawing_speed = self._speeds["fast"]
        self._speed = "fast"
        self.connect("on-render", self.on_render)
        self.current_line = None
        self.drawing = False
        self.snap_to_pixel = True
        self.rotation = math.radians(45)
        self.color = color or "#eee"
        self.width = self.height = 10 # for layout

    def on_render(self, sprite):
        self.graphics.fill_area(-7.5, -7.5, 14, 14, self.color)


    @property
    def current_speed(self):
        for speed_name, speed in self._speeds.items():
            if speed == self.drawing_speed:
                return speed_name
        return "fast"

    def set_drawing(self, drawing):
        self.drawing = drawing
        if drawing:
            self.drawing_speed = self.speed

    @property
    def speed(self):
        return self._speeds[self._speed]

    @speed.setter
    def speed(self, speed):
        speed_number = self._speeds[speed]
        # register the fastest speed we used to draw
        self.drawing_speed = max(self.speed, speed_number)
        self._speed = speed


    def blowup(self, callback=None, explode=True):
        def kill(sprite, do_callback=False):
            sprite.parent.remove_child(sprite)
            if do_callback and callback:
                callback(self)


        for i in range(5):
            from_scale, to_scale = 1, self.scale_x + 1 + i * 5
            from_opacity, to_opacity = 0.8, 0

            if not explode:
                to_scale, from_scale = from_scale, to_scale
                from_opacity, to_opacity = to_opacity, from_opacity


            another_cube = Cubic(x=self.x, y=self.y,
                                 scale_x=from_scale, scale_y=from_scale,
                                 opacity=from_opacity,
                                 z_order=5000-i)
            self.parent.add_child(another_cube)


            if i == 4:
                # we will hang callback to the last of the guys
                on_complete = lambda sprite: kill(sprite, True)
            else:
                on_complete = lambda sprite: kill(sprite)

            another_cube.animate(scale_x=to_scale, scale_y=to_scale,
                                 opacity=to_opacity,
                                 duration= (i + 1) / 5.0,
                                 on_complete=on_complete)

    def beam_out(self, callback=None):
        self.visible = False
        self.blowup(callback)

    def beam_in(self, callback):
        self.visible = True
        self.blowup(callback, False)


class Qix(graphics.Sprite):
    """the qix has random movement that tries to stick within the set
    degrees of angle, so that it appears to have an agenda"""

    def __init__(self, color=None, angle=0, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)

        # number of steps it takes to get from A to B
        self.min_steps = 10
        self.max_steps = 30

        # the bigger the distance the bigger the hop
        # the faster it will move
        self.min_distance = 30
        self.max_distance = 150


        self.next_ticks = 0
        self.current_tick = 0
        self.dx, self.dy = 0, 0
        self.started_moving = False
        self.next_x, self.next_y = 0, 0
        self.next_distance = 0
        self.current_angle = angle
        self.claimed = False
        self.prev_x, self.prev_y = 0, 0
        self.color = color

        self.steps = 10
        self.current_step = 0

        self.shadow_coords = []
        self.shadow_count = 15
        for i in range(self.shadow_count):
            self.add_child(graphics.Rectangle(20, 20, pivot_x=10, pivot_y=10,
                                              fill=graphics.Colors.darker(self.color, i * 5),
                                              opacity=0.8 - (i * 0.7 / self.shadow_count)))
        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        if not self.debug:
            return
        self.graphics.move_to(-10, -10)
        self.graphics.line_to([(+10, -10),
                               (+10, +10),
                               (-10, +10),
                               (-10, -10)])
        self.graphics.stroke("#f00")


    def explode(self):
        for i, sprite in enumerate(self.sprites):
            degree = math.radians(i * 1.0 / len(self.sprites) * 360)
            sprite.animate(x=math.cos(degree) * 1200,
                           y=math.sin(degree) * 1200,
                           scale_x = 20,
                           scale_y = 20,
                           duration=1.4,
                          # fill="#fff",
                           rotation=120,
                           easing=Easing.Expo.ease_in,
                           )
            #self.animate(rotation=10, duration=1.4)


    def move(self, game_rects):
        if not self.started_moving:
            self.started_moving = True
            self.next_target(self)

        self.current_step += 1

        # push us closer to the target
        factor = Easing.Linear.ease_in(self.current_step * 1.0 / self.steps)
        x = self.prev_x * (1 - factor) + self.next_x * factor
        y = self.prev_y * (1 - factor) + self.next_y * factor

        self.x, self.y = x, y

        self.shadow_coords.insert(0, (x, y))
        self.shadow_coords = self.shadow_coords[:self.shadow_count]


        if self.current_step == self.steps:
            self.next_target()

        self._update_children()




    def touching_poly(self, poly):
        poly_lines = [(dot1, dot2) for dot1, dot2 in zip(poly, poly[1:])]
        x1, y1, x2, y2 = int(self.x) - 10, int(self.y) - 10, \
                         int(self.x) + 10, int(self.y) + 10
        qix_box = game_utils._bounding_box((x1, y1), (x2, y2))

        # first do a cheap run on the bounding box
        if len(poly_lines) > 1:
            (xb1, yb1), (xb2, yb2) = game_utils.box_range(poly)
            if not any((xb1 <= x <= xb2 and yb1 <= y <= yb2 for (x, y) in qix_box)):
                return False

        for line1 in zip(qix_box, qix_box[1:]):
            for line2 in poly_lines:
                if game_utils.intersection(line1, line2):
                    return True


    def next_target(self, sprite=None):
        self.prev_x, self.prev_y = self.x, self.y

        scene = self.get_scene()
        if not scene:
            return

        game_rects, game_poly = scene.board.game_rects, scene.board.game_area

        game_lines = [(dot1, dot2) for dot1, dot2 in zip(game_poly, game_poly[1:])]

        delta_angle = 0
        angle_range = 180

        in_area, stuck = False, 0
        while not in_area and stuck < 10:
            stuck += 1
            delta_angle = self.current_angle - math.radians(angle_range / 2) + random.random() * math.radians(angle_range)

            distance = random.randint(self.min_distance, self.max_distance)

            x, y = self.x + distance * math.cos(delta_angle), self.y + distance * math.sin(delta_angle)
            x, y = int(x), int(y)

            dots = [(x, y)]
            in_area = all((game_utils.in_area(dot, game_rects) for dot in dots))

            if in_area:
                # check for overlaps
                line_pairs = ((((x, y), (self.x, self.y)), line) for line in game_lines)
                for pair in line_pairs:
                    if game_utils.intersection(*pair):
                        in_area = False
                        break


            if not in_area:
                angle_range += 60


        self.current_angle = delta_angle % math.radians(360)

        self.steps = random.randint(self.min_steps, self.max_steps)
        self.current_step = 0

        if stuck < 10:
            self.next_x, self.next_y = x, y
            self.next_distance = distance

    def _update_children(self):
        x2, y2 = self.x, self.y
        for i, (x, y) in enumerate(self.shadow_coords):
            sprite = self.sprites[i]
            sprite.x, sprite.y = x - x2 - 10, y - y2 - 10
            sprite.rotation += 0.05


class Spark(graphics.Sprite):
    __gsignals__ = {
        "confused": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    def __init__(self, speed = 3, clockwise=True, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.clockwise = clockwise
        self.speed = speed

        self._polys_stack = []
        self.current_line = None
        self.frozen = True

        self.connect("on-render", self.on_render)

    def on_render(self, sprite):
        self.graphics.fill_area(-5.5, -5.5, 10, 10, "#fff")

    def next(self, dot, poly):
        return game_utils.next_dot(dot, poly) if self.clockwise else game_utils.prev_dot(dot, poly)


    def show_confusion(self):
        self.emit("confused")
        def comeback(sprite):
            def unfreeze(sprite):
                self.frozen = False
                self.clockwise = not self.clockwise
            self.animate(scale_x=1, scale_y=1,
                         duration=1,
                         easing=Easing.Sine.ease_out,
                         on_complete=unfreeze)

        self.frozen = True
        self.animate(scale_x=2, scale_y=2,
                     duration=1,
                     rotation=self.rotation - math.pi/2,
                     easing=Easing.Sine.ease_out,
                     on_complete=comeback)

    def move(self, poly):
        if self.frozen:
            return

        dot = (self.x, self.y)

        # check if we are still on the new poly, because if we are not, then
        # we will keep walking the old one until we get back on track
        if game_utils.on_line(dot, poly):
            self._polys_stack = [poly]
        else:
            if poly not in self._polys_stack:
                self._polys_stack.append(poly)

                if len(self._polys_stack) == 2:
                    self.show_confusion()

            # we go from the freshest to oldest poly to see if we can find ourselves
            for i, p in enumerate(reversed(self._polys_stack)):
                if game_utils.on_line(dot, p):
                    poly = p
                    break

        if not poly:
            return

        dot2 = None
        if dot in poly:
            dot2 = self.next(dot, poly)
        else:
            line = game_utils.on_line(dot, poly)
            if not line:
                return
            dot2 = line[1] if self.clockwise else line[0]


        # distance is sum because one of them will be the same

        speed = self.speed
        while speed > 0:
            distance = game_utils.distance(dot, dot2)
            direction = 1 if any ((a<b for a, b in zip(dot, dot2))) else -1

            step_speed = min(speed, distance)

            if dot[0] == dot2[0]:
                # vertical movement
                self.y += step_speed * direction
            else:
                # horizontal movement
                self.x += step_speed * direction

            distance = distance - step_speed
            if distance == 0:
                dot, dot2 = dot2, self.next(dot2, poly)

            speed = speed - step_speed

        self.current_line = game_utils.on_line((self.x, self.y), poly)


class ClaimedPoly(graphics.Polygon):
    def __init__(self, points, poly_type, **kwargs):
        kwargs["points"] = points
        graphics.Polygon.__init__(self, **kwargs)
        self.visible = False
        self.cache_as_bitmap = True
        self.poly_type = poly_type

    def appear(self):
        self.visible = True
        current_fill = self.fill
        self.fill = "#333"
        self.line_width = 3
        self.animate(0.7, easing=Easing.Cubic.ease_out, fill=current_fill)

    def __setattr__(self, name, val):
        graphics.Polygon.__setattr__(self, name, val)
        if name == "poly_type":
            self.fill = getattr(colors, "claim_%s" % val)
            self.stroke = graphics.Colors.darker(self.fill, -50)
