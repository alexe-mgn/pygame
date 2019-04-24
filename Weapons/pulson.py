import pymunk
from geometry import Vec2d
from loading import load_model, cast_model, load_sound
from game_class import BaseWeapon
from config import *
import math

NAME = __name__.split('.')[-1]
MODEL = load_model('Weapons\\Models\\%s' % (NAME,))

CS = Vec2d(24, 30)


class Weapon(BaseWeapon):
    size_inc = 1
    max_health = 50
    fire_delay = 2000
    proj_velocity = 1100
    sound = {
        'fire': [load_sound('Weapons\\Models\\boing_x', ext='wav'), {'channel': CHANNEL.PULSON_WEAPON}]
    }

    def __init__(self):
        super().__init__()

        self.i_body = pymunk.Body()
        self.shape = pymunk.Circle(self.body, self.RADIUS, self.image_to_local((48, 30)))
        self.shape.density = 1

    def force_fire(self, **kwargs):
        self.play_sound('fire')
        proj = self.spawn_proj()
        ang = self.miss_angle()
        rad = math.radians(ang)
        if 'target' in kwargs.keys():
            dis = (proj.pos - kwargs['target']).length
            dmp = self.Projectile.damping
            vel = (2 * dis * dmp) / (math.e ** (-dmp * self.Projectile.lifetime) + 1)
            if vel > self.proj_velocity:
                vel = self.proj_velocity
        else:
            vel = self.proj_velocity
        vec = Vec2d(vel * math.cos(rad), vel * math.sin(rad))
        proj.velocity = vec
        proj.angle = ang

    @classmethod
    def init_class(cls):
        cls._frames, cls.IMAGE_SHIFT = cast_model(MODEL, CS, cls.size_inc)
        cls.precalculate_shape()
        cls.calculate_poly_shape()
        from Projectiles.pulson import Projectile
        cls.Projectile = Projectile
        cls.fire_pos = cls.image_to_local((64, 30))

    @classmethod
    def precalculate_shape(cls):
        radius = 40

        cls.RADIUS = radius * cls.size_inc

    @classmethod
    def calculate_poly_shape(cls):
        img_poly_left = []
        poly_left = [tuple(e[n] - CS[n] for n in range(2)) for e in img_poly_left]
        poly_right = [(e[0], -e[1]) for e in poly_left[::-1]]
        cls.POLY_SHAPE = [(e[0] * cls.size_inc, e[1] * cls.size_inc) for e in poly_left + poly_right]


Weapon.init_class()