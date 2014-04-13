![APX gameplay](https://farm8.staticflickr.com/7434/13823878335_e242ac1c23_o.png)


Running
=======

The game requires GTK 3.0 with python introspection installed.
Your safest bet would be to run gnome shell, or being able to
run gnome shell.

Call ./apx.py to run the game


Game description and goal
==========================

APX is a [QIX](http://en.wikipedia.org/wiki/Qix) clone with minor differences from the original in gameplay.

Use arrow keys to move around the perimeter of square, use <Space> and <Shift> 
to "cut" the area. Connect back to perimeter to "claim" the area.

Your objective is to claim 75% or more to proceed to the next level

Claiming with Shift key will be slower but give you double the points.

For every claimed full percent over 75% you get extra 1000 points.


Implementation
==============

The game was implemented using 
[hamster graphics](https://github.com/projecthamster/experiments)
and somewhat serves also as a tech demo. Check out the tutorial!
