# - coding: utf-8 -
# Copyright (C) 2013-2014 Toms Bauģis <toms.baugis at gmail.com>

import datetime
import datetime as dt

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk

from . import scores
from . import sprites

from .lib import graphics
from .lib import layout
from .lib import utils
from .lib.pytweener import Easing

class PauseScreen(layout.Container):
    def __init__(self, id):
        layout.Container.__init__(self, visible=False, id=id)
        box = layout.VBox(
            sprites.Label("PAUSE", size=120)
        )
        self.add_child(box)
        box.connect("on-render", self.on_render_box)

    def on_render_box(self, sprite):
        sprite.graphics.fill_area(0, 0, sprite.alloc_w, sprite.alloc_h, "#333", 0.8)


class GameOverScreen(layout.Container):
    def __init__(self, id):
        layout.Container.__init__(self, visible=False, id=id)

        self.game_over_label = sprites.Label("GAME OVER", size=90)

        self.name_input = sprites.Label("AAA", size=120, opacity=0.01)
        self.prompt = sprites.Label("_", size=120, opacity=0)
        self.name_entered = False
        self.name = ""
        self.game = None

        self.storage = scores.Storage()

        self.place_labels = layout.VBox()
        self.name_labels = layout.VBox()
        self.level_labels = layout.VBox()
        self.score_labels = layout.VBox()


        self.place_labels.add_child(sprites.Label(" ", margin_bottom=5, size=30))
        self.name_labels.add_child(sprites.Label(markup="<b>Name</b>", margin_bottom=5, size=30))
        self.level_labels.add_child(sprites.Label(markup="<b>Level</b>", margin_bottom=5, size=30))
        self.score_labels.add_child(sprites.Label(markup="<b>Score</b>", margin_bottom=5, size=30, x_align=0))

        self.score_board = layout.HBox([
            self.place_labels,
            self.name_labels,
            self.level_labels,
            self.score_labels],
            visible=False
        )


        fixed = layout.Fixed([
            self.game_over_label,
            self.name_input,
            self.prompt,
            self.score_board,
        ], fill=False)
        fixed.width = 650
        fixed.height = 600
        box = layout.Container(layout.Container(fixed, fill=False))

        self.add_child(box)
        box.connect("on-render", self.on_render_box)

    def on_render_box(self, sprite):
        sprite.graphics.fill_area(0, 0, sprite.alloc_w, sprite.alloc_h, "#333", 0.97)

    def handle_keys(self, scene, event, pressed):
        if not self.name_entered:
            if event.keyval in (gdk.KEY_BackSpace, gdk.KEY_Delete):
                self.name = self.name[:-1]
                self.move_cursor()

            elif event.keyval == gdk.KEY_Return:
                if len(self.name) == 3:
                    self.name_entered = True
                    self.show_scores()

            elif event.string:
                self.name = (self.name + event.string.upper())[:3]
                self.move_cursor()
        else:
            if event.keyval == gdk.KEY_Return:
                scene.new_game()

            elif event.keyval == gdk.KEY_Escape:
                gtk.main_quit()

    def show_scores(self):
        self.storage.save_score(self.name, self.game)

        scores = self.storage.get_scores()

        found = None
        for rec in scores:
            if (rec['score'], rec['name']) == (self.game.total_stats['score'], self.name):
                found = rec

        idx = max(0, scores.index(found) - 4) # normally show us in the middle
        idx = max(0, min(idx, len(scores)-9)) # if we are at the very bottom
        scores = scores[idx:idx+10]


        for i, score in enumerate(scores):
            color ="#eee" if score == found else "#999"

            self.place_labels.add_child(sprites.ScoreLabel("%d.", idx + i + 1, size=30, color=color))
            self.name_labels.add_child(sprites.Label(score['name'], size=30, color=color))
            self.level_labels.add_child(sprites.ScoreLabel(score=score['level'], size=30, color=color))
            self.score_labels.add_child(sprites.ScoreLabel(score=score['score'], size=30, color=color, x_align=0))


        self.prompt.stop_animation()
        self.prompt.opacity = 0
        self.name_input.animate(opacity=0)

        self.score_board.visible = True
        self.score_board.opacity = 0

        self.score_board.alloc_w = 500
        self.score_board.x = (self.score_board.parent.width - self.score_board.width) / 2
        self.score_board.y = 130
        self.score_board.animate(opacity=1)

        self.prompt.text = "<Enter> / <Escape>"
        self.prompt.size = 20
        self.prompt.y = self.score_board.y + self.score_board.height + 25
        self.prompt.x = (self.prompt.parent.width - self.prompt.width) / 2
        self.prompt.animate(opacity=1, duration=1.2, delay=2, on_complete=self.blink_prompt)


    def move_cursor(self):
        self.prompt.stop_animation()

        self.prompt.opacity = 1
        if self.name:
            self.name_input.text = self.name
        self.name_input.opacity = 1 if len(self.name) > 0 else 0

        w = self.name_input.width if self.name else 0

        if len(self.name) >= 3:
            self.prompt.size = 30
            self.prompt.text = "<Enter>"
            self.prompt.y = self.name_input.y + (self.name_input.height - self.prompt.height - 20)
        else:
            self.prompt.size = 120
            self.prompt.text = "_"
            self.prompt.y = self.name_input.y + 25

        self.prompt.x = self.name_input.x + w
        self.blink_prompt()


    def blink_prompt(self, sprite=None):
        self.prompt.animate(opacity=1 - self.prompt.opacity,
                            duration=1.2,
                            on_complete=self.blink_prompt)

    def show(self, game):
        self.name_entered = False
        self.name = ""
        self.game = game

        container = self.prompt.parent

        self.opacity = 0
        self.visible = True
        self.game_over_label.opacity = 0
        self.game_over_label.x = (container.width - self.game_over_label.width) / 2
        self.game_over_label.y = (container.height - self.game_over_label.height) / 2

        self.name_input.opacity = 0
        self.name_input.x = (container.width - self.name_input.width) / 2
        self.name_input.y = (container.height - self.name_input.height) / 2 + 50

        self.prompt.x = self.name_input.x
        self.prompt.y = self.name_input.y + 25

        self.game_over_label.animate(opacity=1, duration=1.4)
        graphics.chain(
            self, {"opacity": 1, "duration": 0.7},
            self.game_over_label, {"y": 20, "delay": 0.3, "duration": 1},
            self.blink_prompt, {},
        )




