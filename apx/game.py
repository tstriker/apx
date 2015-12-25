# - coding: utf-8 -
# Copyright (C) 2013-2014 Toms Bauģis <toms.baugis at gmail.com>

import datetime as dt

from gi.repository import GObject as gobject
from .lib import game_utils
from collections import defaultdict

class Game(gobject.GObject):
    """all of the game logic, so it doesn't mix with presentation"""
    __gsignals__ = {
        "on-area-claimed": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    def __init__(self):
        gobject.GObject.__init__(self)

        maxx, maxy = 600, 500
        self.start_poly = [(0, 0), (maxx, 0), (maxx, maxy), (0, maxy), (0, 0)]
        self._total_area = game_utils.total_area([self.start_poly])

        self.level = 1
        self.level_stats = defaultdict(lambda: defaultdict(int))

        self.speed = 1 #: current game speed

        self.paused = False #: paused by player
        self.claiming = False #: currently trying to claim new teritory
        self.immortal = False #: you cheat!
        self._prev_claim_time = dt.datetime.now()

        self.lives = 3


    def next_level(self):
        self.level += 1
        self._prev_claim_time = dt.datetime.now()
        self.speed = 1 + self.level * 0.03

    @property
    def claimed_enough(self):
        """tells if we have claimed enough area for the next level"""
        if self.stats['claimed_percent'] > 75:
            return True
        else:
            return False


    def update_score(self, claimed_area, speed):
        """
            1000 points per level
            3x points for going slow
            claimed is in range 0..1, so we multiply by 1000 to get points
        """
        claimed = claimed_area * 100.0 / self._total_area
        score = int(claimed * 100) # 100 points per percent
        score *= 3 if speed == "slow" else 1

        now = dt.datetime.now()
        for level in (0, self.level):
            # 0 level is our totals (how uncanny!)
            stats = self.level_stats[level]
            stats['score'] += score
            stats['claimed_area'] += claimed_area
            stats['claimed_percent'] =  stats['claimed_area'] * 100.0 / self._total_area

            stats['duration'] = stats['duration'] or dt.timedelta()
            stats['duration'] += (now - self._prev_claim_time)

            stats['claims'] = stats['claims'] or []
            stats['claims'].append({"claimed": claimed,
                                    "speed": speed,
                                    "time": dt.datetime.now() - self._prev_claim_time})

        self._prev_claim_time = now

        # extra lives on 100k and then on every next 50k as life gets harder
        extra_lives = [100000 + 50000 * i for i in range (10)]
        for live_score in extra_lives:
            if self.level_stats[0]['score'] >= live_score and \
               self.level_stats[0]['score'] - score < live_score:
                self.lives += 1

        self.emit("on-area-claimed", claimed)

    def die(self):
        self.lives -= 1

    @property
    def stats(self):
        stats = self.level_stats[self.level]
        stats.update({
            "qix": min(3, int(round(0.8 + self.level * 0.33))), # no more than 3 quix
            "sparks": int(round(1 + self.level * 0.6)),
        })
        return stats

    @property
    def total_stats(self):
        return self.level_stats[0]
