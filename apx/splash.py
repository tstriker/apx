#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 Toms Baugis <toms.baugis@gmail.com>

"""Exploring symmetry. Feel free to add more handles!"""
import math
import random

from collections import defaultdict
from gi.repository import Gtk as gtk
from gi.repository import GObject as gobject
from gi.repository import Pango as pango

from .lib import graphics
from .lib.pytweener import Easing

from . import sprites

class Point(gobject.GObject):
    __gsignals__ = {
        "on-point-changed": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }
    def __init__(self, x=0, y=0):
        gobject.GObject.__init__(self)
        self.x = x
        self.y = y

    def __setattr__(self, name, val):
        if hasattr(self, name) and getattr(self, name) == val:
            return

        gobject.GObject.__setattr__(self, name, val)
        self.emit("on-point-changed")

    def __repr__(self):
        return "<%s x=%d, y=%d>" % (self.__class__.__name__, self.x, self.y)

    def __iter__(self):
        yield self.x
        yield self.y

class Line(object):
    def __init__(self, a, b, anchor=None):
        self.a, self.b = a, b

        # anchor can be either dot A or dot B
        self.anchor = anchor or self.a

    @property
    def length(self):
        return math.sqrt((self.a.x - self.b.x) ** 2 + (self.a.y - self.b.y) ** 2)

    @property
    def rotation(self):
        a = self.anchor
        b = self.b if a != self.b else self.a
        return math.atan2(b.x - a.x, b.y - a.y)

    def __setattr__(self, name, val):
        if name == "rotation":
            self.set_rotation(val)
        else:
            object.__setattr__(self, name, val)

    def set_rotation(self, radians):
        a = self.anchor
        b = self.b if a != self.b else self.a

        length = self.length

        b.x = a.x + math.cos(radians - math.radians(90)) * length
        b.y = a.y + math.sin(radians - math.radians(90)) * length


class SymmetricalRepeater(graphics.Sprite):
    def __init__(self, sides, poly=None, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)

        poly = poly or [(0, 0), (0, 0)]

        self.master_poly = [Point(*coords) for coords in poly]
        for point in self.master_poly:
            point.connect("on-point-changed", self.on_master_changed)

        self.sides = []
        for i in range(sides):
            side = [Point(*coords) for coords in poly]
            self.sides.append(side)
            for point in side:
                point.connect("on-point-changed", self.on_side_changed)

        self.connect("on-render", self.on_render)


    def on_master_changed(self, point):
        """propagate to the kids"""
        idx = self.master_poly.index(point)
        for side in self.sides:
            side[idx].x, side[idx].y = point.x, point.y

    def on_side_changed(self, point):
        self._sprite_dirty = True

    def on_render(self, sprite):
        angle = 360.0 / len(self.sides)


        # debug
        """
        self.graphics.save_context()
        for i in range(len(self.sides)):
            self.graphics.move_to(0, 0)
            self.graphics.line_to(1000, 0)
            self.graphics.rotate(math.radians(angle))
        self.graphics.stroke("#3d3d3d")
        self.graphics.restore_context()
        """

        self.graphics.set_line_style(3)


        for side in self.sides:
            self.graphics.move_to(*side[0])
            for point in side[1:]:
                self.graphics.line_to(*point)
            self.graphics.rotate(math.radians(angle))
        self.graphics.stroke("#fafafa")



