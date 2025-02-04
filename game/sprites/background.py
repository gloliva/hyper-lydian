"""
This module defines all the sprites that are:
    1) in the background (stars)
    2) appear in menus (blackhole, destroyed notes, notes, destroyed ship)
    3) are collectible (notes)
    4) or are used in special events (notes, letters)

These objects are tied together in that they are not character sprites nor projectiles; they are
the additional sprites that set the background.

Author: Gregg Oliva
"""

# stdlib imports
from math import sqrt
from random import (
    randint,
    uniform,
    choice as randelem,
    choices as weightedelem
)
from typing import Optional, List, Tuple

# 3rd-party imports
import pygame as pg

# project imports
from sprites.base import construct_asset_full_path
from stats import stat_tracker


class Background(pg.sprite.Sprite):
    """
    Basic background base class that defines minimal functionality that is shared across all
    background sprites, such as an update function and a rotate function.
    """
    DRAW_LAYER = 0
    ROTATION_AMOUNT = 1

    def __init__(self) -> None:
        super().__init__()

        self.current_rotation = 0
        self._layer = self.DRAW_LAYER

    def update(self, screen_rect: pg.Rect):
        """Basic update function that moves the background sprite across the screen"""
        self.rect.move_ip(0, 2)
        if self.rect.top > screen_rect.height:
            self.kill()

    def rotate(self, rotation_angle: int):
        """
        Rotate the sprite's image. The current image in the animation needs to be rotated,
        a new sprite mask needs to be created, and then the rect needs to be re-centered.
        """
        curr_alpha = self.surf.get_alpha()
        self.current_rotation = rotation_angle % 360

        self.surf = pg.transform.rotate(self.image, self.current_rotation + rotation_angle)

        # make sure alpha value is the same
        if curr_alpha is not None:
            self.surf.set_alpha(curr_alpha)

        # make sure image retains its previous center
        current_image_center = self.rect.center
        self.rect = self.surf.get_rect()
        self.rect.center = current_image_center

        if hasattr(self, 'mask'):
            self.mask = pg.mask.from_surface(self.surf)


