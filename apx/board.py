# - coding: utf-8 -
# Copyright (C) 2013-2014 Toms Bauģis <toms.baugis at gmail.com>

import datetime as dt
from gi.repository import Gdk as gdk
import math
import random

import itertools

from . import sprites

from .lib import game_utils
from .lib import graphics
from .lib import layout
from .lib import utils
from .lib.pytweener import Easing


class StatePanel(layout.VBox):
    """score, lives, next spark spawn time"""
    def __init__(self):
        layout.VBox.__init__(self, expand=False)
        self.label_claimed = sprites.ScoreLabel("<b>Claimed: %d%%</b>", x_align=0, width=250)
        self.label_score = sprites.ScoreLabel("<b>Points: %d</b>", x_align=0, width=250)

        self.label_level = sprites.ScoreLabel("<b>LEVEL %d</b>", x_align=0, size=38,
                                              color="#ddd")

        self.lifes_container = layout.HBox(expand=False, fill=False,
                                           spacing=20, x_align=1,
                                           padding_top=10) # padding as cubic is drawing into negative

        self.add_child(layout.HBox([
            layout.VBox([
                self.label_claimed,
                self.label_score
            ]),
            self.label_level,
            layout.VBox([
                self.lifes_container
            ])
        ]))


    def update(self, game):
        self.label_score.animate(score=game.total_stats['score'],
                                 easing=Easing.Expo.ease_in_out)
        self.label_claimed.animate(score=game.stats['claimed_percent'],
                                   easing=Easing.Expo.ease_in_out)
        self.label_level.score = game.level


        lives_diff = game.lives - len(self.lifes_container.sprites)
        if lives_diff > 0:
            # life
            for i in range(lives_diff):
                cube = sprites.Cubic()
                self.lifes_container.add_child(cube)
                cube.scale_x = cube.scale_y = 0.1
                cube.color = "#4f4"

                cube.animate(scale_x=1, scale_y=1,
                             color="#eee",
                             rotation=math.pi * 2 + math.radians(45),
                             duration=1.5,
                             easing=Easing.Bounce.ease_out)

        elif lives_diff < 0:
            # death
            for i in range(min(-lives_diff, len(self.lifes_container.sprites))):
                cube = self.lifes_container.sprites[i]

                def drop(cube):
                    cube.parent.remove_child(cube)
                cube.color = "#f00"
                cube.animate(rotation=0, color="#f00",
                             opacity=0, x=-500,
                             duration=1.5,
                             easing=Easing.Expo.ease_in_out,
                             on_complete=drop)




