from arena import *
import random

arena = Arena(host="arena.andrew.cmu.edu", realm="realm", scene="example")

@arena.run_once
def main():
    def click(evt):
        if evt.type == "mousedown":
            start = evt.data.clickPos
            end = evt.data.position
            line = ThickLine(path=(start, end), color=(random.randint(0,255), random.randint(0,255), random.randint(0,255)), lineWidth=5)
            arena.add_object(line)

    box = Box(object_id="my_box", color=(255,0,0), position=Position(0,2,0), click_listener=True, evt_handler=click)
    arena.add_object(box)

arena.run_tasks()