class Note(Background):
    """Note object that appears in the MAIN MENU and is a collectible during the gameplay loop"""
    SCORE = 1
    NUM_NOTES_PER_EVENT = 2
    NUM_NOTES_PER_MENU_EVENT = 10
    NUM_ON_LOAD = 60
    NUM_VARIANTS = 6
    DRAW_LAYER = 1
    MENU_SPAWN_SIDE = ['left', 'top', 'right', 'bottom']
    GAMEPLAY_SPAWN_SIDE = ['left', 'top', 'right']
    NUM_MOVEMENT_POINTS = 20
    ALPHA_BOUNDS = [100, 200]
    SCALE_BOUNDS = [0.15, 1]
    SPEED_MAX = 4
    SCALE_MIN = 0.2
    SCALE_MAX = 0.5

    @staticmethod
    def interpolate_between_points(start: pg.Rect, end: pg.Rect, num_points: int) -> List[Tuple[int, int]]:
        step_x = (end.centerx - start.centerx) / (num_points - 1)
        step_y = (end.centery - start.centery) / (num_points - 1)

        # Generate the list of equidistant points
        equidistant_points = [
            (start.centerx + curr_step * step_x, start.centery + curr_step * step_y)
            for curr_step in range(num_points)
        ]

        return equidistant_points

    @staticmethod
    def interpolate_between_values(start: float, end: float, num_points) -> List[float]:
        step = (end - start) / (num_points - 1)

        equidistant_values = [
            start + curr_step * step
            for curr_step in range(num_points)
        ]

        return equidistant_values

    def __init__(self, screen_rect: pg.Rect, on_load: bool = False, in_menu: bool = False) -> None:
        super().__init__()
        note_type = randint(0, self.NUM_VARIANTS - 1)
        note = 'white_note_{0}'.format(note_type) if in_menu else 'gold_note_{0}'.format(note_type)
        image_file = construct_asset_full_path(f"backgrounds/notes/{note}.png")
        self.image = pg.image.load(image_file).convert_alpha()

        # Initial rotation
        image_scale = 0
        self.image = pg.transform.rotate(self.image, randint(0, 359))
        if not in_menu:
            image_scale = uniform(self.SCALE_MIN, self.SCALE_MAX)
            self.image = pg.transform.scale_by(self.image, image_scale)

        # Save image to reference when rotating / scaling
        self.surf = self.image

        # Set note color if in menu
        if in_menu:
            color_image = pg.Surface(self.surf.get_size()).convert_alpha()
            color_image.fill((randint(0, 255), randint(0, 255), randint(0, 255), randint(180, 255)))
            self.surf.blit(color_image, (0,0), special_flags=pg.BLEND_RGBA_MULT)

        # Spawn randomly across the screen
        if on_load:
            self.rect = self.surf.get_rect(
                center=(
                    randint(1, screen_rect.width - 1),
                    randint(1, screen_rect.height - 1),
                )
            )
        # Spawn along the edges of the screen
        elif in_menu:
            spawn_side = randelem(self.MENU_SPAWN_SIDE)
            if spawn_side == 'left':
                x, y = 20, randint(20, screen_rect.height - 20)
            elif spawn_side == 'top':
                x, y = randint(20, screen_rect.width - 20), 20
            elif spawn_side == 'right':
                x, y = screen_rect.width - 20, randint(20, screen_rect.height - 20)
            else:
                x, y = randint(20, screen_rect.width - 20), screen_rect.height - 20

            self.rect = self.surf.get_rect(
                center=(x, y)
            )
        # Spawn outside the screen
        else:
            spawn_side = randelem(self.GAMEPLAY_SPAWN_SIDE)
            if spawn_side == 'left':
                x, y = randint(-100, -20), randint(-100, -20),
                self.direction = 'right'
            elif spawn_side == 'top':
                x, y = randint(20, screen_rect.width - 20), randint(-100, -20)
                self.direction = 'bottom'
            else:
                x, y = randint(screen_rect.width + 20, screen_rect.width + 100), randint(-100, -20)
                self.direction = 'left'

            self.rect = self.surf.get_rect(
                center=(x, y)
            )

        # Gameplayer parameters
        self.movement_vector = [0, 0]
        self.rotation_amount = uniform(0.1, 1.5) * randelem([1, -1])
        if not on_load and not in_menu:
            if self.direction == 'left':
                self.movement_vector = (randint(1, self.SPEED_MAX), randint(1, self.SPEED_MAX))
            elif self.direction == 'right':
                self.movement_vector = (randint(-self.SPEED_MAX, -1), randint(1, self.SPEED_MAX))
            else:
                self.movement_vector = (randint(-self.SPEED_MAX, self.SPEED_MAX), randint(1, self.SPEED_MAX))

        speed = sqrt(self.movement_vector[0]**2 + self.movement_vector[1]**2)
        self.score = int(speed) + int((1 - image_scale) * 10)

        # Menu animation parameters
        self.movement_counter = 0
        self.spawn_center = self.rect
        alpha_values = self.interpolate_between_values(
            self.ALPHA_BOUNDS[0], self.ALPHA_BOUNDS[1], self.NUM_MOVEMENT_POINTS
        )
        scale_values = self.interpolate_between_values(
            self.SCALE_BOUNDS[0], self.SCALE_BOUNDS[1], self.NUM_MOVEMENT_POINTS
        )

        self.alpha_values = alpha_values[::-1]
        self.scale_values = scale_values[::-1]

        # Additional note values
        self.spawn_time = pg.time.get_ticks()

        if not in_menu and not on_load:
            stat_tracker.notes__total += 1

    def update(
            self,
            screen_rect: pg.Rect,
            in_menu: bool = False,
            blackhole_rect: Optional[pg.Rect] = None
        ) -> None:
        if in_menu:
            if self.movement_counter < self.NUM_MOVEMENT_POINTS - 1:
                self.move_in_menu(blackhole_rect)
                self.rotate(self.current_rotation + self.ROTATION_AMOUNT)
                self.fade_out()
                self.movement_counter += 1
            else:
                self.kill()
        else:
            self.move_in_game(screen_rect)
            self.rotate(self.current_rotation + self.rotation_amount)
            super().update(screen_rect)

    def move_in_game(self, screen_rect: pg.Rect) -> None:
        self.rect.move_ip(*self.movement_vector)

        if self.rect.top > screen_rect.height:
            self.kill()

    def move_in_menu(self, blackhole_rect: pg.Rect) -> None:
        path = self.interpolate_between_points(self.spawn_center, blackhole_rect, self.NUM_MOVEMENT_POINTS)
        self.rect.center = path[self.movement_counter]

    def fade_out(self) -> None:
        alpha_value = self.alpha_values[self.movement_counter]
        scale_value = self.scale_values[self.movement_counter]
        prev_center = self.rect.center
        self.surf = pg.transform.scale_by(self.image, scale_value)
        self.surf.set_alpha(alpha_value)
        self.rect = self.surf.get_rect(center=prev_center)

    def kill(self) -> None:
        if stat_tracker.control__game_init.value == 1:
            current_time = pg.time.get_ticks()
            stat_tracker.notes__time__lifespan.add(current_time - self.spawn_time)
        super().kill()