class Scene(graphics.Scene):
    def __init__(self):
        graphics.Scene.__init__(self, background_color="#333")

        self.repeater2 = None

        self.container = graphics.Sprite()
        self.add_child(self.container)

        self.connect("on-first-frame", self.on_first_frame)
        self.connect("on-resize", self.on_resize)


    def appear1(self, parent, callback):
        def clone_grow(repeater, on_complete=None):
            repeater2 = SymmetricalRepeater(len(repeater.sides),
                                            repeater.master_poly)
            parent.add_child(repeater2)
            a, b = repeater2.master_poly

            self.animate(a, x=diagonal, delay=0.3, duration=1.3)
            self.animate(b, y=-diagonal, delay=0.3, duration=1.3)

            if on_complete:
                on_complete()

        repeater = SymmetricalRepeater(4)
        parent.add_child(repeater)

        a, b = repeater.master_poly

        # push the dots away at the beginning
        a.x, b.x = 1000, 1000

        size = 100
        diagonal = math.sqrt(100**2 + 100**2)

        graphics.chain(
            # fly in
            self.animate, {"sprite": a, "x": size, "duration": 1, "easing": Easing.Expo.ease_in_out},

            self.animate, {"sprite": Line(a, b), "rotation": math.radians(-45), "duration": 0.8},

            #clone_grow, {"repeater": repeater},
            #repeater, {"rotation": math.radians(-45), "duration": 1.3, "delay": 0.3},

            callback, {},
        )

        # parallel chains
        graphics.chain(
            self.animate, {"sprite": b, "x": size + diagonal, "duration": 1, "easing": Easing.Expo.ease_in_out},
        )



    def appear2(self, parent, callback):
        size = 100
        diagonal = math.sqrt((2 * size) ** 2)

        repeater = SymmetricalRepeater(4)
        parent.add_child(repeater)

        poly = [(1000, 0), (size, 0), (1000, 0)]
        repeater2 = SymmetricalRepeater(4, poly)


        def appear21(on_complete=None):
            parent.add_child(repeater2)
            a, b, c = repeater2.master_poly

            self.animate(Line(b, a), rotation=math.radians(-45), duration=0.7, easing=Easing.Expo.ease_in_out)
            self.animate(Line(b, c), rotation=math.radians(225), duration=0.7, easing=Easing.Expo.ease_in_out)
            repeater2.animate(rotation=math.radians(-90), duration=0.7, easing=Easing.Expo.ease_in_out,
                              on_complete=on_complete)

        def disappear21(on_complete):
            a, b = repeater.master_poly
            c, d, e = repeater2.master_poly
            graphics.chain(
                self.animate, {"sprite": b, "x": 0, "duration": 0.6, "easing": Easing.Expo.ease_out},
                on_complete, {}
            )

            self.animate(d, x=d.x + 3000, duration=2.3, easing=Easing.Expo.ease_out)
            self.animate(c, x=c.x + 3000, duration=2.3, easing=Easing.Expo.ease_out)
            self.animate(e, x=e.x + 3000, duration=2.3, easing=Easing.Expo.ease_out)



        a, b = repeater.master_poly

        # push the dots away at the beginning
        a.x, b.x = 1000, 1000

        def add_outline(on_complete=None):
            self._add_outline(parent, on_complete)

        graphics.chain(
            # fly in
            self.animate, {"sprite": a, "x": 0, "duration": 1.3},
            appear21, {},
            add_outline, {},
            disappear21, {},
            callback, {},
        )

    def _add_outline(self, parent, on_complete=None):
        cube2 = graphics.Polygon([(100, 0), (0, -100), (-100, 0), (0, 100), (100, 0)],
                                stroke="#fafafa", line_width=3)
        parent.add_child(cube2)
        if on_complete:
            on_complete()


    def appear3(self, parent, callback):
        repeater = SymmetricalRepeater(4)
        parent.add_child(repeater)

        size = 100
        diagonal = math.sqrt(100**2 + 100**2)

        def appear31(on_complete=None):
            poly = [(size, 0), (size, 0), (size, 0)]
            repeater2 = SymmetricalRepeater(4, poly)
            parent.add_child(repeater2)
            a, b, c = repeater2.master_poly

            self.animate(a, x=0, y=size, duration=1)
            self.animate(c, x=0, y=-size, duration=1, on_complete=on_complete)


        a, b = repeater.master_poly

        # push the dots away at the beginning
        a.x, b.x = 1000, 1000

        graphics.chain(
            # fly in
            self.animate, {"sprite": a, "x": 0, "duration": 1.3},
            appear31, {},
            callback, {},
        )

        graphics.chain(
            # fly in
            self.animate, {"sprite": b, "x": size, "duration": 1.3},
        )


    def on_first_frame(self, scene, context):
        func = random.choice([self.appear1, self.appear2, self.appear3])
        func(self.container, lambda: self.on_intro_done())

    def on_resize(self, scene, event):
        self.container.x = self.width / 2
        self.container.y = self.height / 2

    def on_intro_done(self):
        container = self[0]

        cube = graphics.Polygon([(100, 0), (0, -100), (-100, 0), (0, 100)],
                                fill="#fafafa", opacity=0)
        title = sprites.Label("APX", size=200, y=150, opacity=0)
        title.x = -title.width / 2

        description = sprites.Label("A cousine of QIX\nPress <Space>!",
                                    y=350, opacity=0, alignment=pango.Alignment.CENTER)
        description.x = -description.width / 2

        container.add_child(cube, title, description)

        def announce_ready():
            pass

        graphics.chain(
            cube, {"opacity": 1,
                   "duration": 0.7, "delay": 0.3, "easing": Easing.Sine.ease_in_out},
            announce_ready, {}
        )

        container.animate(y=150, duration=0.7, delay=0.3, easing= Easing.Sine.ease_out)
        title.animate(opacity=1, y=110, duration=0.7, delay=0.5, easing= Easing.Expo.ease_out)
        description.animate(opacity=1, y=300, duration=0.5, delay=0.5, easing= Easing.Expo.ease_out)


class BasicWindow:
    def __init__(self):
        window = gtk.Window()
        window.set_default_size(600, 600)
        window.connect("delete_event", lambda *args: gtk.main_quit())

        self.scene = Scene()
        window.add(self.scene)
        window.show_all()


if __name__ == '__main__':
    window = BasicWindow()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL) # gtk3 screws up ctrl+c
    gtk.main()