class StackedBar(graphics.Sprite):
    def __init__(self, height=150, width=500, **kwargs):
        graphics.Sprite.__init__(self, **kwargs)
        self.height = height
        self.width = width

        self.bar_container = graphics.Sprite(snap_to_pixel=False)
        self.bar_container.height = 50
        self.add_child(self.bar_container)

        self.label = sprites.Label("", color="#eee")
        self.add_child(self.label)

        self.colors = {
            "slow": "#63623F",
            "fast": "#3F5B63",
        }

        self.bar_container.connect("on_render", self.on_render)

    def on_render(self, sprite):
        sprite.graphics.rectangle(0, 0, self.width, sprite.height)
        sprite.graphics.fill("#444")


    def load(self, data):
        total = sum((rec['claimed'] for rec in data))

        h = self.bar_container.height
        w = int(self.width / 100.0 * total)

        self.bar_container.clear()

        gap = 3
        widths = utils.full_pixels(w, [rec['claimed'] for rec in data], gap)

        x = 0
        for rec_w, rec in zip(widths, data):
            self.bar_container.add_child(
                graphics.Rectangle(rec_w, h,
                                   x = x,
                                   visible=False,
                                   fill=graphics.Colors.contrast(self.colors[rec['speed']], 50))
            )
            x += rec_w + gap

        def position_label(sprite):
            areas = self.bar_container.sprites.index(sprite) + 1
            claimed = (sprite.x + sprite.width) * 100.0 / self.width

            self.label.text = "%d%% claimed\nin %d jumps" % (claimed, areas)
            self.label.y = sprite.y + sprite.height + 10

            label_w = self.label.width
            self.label.x = min(max(sprite.x + sprite.width - label_w / 2, 10),
                               self.width - label_w - 10)

        def kick(sprite=None):
            for bar in self.bar_container.sprites:
                if bar.visible is False:
                    bar.visible = True
                    bar_w = bar.width
                    color = graphics.Colors.hex(bar.fill)
                    bar.width = 0
                    bar.fill = "#fff"

                    bar.animate(width=bar_w,
                                duration=0.1 + bar_w / 500.0,
                                on_update=position_label,
                                on_complete=kick)
                    bar.animate(fill=color, duration=1.7,
                                easing=Easing.Sine.ease_out)

                    return

        # dummy for delay
        self.animate(x=0, duration=0, delay=0.7, on_complete=kick)