class BrokenNote(Background):
    """Broken Notes that bounce around the screen during the DEATH MENU screen"""
    NUM_ON_LOAD = 80
    NUM_VARIANTS = 12
    DIRECTION = ['left', 'top', 'right', 'bottom']
    FRAME_THRESHOLD = 360
    DRAW_LAYER = 1

    def __init__(self, screen_rect: pg.Rect) -> None:
        super().__init__()
        note_type = randint(0, self.NUM_VARIANTS - 1)
        image_file = construct_asset_full_path(f"backgrounds/notes/broken_note_{note_type}.png")
        image = pg.image.load(image_file).convert_alpha()
        self.image = pg.transform.scale_by(pg.transform.rotate(image, randint(0, 359)), uniform(0.05, 0.4))
        self.surf = self.image
        self.surf.set_alpha(randint(100, 240))

        self.rect = self.surf.get_rect(
            center=(
                randint(1, screen_rect.width - 1),
                randint(1, screen_rect.height - 1),
            )
        )

        # Movement parameters
        self.prev_x = 0
        self.prev_y = 0
        self.frame_counter = 0
        self.direction = randelem(self.DIRECTION)
        self.rotation_amount = uniform(0.1, 1.5) * randelem([1, -1])

    def update(self, screen_rect: pg.Rect, fade_out: bool = False, alpha: int = 255) -> None:
        if fade_out:
            self.surf.set_alpha(alpha)

        self.drift(screen_rect)
        self.rotate(self.current_rotation + self.rotation_amount)

    def drift(self, screen_rect: pg.Rect) -> None:
        should_update = (self.frame_counter % self.FRAME_THRESHOLD) == 0

        if self.direction == 'left':
            x, y = -1, randint(0, 1) if should_update else self.prev_y
        elif self.direction == 'right':
            x, y = 1, randint(-1, 0) if should_update else self.prev_y
        elif self.direction == "top":
            x, y = randint(-1, 0) if should_update else self.prev_x, -1
        else:
            x, y = randint(0, 1) if should_update else self.prev_x, 1
        self.rect.move_ip(x, y)

        self.prev_x, self.prev_y = x, y
        self.frame_counter += 1

        # don't move out of bounds
        if self.rect.left < -10:
            self.rect.left = -10
            self.direction = 'right'
            self.rotation_amount *= -1
        if self.rect.right > screen_rect.width + 20:
            self.rect.right = screen_rect.width + 20
            self.direction = 'left'
            self.rotation_amount *= -1
        if self.rect.top <= -10:
            self.rect.top = -10
            self.direction = 'bottom'
            self.rotation_amount *= -1
        if self.rect.bottom > screen_rect.height + 20:
            self.rect.bottom = screen_rect.height + 20
            self.direction = 'top'
            self.rotation_amount *= -1


class Star(Background):
    """Background stars that move and twinkle in the sky"""
    NUM_ON_LOAD = 800
    NUM_STARS_PER_EVENT = 2
    DRAW_LAYER = 0
    STAR_TYPES = ['star_tiny', 'star_small']
    ALPHA_VALUES = [50, 50, 50, 50, 100, 150, 200, 255, 200, 100]
    STAR_COLORS = ['white', 'red', 'yellow', 'blue', 'orange']
    STAR_WEIGHTS = [40, 1, 10, 1, 5]

    def __init__(self, screen_rect: pg.Rect, on_load: bool = False) -> None:
        super().__init__()
        star_type = randelem(self.STAR_TYPES)
        star_color = weightedelem(self.STAR_COLORS, weights=self.STAR_WEIGHTS)[0]
        image_file = construct_asset_full_path(f"backgrounds/stars/{star_type}.png")
        image = pg.image.load(image_file).convert_alpha()
        self.image = pg.transform.scale_by(pg.transform.rotate(image, randint(0, 359)), uniform(0.05, 0.4))
        self.surf = self.image

        # Set star color
        if star_color != 'white':
            color_image = pg.Surface(self.surf.get_size()).convert_alpha()
            color_image.fill(star_color)
            self.surf.blit(color_image, (0,0), special_flags=pg.BLEND_RGBA_MULT)

        # Set star rect
        if on_load:
            self.rect = self.surf.get_rect(
                center=(
                    randint(1, screen_rect.width - 1),
                    randint(-100, screen_rect.height - 1),
                )
            )
        else:
            self.rect = self.surf.get_rect(
                center=(
                    randint(1, screen_rect.width - 1),
                    -100,
                )
            )

        # star attributes
        self.curr_alpha_id = 0
        self.num_alpha_values = len(self.ALPHA_VALUES)
        self.twinkle_increment = uniform(0.1, 0.5)

    def update(self, screen_rect: pg.Rect, in_menu: bool = False):
        self.show_twinkle_animation()
        if not in_menu:
            super().update(screen_rect)

    def show_twinkle_animation(self) -> None:
        self.curr_alpha_id = (self.curr_alpha_id + self.twinkle_increment) % self.num_alpha_values
        alpha_id = int(self.curr_alpha_id)
        alpha_value = self.ALPHA_VALUES[alpha_id]
        self.surf.set_alpha(alpha_value)