class GameBoard(graphics.Sprite):
    """the game board with the cube, the sparks and so on"""
    def __init__(self, start_area, sparks=2, qix=1):
        graphics.Sprite.__init__(self, snap_to_pixel=False)

        # outer box - always relevant
        self._start_game_area = start_area

        #: the current available game area
        self.game_area = start_area
        self.scale_x, self.scale_y = 1, 1

        (x, y), (x2, y2) = game_utils.box_range(self.game_area)
        self.width, self.height = x2 - x, y2 - y

        self.claimed_polys_containter = graphics.Sprite()
        self.add_child(self.claimed_polys_containter)


        self.current_polygon = []

        self.current_polygon_path = graphics.Polygon([], stroke="#eee", line_width=3)
        self.add_child(self.current_polygon_path)

        self.game_area_path = graphics.Polygon([], stroke="#eee", line_width=3)
        self.add_child(
            graphics.Polygon(self.game_area, stroke="#eee", line_width=3, z_order=500),
            self.game_area_path,
        )


        self._current_direction = None

        self.claimed_polys = []



        self.cube = sprites.Cubic(x=x2 / 2, y = y2)
        self.add_child(self.cube)

        self.sparks_waiting = []
        self.sparks = []
        self.spark_throttle_secs = 1.5
        for i in range(sparks):
            self.sparks_waiting.append(sprites.Spark(x=x2 / 2, y=y, speed=2 + (i / 5.0), clockwise = i % 2 ==0))


        self.qix = []
        qix_colors = ["#afe", "#FEF4AF"]
        for i in range(qix):
            self.qix.append(sprites.Qix(x=x2 / 2,
                                        y=y2 / 2,
                                        angle=(i * 360.0 / qix),
                                        color=qix_colors[i % len(qix_colors)]))

        self.add_child(*self.qix)

        self.game_rects = game_utils.triangulate(self.game_area)

        self.level_start = None
        # outer container - want to keep that always
        #self.connect("on-render", self.on_render)



    def tick(self):
        now = dt.datetime.now()
        self.level_start = self.level_start or now
        elapsed  = now - self.level_start
        elapsed = elapsed.seconds + elapsed.microseconds / 1000000.0

        if self.sparks_waiting and elapsed > len(self.sparks) * self.spark_throttle_secs:
            spark = self.sparks_waiting.pop()
            spark.opacity = 0
            spark.frozen = True
            self.sparks.append(spark)
            self.add_child(spark)

            def push_spark(spark):
                spark.frozen = False

            spark.animate(opacity=1, duration=1, on_complete=push_spark)


        for spark in self.sparks:
            spark.move(self.game_area)

        for qix in self.qix:
            # TODO - bounce against newly formed points
            qix.move(self.game_rects)



    def in_game_bounds(self, dot):
        return game_utils.in_area(dot, [self._start_game_area])


    def in_free_area(self, dot):
        """checks if the dot is in the free area"""
        if not self.in_game_bounds(dot):
            # first we check if the dot is within out game area
            return False

        return game_utils.in_area(dot, self.game_rects, on_line=True)


    def close_claim(self, poly, speed, game):
        inside, outside = game_utils.cut_poly(self.game_area, poly)

        # we will triangulate only one of the guys
        # then we check if it is the bigger portion (last known area minus new)

        total_area = game_utils.total_area([self._start_game_area])
        prev_remaining = total_area - game.stats['claimed_area']

        rects_out = game_utils.triangulate(outside) or []

        qixes = [qix for qix in self.qix if not qix.claimed]
        # flip sides if the qix is not in the game area - can't claim
        # qix space
        claimed_qix = []
        for qix in qixes:
            if not game_utils.in_area((qix.x, qix.y), rects_out, on_line=True):
                claimed_qix.append(qix)

        claimed_area = prev_remaining - game_utils.total_area(rects_out)
        available_area = prev_remaining - claimed_area

        if (len(claimed_qix) > len(qixes) / 2.0) or (available_area < claimed_area and len(claimed_qix) >= len(qixes)):
            # outside normally should be bigger than inside
            # exception is when we have more qix on the smaller patch
            inside, outside = outside, inside
            rects_out = game_utils.triangulate(outside) or []
            claimed_area = prev_remaining - game_utils.total_area(rects_out)


        for qix in qixes:
            if not game_utils.in_area((qix.x, qix.y), rects_out, on_line=True):
                qix.claimed = True

        self.game_rects = rects_out
        self.game_area = outside
        self.game_area_path.points = outside

        claimed = sprites.ClaimedPoly(inside, speed)
        self.claimed_polys_containter.add_child(claimed)
        claimed.appear()
        self.claimed_polys.append((inside, 1))

        for qix in self.qix:
            # make sure they are not easing some place nasty
            qix.next_target()

        game.update_score(claimed_area, speed)


    def _handle_keys(self, keys_down, game):
        x, y = self.cube.x, self.cube.y


        # if we have direction, we know that user wants to do something
        # when drawing hasn't been initiated, user can move around the game poly
        # moving around game poly means the dot is on the line at any given time


        # when drawing is started, user can move all over the place but can't bump
        # into the current drawing polygon
        # path is closed if the move ends up on the game poly
        #

        # both cases we will want to adjust the new_x or new direction so that
        # it is somewhere on the line
        game_poly_dot, non_game_poly_dot = None, None


        current_pos = (self.cube.x, self.cube.y)
        if current_pos in self.game_area:
            current_line = [game_utils.prev_dot(current_pos, self.game_area),
                            current_pos,
                            game_utils.next_dot(current_pos, self.game_area)]
        else:
            current_line = game_utils.on_line(current_pos, self.game_area)

        key_directions = {
            gdk.KEY_Left: "left",
            gdk.KEY_j: "left",
            gdk.KEY_J: "left",

            gdk.KEY_Right: "right",
            gdk.KEY_l: "right",
            gdk.KEY_L: "right",

            gdk.KEY_Up: "up",
            gdk.KEY_i: "up",
            gdk.KEY_I: "up",

            gdk.KEY_Down: "down",
            gdk.KEY_k: "down",
            gdk.KEY_K: "down",
        }

        direction = None
        for keyval in reversed(keys_down):
            if keyval in key_directions:
                direction = key_directions[keyval]
                break

        if not direction:
            return
        speed_direction = 1 if direction in ("right", "down") else -1

        # find the furthest step we can take for the next game polygon dot
        # when not drawing that's as far as we can go on current line
        # when drawing, that's the closest border within step
        for speed in reversed(list(range(self.cube.speed))):
            game_x = x if direction in ("up", "down") else x + (speed + 1) * speed_direction
            game_y = y if direction in ("left", "right") else y + (speed + 1) * speed_direction

            if current_line:
                if not game_poly_dot and game_utils.on_line((game_x, game_y), current_line):
                    # if we are on a line then we are looking for the max position at
                    # which we still have a hit
                    game_poly_dot = (game_x, game_y)
            else:
                # roaming around - checking if the next move is valid
                if game_utils.on_line((game_x, game_y), self.game_area):
                    game_poly_dot = (game_x, game_y)



        # look for the furthest valid non-game poly
        # we stop when we find non-poly point and then bump into an on-line point
        for speed in range(self.cube.speed):
            game_x = x if direction in ("up", "down") else x + (speed + 1) * speed_direction
            game_y = y if direction in ("left", "right") else y + (speed + 1) * speed_direction

            on_line = game_utils.on_line((game_x, game_y), self.game_area)

            if not self.in_game_bounds((game_x, game_y)):
                break

            if not on_line:
                non_game_poly_dot = (game_x, game_y)
            elif on_line and non_game_poly_dot:
                break


        space_down = any([key in keys_down for key in (gdk.KEY_space, gdk.KEY_Shift_L, gdk.KEY_Shift_R)])
        if space_down and non_game_poly_dot and not game.claiming:
            if game_utils.in_area(non_game_poly_dot, self.game_rects, on_line=True):
                game.claiming = True
                self.cube.set_drawing(True)
                self._current_direction = None


        if game.claiming and self._current_direction != direction:
            self._current_direction = direction
            if (self.cube.x, self.cube.y) not in self.current_polygon:
                self.current_polygon.append((self.cube.x, self.cube.y))


        # when we are drawing, we can move outside the claimed poly's
        # when we are moving around, we can move only within the poly
        # check if the move is valid
        # we will go through all lines and check that our path is not
        # intersecting
        if game.claiming and game_poly_dot:
            self.close_claim(self.current_polygon + [game_poly_dot],
                             self.cube.current_speed,
                             game)
            game.claiming = False
            self.cube.set_drawing(False)
            self.current_polygon = []
            self.current_polygon_path.points = []
            self.cube.x, self.cube.y = game_poly_dot
            self.cube.current_line = game_utils.on_line(game_poly_dot, self.game_area)
            return


        on_current_poly = non_game_poly_dot and game_utils.on_line(non_game_poly_dot, self.current_polygon) is not None
        if game.claiming and not on_current_poly and non_game_poly_dot:
            if game_utils.in_area(non_game_poly_dot, self.game_rects, on_line=True):
                self.cube.x, self.cube.y = non_game_poly_dot
                self.current_polygon_path.points = self.current_polygon + [non_game_poly_dot]

        if not game.claiming and game_poly_dot:
            # legal move is one where the next dot is on the same line as the prev one
            line = game_utils.on_line([self.cube.x, self.cube.y], self.game_area)
            new_line, good_lines = None, []
            if line:
                prev1, prev2 = line
                lines = [(dot1, dot2) for dot1, dot2 in zip(self.game_area, self.game_area[1:])]
                lines.append((self.game_area[-1], self.game_area[0]))
                good_lines = [line for line in lines if prev1 in line or prev2 in line]
                new_line = game_utils.on_line(game_poly_dot, self.game_area)


            if new_line in good_lines:
                self.cube.x, self.cube.y = game_poly_dot
                self.cube.current_line = new_line


    def check_death(self, claiming):
        x, y = self.cube.x, self.cube.y
        if not claiming:
            # while not claiming beware of sparks
            for spark in self.sparks:
                if set(spark.current_line or []) & set(self.cube.current_line or []):
                    if game_utils.distance((x, y), (spark.x, spark.y)) < 10:
                        # on spark collision spark dies
                        self.sparks.remove(spark)
                        spark.parent.remove_child(spark)
                        return True

        else:
            # while claiming beware of Qix
            for qix in self.qix:
                if game_utils.distance((x, y), (qix.x, qix.y)) < 20:
                    return True

                if qix.touching_poly(self.current_polygon + [(self.cube.x, self.cube.y)]):
                    return True
        return False


    def death(self, callback):
        def followup(cube):
            if self.current_polygon:
                cube.x, cube.y = self.current_polygon[0]

            scene = cube.get_scene()
            self.current_polygon = []
            self.current_polygon_path.points = []
            cube.beam_in(callback)

        self.cube.beam_out(followup)
