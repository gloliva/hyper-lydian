# stdlib imports
import asyncio
from subprocess import Popen

# 3rd-party imports
import pygame as pg
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher

# project imports
from defs import (
    ADDRESS,
    INCOMING_PORT,
    GameState,
    MAX_APPLICATION_PATH,
    FPS,
)
from debug import DISABLE_OPENING_MAX_APPLICATION
from sprites.base import construct_asset_full_path


# Max MSP Application
MAX_APP = None
MAX_OPEN = False
MAX_FULLY_LOADED = False

MAX_OPENED_ADDRESS = '/max_opened'
MAX_LOADED_ADDRESS = '/max_loaded'

MAXIMUM_LOADTIME = 30

LOADING_STR = 'LOADING'
MAX_OPEN_STR = 'Opening Max/MSP'
MAX_LOAD_STR = 'Starting Music'
LOADING_DOT_STR = '.'
PERCENT_LOADED_STR = '{percent}%% Loaded'


def loading_screen(game_clock: pg.time.Clock, main_screen: pg.Surface) -> None:
    asyncio.run(open_max_application(game_clock, main_screen))
    return GameState.MAIN_MENU


def max_loaded_handler(address, *args):
    global MAX_FULLY_LOADED
    MAX_FULLY_LOADED = True


def max_opened_handler(address, *args):
    global MAX_OPEN
    MAX_OPEN = True


async def open_max_application(game_clock: pg.time.Clock, main_screen: pg.Surface):
    global MAX_APP

    if DISABLE_OPENING_MAX_APPLICATION:
        return

    # Set up OSC Server
    dispatcher = Dispatcher()
    dispatcher.map(MAX_OPENED_ADDRESS, max_opened_handler)
    dispatcher.map(MAX_LOADED_ADDRESS, max_loaded_handler)
    server = AsyncIOOSCUDPServer((ADDRESS, INCOMING_PORT), dispatcher, asyncio.get_event_loop())
    transport, _ = await server.create_serve_endpoint()

    # Open Max application
    args = ['open', MAX_APPLICATION_PATH]
    MAX_APP = Popen(args)

    # show studio logo
    show_studio_logo_screen(game_clock, main_screen)

    # Update load screen and wait for Max to finish loading
    await wait_for_max_to_load()

    transport.close()


def show_studio_logo_screen(game_clock: pg.time.Clock, main_screen: pg.Surface):
    screen_rect = main_screen.get_rect()
    studio_logo = StudioLogo(screen_rect, screen_rect.height)
    alpha_value = 255
    screentime = 0

    while screentime < 6:
        # draw background
        main_screen.fill("black")

        # draw studio logo
        if screentime < 2:
            alpha_value = int((screentime / 2.0) * 255)
            alpha_value = max(0, min(255, alpha_value))
        elif screentime > 4:
            alpha_value = int((2 - (6 - screentime)) * 255)
            alpha_value = 255 - (max(0, min(255, alpha_value)))

        studio_logo.surf.set_alpha(alpha_value)
        main_screen.blit(studio_logo.surf, studio_logo.rect)

        # render screen
        pg.display.flip()

        # lock FPS
        screentime += game_clock.tick(FPS) / 1000


async def wait_for_max_to_load():
    elapsed_load_time = 0

    # Update load screen while waiting for Max
    while not MAX_OPEN:
        loading_dot_str = LOADING_DOT_STR * ((elapsed_load_time % 3) + 1)
        print(f'Waiting for Max to open{loading_dot_str}')
        elapsed_load_time += 1
        await asyncio.sleep(1)
    while not MAX_FULLY_LOADED:
        loading_dot_str = LOADING_DOT_STR * ((elapsed_load_time % 3) + 1)
        print(f'Waiting for Max to load{loading_dot_str}')
        elapsed_load_time += 1
        await asyncio.sleep(1)

    print('Max has finished loading')
    await asyncio.sleep(1)


class StudioLogo(pg.sprite.Sprite):
    def __init__(self, screen_rect: pg.Rect, scale_resolution: int) -> None:
        super().__init__()
        image_file = construct_asset_full_path('logo/hello_drama_studios.png')
        image = pg.image.load(image_file).convert()
        self.surf = pg.transform.scale(image, (scale_resolution, scale_resolution))
        self.rect = self.surf.get_rect(
            center=screen_rect.center
        )