class Letter(Background):
    """Letter sprites that spawn during a LetterField Special Event"""
    # Image
    NUM_VARIANTS = 7
    DRAW_LAYER = 3

    # Gameplay
    DAMAGE = 1

    # Spawn
    SPAWN_SIDE = ['left', 'top', 'right', 'bottom']

    # Movement
    SPEED_MAX = 6
    OPPOSITE_MOVEMENT = {
        'top': 'bottom',
        'bottom': 'top',
        'left': 'right',
        'right': 'left',
    }

    # Animation
    FADE_INCREMENT = 0.2
    ALPHA_VALUES = [255, 232, 200, 182, 150, 122, 100, 73, 50, 22, 1]

    def __init__(self, screen_rect: pg.Rect) -> None:
        super().__init__()
        letter_type = randint(0, self.NUM_VARIANTS - 1)
        image_file = construct_asset_full_path(f"backgrounds/letters/letter_{letter_type}.png")
        image = pg.image.load(image_file).convert_alpha()
        self.image_scale = uniform(0.4, 1.)
        self.image = pg.transform.scale_by(pg.transform.rotate(image, randint(0, 359)), self.image_scale)
        self.surf = self.image

        # Spawn outside of the screen
        spawn_side = randelem(self.SPAWN_SIDE)
        if spawn_side == 'left':
            x, y = randint(-100, -20), randint(-100, -20),
            self.direction = 'right'
        elif spawn_side == 'top':
            x, y = randint(20, screen_rect.width - 20), randint(-100, -20)
            self.direction = 'bottom'
        elif spawn_side == 'right':
            x, y = randint(screen_rect.width + 20, screen_rect.width + 100), randint(-100, -20)
            self.direction = 'left'
        else:
            x, y = randint(20, screen_rect.width - 20), randint(screen_rect.height + 20, screen_rect.height + 100)
            self.direction = 'top'

        self.rect = self.surf.get_rect(
            center=(x, y)
        )

        self.rotation_amount = uniform(0.1, 0.8) * randelem([1, -1])
        self.set_movement_vector()

        # gameplay parameters
        self.damage = self.DAMAGE
        self.overlapping_letters = set()

        # Animation parameters
        self.show_fade_out = False
        self.curr_alpha_id = 0
        self.num_alpha_values = len(self.ALPHA_VALUES)

        # Sprite mask
        self.mask = pg.mask.from_surface(self.surf)

    def reverse_rotation(self) -> None:
        self.rotation_amount *= -1

    def set_movement_vector(self) -> None:
        if self.direction == 'left':
            self.movement_vector = (randint(1, self.SPEED_MAX), randint(-self.SPEED_MAX, self.SPEED_MAX))
        elif self.direction == 'top':
            self.movement_vector = (randint(-self.SPEED_MAX, self.SPEED_MAX), randint(-self.SPEED_MAX, -1))
        elif self.direction == 'right':
            self.movement_vector = (randint(-self.SPEED_MAX, -1), randint(-self.SPEED_MAX, self.SPEED_MAX))
        else:
            self.movement_vector = (randint(-self.SPEED_MAX, self.SPEED_MAX), randint(1, self.SPEED_MAX))

    def reverse_direction(self, collision_letter: "Letter") -> None:
        collision_image_scale = collision_letter.image_scale
        similar_size = abs(self.image_scale - collision_image_scale) < 0.5
        self_is_smaller = self.image_scale < collision_image_scale

        x, y = self.movement_vector

        if similar_size or (self_is_smaller):
            x *= -1
            y *= -1

        # If image sizes are within 0.5, come to near stop in opposite direction
        # Otherwise, the larger image loses momentum and the smaller image gains momentum
        if similar_size:
            if x != 0:
                x = 1 if x > 0 else -1
            if y != 0:
                y = 1 if y > 0 else -1
        else:
            momentum = 1 if not self_is_smaller else -1

            if x < 0:
                x += (1 * momentum)
            else:
                x -= (1 * momentum)

            if y < 0:
                y += (1 * momentum)
            else:
                y -= (1 * momentum)

            speed = sqrt(x**2 + y**2)
            if speed == 0 and self_is_smaller:
                if self.direction == 'left':
                    x -= randint(0, 1)
                elif self.direction == 'top':
                    y -= randint(0, 1)
                elif self.direction == 'right':
                    x += randint(0, 1)
                else:
                    y += randint(0, 1)

        self.movement_vector = [x, y]

    def change_movement_on_collision(self, letter: "Letter") -> None:
        self.direction = self.OPPOSITE_MOVEMENT[self.direction]

        if letter not in self.overlapping_letters:
            self.reverse_direction(letter)
            self.reverse_rotation()
            self.overlapping_letters.add(letter)

    def update(self, screen_rect: pg.Rect):
        for letter in self.overlapping_letters.copy():
            if not pg.sprite.collide_circle(self, letter):
                self.overlapping_letters.remove(letter)

        if self.show_fade_out:
            self.fade_out()

        self.move(screen_rect)
        self.rotate(self.current_rotation + self.rotation_amount)

    def move(self, screen_rect: pg.Rect) -> None:
        self.rect.move_ip(*self.movement_vector)

        # Check to see if moved offscreen
        if self.direction == 'bottom' and \
            (self.rect.top > screen_rect.height or
             self.rect.left > screen_rect.width or
             self.rect.right < 0
            ):
            self.kill()
        elif self.direction == 'top' and \
            (self.rect.bottom < 0 or
             self.rect.left > screen_rect.width or
             self.rect.right < 0
            ):
            self.kill()
        elif self.direction == 'left' and \
            (self.rect.right < 0 or
             self.rect.top > screen_rect.height or
             self.rect.bottom < 0 or self.rect.left
            ):
            self.kill()
        elif self.direction == 'right' and \
            (self.rect.left > screen_rect.width or
             self.rect.top > screen_rect.height or
             self.rect.bottom < 0 or self.rect.left
            ):
            self.kill()

    def enable_fade_out(self) -> None:
        self.show_fade_out = True

    def fade_out(self) -> None:
        self.curr_alpha_id = (self.curr_alpha_id + self.FADE_INCREMENT)

        if self.curr_alpha_id >= self.num_alpha_values:
            self.kill()
            return

        alpha_id = int(self.curr_alpha_id)
        alpha_value = self.ALPHA_VALUES[alpha_id]
        self.surf.set_alpha(alpha_value)