class LevelScreen(layout.Container):
    def __init__(self, id):
        layout.Container.__init__(self, visible=False, id=id)

        self.stats_bar = StackedBar()
        self.level_score_label = sprites.ScoreLabel(size=32, x_align=0)
        self.claimed_percent_label = sprites.ScoreLabel("%d%%", size=32, x_align=0)
        self.bonus_label = sprites.ScoreLabel("%d", size=32, x_align=0)

        self.score_rows = [
            (sprites.Label("Level score:", size=32, x_align=0), self.level_score_label),
            (sprites.Label("Claimed:", size=32, x_align=0), self.claimed_percent_label),
            (sprites.Label("Bonus over 75%:", size=32, x_align=0), self.bonus_label),
        ]

        self.box = layout.VBox(
            layout.VBox([
                self.stats_bar,
                layout.HBox([
                    layout.VBox([row[0] for row in self.score_rows]),
                    layout.VBox([row[1] for row in self.score_rows])
                ], spacing=50)
            ], fill=False)
        )
        self.add_child(self.box)
        self.box.connect("on-render", self.on_render_box)


    def display_score(self, game, callback):
        self.visible = True
        self.opacity = 0

        for i, (label, points) in enumerate(self.score_rows):
            label.opacity = 0
            points.opacity = 0

        claimed_percent = int(round(game.stats['claimed_percent']))
        extra = (claimed_percent - 75)


        def fade_in_done(on_complete):
            self.stats_bar.load(game.stats['claims'])

            self.level_score_label.score = game.stats['score']
            self.claimed_percent_label.score = claimed_percent


            for i, (label, points) in enumerate(self.score_rows):
                label.animate(delay=i*0.7, opacity=1)
                points.animate(delay=i*0.7, opacity=1)

            # dummy
            self.animate(x=0, delay=0.7*2, on_complete=on_complete)


        def add_extra(on_complete):
            #self.bonus_label.score = self.bonus_label.score + 1000

            # dummy
            self.bonus_label.animate(score=self.bonus_label.score + 1000, duration=0.1, on_complete=on_complete)


        def scores_done(on_complete):
            for level in (0, game.level):
                game.level_stats[level]['score'] += extra * 1000
            self.box.animate(opacity=0, duration=0.5, delay=2.5, on_complete=on_complete)

        def finish_level_screen():
            for level in (0, game.level):
                game.level_stats[level]['score'] += extra * 1000

            self.visible = False
            callback()


        chain = [
            self, {"opacity": 1, "duration": .8},
            fade_in_done, {},
        ]

        for i in range(extra):
            chain += [add_extra, {}]

        chain += [scores_done, {}, finish_level_screen, {}]

        graphics.chain(*chain)


    def on_render_box(self, sprite):
        sprite.graphics.fill_area(0, 0, sprite.alloc_w, sprite.alloc_h, "#333")
