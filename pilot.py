import datetime
import os
import sys
import traceback
from pygame.locals import *
import tellopy
import av
import cv2 as cv2  # for avoidance of pylint error
import numpy
import time
import pygame
import pygame.font
import threading

global session_name
speed = 30

class FlightDataDisplay(object):
    # previous flight data value and surface to overlay
    _value = None
    _surface = None
    # function (drone, data) => new value
    # default is lambda drone,data: getattr(data, self._key)
    _update = None
    def __init__(self, key, format, colour=(255,255,255), update=None):
        self._key = key
        self._format = format
        self._colour = colour

        if update:
            self._update = update
        else:
            self._update = lambda drone,data: getattr(data, self._key)

    def update(self, drone, data):
        new_value = self._update(drone, data)
        if self._value != new_value:
            self._value = new_value
            self._surface = pygame.font.render(self._format % (new_value,), True, self._colour)
        return self._surface

def take_picture(drone, speed):
    if speed == 0:
        return
    drone.take_picture()

controls = {
    'w': 'forward',
    's': 'backward',
    'a': 'left',
    'd': 'right',
    'space': 'up',
    'left shift': 'down',
    'right shift': 'down',
    'q': 'counter_clockwise',
    'e': 'clockwise',
    # arrow keys for fast turns and altitude adjustments
    'left': lambda drone, speed: threading.Thread(target=lambda: drone.counter_clockwise(speed*2)).start(),
    'right': lambda drone, speed: threading.Thread(target=lambda: drone.clockwise(speed*2)).start(),
    'up': lambda drone, speed: threading.Thread(target=lambda: drone.up(speed*2)).start(),
    'down': lambda drone, speed: threading.Thread(target=lambda: drone.down(speed*2)).start(),
    'tab': lambda drone, speed: threading.Thread(target=lambda: drone.takeoff()).start(),
    'backspace': lambda drone, speed: threading.Thread(target=lambda: drone.land()).start(),
    'enter': threading.Thread(target=lambda: take_picture).start(),
    'return': threading.Thread(target=lambda: take_picture).start(),
}

def handleFileReceived(event, sender, data):
    global session_name
    global date_fmt
    # Create a file in ~/Pictures/ to receive image data from the drone.
    if not os.path.exists(session_name):
        os.makedirs(session_name + '/images')
        #os.makedirs('%s/images') % PICTURES_FOLDER
    path = '%s/images/tello-%s.jpeg' % (
        #os.getcwd(),
        session_name,
        datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'))
    with open(path, 'wb') as fd:
        fd.write(data)
    print('Saved photo to %s' % path)


def main():
    global session_name

    if len(sys.argv) != 2:
        print("Usage %s session_name" % sys.argv[0])
        sys.exit(1)

    session_name = sys.argv[1]

    drone = tellopy.Tello()
    pygame.init()
    screen = pygame.display.set_mode((960, 720))
    drone.subscribe(drone.EVENT_FILE_RECEIVED, handleFileReceived)

    try:
        drone.connect()
        drone.wait_for_connection(60.0)

        retry = 3
        container = None
        while container is None and 0 < retry:
            retry -= 1
            try:
                container = av.open(drone.get_video_stream())
            except av.AVError as ave:
                print(ave)
                print('retry...')

        # skip first 300 frames
        frame_skip = 300
        run_app = True

        while run_app:

            for frame in container.decode(video=0):
                try:
                    for e in pygame.event.get():
                        # WASD for movement
                        if e.type == pygame.locals.KEYDOWN:
                            print('+' + pygame.key.name(e.key))
                            keyname = pygame.key.name(e.key)
                            if keyname == 'escape':
                                drone.quit()
                                exit(0)
                            if keyname in controls:
                                key_handler = controls[keyname]
                                if type(key_handler) == str:
                                    getattr(drone, key_handler)(speed)
                                    threading.Thread(target=lambda: getattr(drone, key_handler)(speed)).start()
                                else:
                                    threading.Thread(target=lambda: key_handler(drone, speed)).start()

                        elif e.type == pygame.locals.KEYUP:
                            print('-' + pygame.key.name(e.key))
                            keyname = pygame.key.name(e.key)
                            if keyname in controls:
                                key_handler = controls[keyname]
                                if type(key_handler) == str:
                                    threading.Thread(target=lambda: getattr(drone, key_handler)(0)).start()
                                else:
                                    threading.Thread(target=lambda: key_handler(drone, 0)).start()
                    if 0 < frame_skip:
                        frame_skip = frame_skip - 1
                        continue
                    frame = numpy.array(frame.to_image())
                    frame = numpy.rot90(frame)
                    frame = numpy.flipud(frame)
                    surf = pygame.surfarray.make_surface(frame)
                    surf.blit(FlightDataDisplay('battery_percentage', 'BAT %3d%%').update(drone), (0, 0))
                    screen.fill((0,0,0))
                    screen.blit(surf, (0,0))
                    pygame.display.update()
                except:
                    screen.fill((0,0,255))
                    pygame.display.update()

            pygame.display.update()


    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(ex)
    finally:
        drone.quit()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()