class BlackHole(Background):
    """Blackhole image that shows up in the MAIN MENU screen"""
    ROTATION_AMOUNT = 4
    MOVEMENT_VALUES = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    MOVEMENT_INCREMENT = 0.05
    DRAW_LAYER = 1

    def __init__(self, screen_rect: pg.Rect) -> None:
        super().__init__()
        image_file = construct_asset_full_path(f"backgrounds/black_hole.png")
        self.image = pg.transform.scale_by(pg.image.load(image_file).convert_alpha(), 4)
        self.surf = self.image
        self.rect = self.surf.get_rect(center=(screen_rect.centerx, screen_rect.centery + 150))
        self.surf.set_alpha(150)

        # Animation Values
        self.movement_id = 0
        self.num_movement_values = len(self.MOVEMENT_VALUES)
        self.current_rotation = 0

    def update(self, screen_rect: pg.Rect, in_menu: bool = False):
        self.rotate(self.current_rotation - self.ROTATION_AMOUNT)
        if in_menu:
            self.move_in_menu()
        else:
            super().update(screen_rect)

    def move_in_menu(self) -> None:
        self.movement_id = (self.movement_id + self.MOVEMENT_INCREMENT) % self.num_movement_values
        move_id = int(self.movement_id)
        x, y = self.MOVEMENT_VALUES[move_id]
        self.rect.move_ip(x, y)


class DestroyedShip(Background):
    """Destroyed Player ship image that shows up in the DEATH MENU screen"""
    ROTATION_AMOUNT = 0.1
    DRAW_LAYER = 3

    def __init__(self, screen_rect: pg.Rect) -> None:
        super().__init__()
        image_file = construct_asset_full_path(f"spaceships/player/destroyed_player_ship.png")
        image = pg.image.load(image_file).convert_alpha()
        self.image = pg.transform.scale_by(image, 5)
        self.surf = self.image

        self.rect = self.surf.get_rect(
            center=(300, screen_rect.height - 200)
        )

    def update(self, _: pg.Rect):
        self.rotate(self.current_rotation + self.ROTATION_AMOUNT)
