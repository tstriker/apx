#!/usr/bin/env python
# - coding: utf-8 -
# Copyright (C) 2014 Toms Bauģis <toms.baugis at gmail.com>
import datetime as dt
import sqlite3 as sqlite

class Storage(object):
    def __init__(self):
        self._con = None

    def get_scores(self):
        scores = self.fetch("""select date, name, level, score, duration from scores
                             order by score desc;
                            """)
        return [dict(zip(("date", "name", "level", "score", "duration"), row)) for row in scores]


    def save_score(self, player_name, game):
        """saves game's score, vague but effective"""
        stats = game.total_stats
        duration = int(stats['duration'].total_seconds())

        self.execute("""insert into scores(date, name, level, score, duration)
                                    values(?, ?, ?, ?, ?)""",
                     (dt.datetime.now(),
                      player_name, game.level, stats['score'], duration))


    """ Here be dragons (lame connection/cursor wrappers) """
    @property
    def connection(self):
        if self._con is None:
            self._con = sqlite.connect("apx.sqlite",
                                       detect_types=sqlite.PARSE_DECLTYPES|sqlite.PARSE_COLNAMES)
            self._con.row_factory = sqlite.Row
            self.run_fixtures()
        return self._con

    def fetch(self, query, params = None):
        con = self.connection
        cur = con.cursor()

        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)

        res = cur.fetchall()
        cur.close()

        return res

    def fetch_one(self, query, params = None):
        res = self.fetchall(query, params)
        if res:
            return res[0]
        else:
            return None

    def execute(self, statement, params = ()):
        """
        execute sql statement. optionally you can give multiple statements
        to save on cursor creation and closure
        """
        con = self.connection
        cur = con.cursor()

        if isinstance(statement, list) == False: # we expect to receive instructions in list
            statement = [statement]
            params = [params]

        for state, param in zip(statement, params):
            cur.execute(state, param)

        con.commit()
        cur.close()

    def run_fixtures(self):
        self.execute("create table if not exists scores(date, name, level, score, duration)");
