import pygame
import pymunk
from geometry import Vec2d, FRect
from config import *
from loading import GObject
from col_handlers import get_handler
import math


class CameraGroup(pygame.sprite.AbstractGroup):

    def __init__(self):
        super().__init__()
        self.default_layer = 9

    def layer_sorted(self):
        return sorted(self.sprites(), key=lambda e: getattr(e, 'draw_layer', self.default_layer))

    def draw(self, surface, camera):
        cam_rect = camera.get_rect()
        cam_tl = cam_rect.topleft
        zoom = camera.get_current_zoom()
        blit = surface.blit
        for sprite in self.layer_sorted():
            if sprite.rect.colliderect(cam_rect):
                s_img = sprite.read_image()
                s_size = s_img.get_size()
                tl = [int((e[1] - e[2] / 2 - e[0]) * zoom) for e in zip(cam_tl, sprite.pos, s_size)]
                self.spritedict[sprite] = blit(
                    pygame.transform.scale(s_img, [int(e * zoom) for e in s_size]), tl)
        self.lostsprites = []


class PhysicsGroup(CameraGroup):

    def __init__(self, space):
        super().__init__()
        self._space = space

    def update(self, upd_time, time_coef=1):
        sprites = self.sprites()
        for s in sprites:
            s.start_step(upd_time * time_coef)
            s.pre_update()
        self._space.step(upd_time / 1000 * time_coef)
        for s in sprites:
            s.update()
            s.end_step()

    def remove_internal(self, sprite):
        super().remove_internal(sprite)
        self._space.remove(sprite.body, sprite.shape)

    def add_internal(self, sprite):
        super().add_internal(sprite)
        sprite.space = self._space

    @property
    def space(self):
        return self._space

    @space.setter
    def space(self, space):
        for s in self.sprites():
            s.space = space
        self._space = space
        for c in COLLISION_TYPE:
            ch = get_handler(c)
            if ch:
                dh = space.add_wildcard_collision_handler(c)
                for i in ['begin', 'pre_solve', 'post_solve', 'separate']:
                    setattr(dh, i, getattr(ch, i))


class PhysObject(pygame.sprite.Sprite):

    def __init__(self):
        """
        Necessary assignment
           - rect
           - image
           - shape
        """
        super().__init__()
        self._rect = None

        self._image = None
        self._space = None
        self._body = None
        self._shape = None

        self.step_time = 1

    @property
    def space(self):
        return self._space

    @space.setter
    def space(self, space):
        if self._space is not None:
            if self.shapes:
                self._space.remove(*self.shapes)
            if self._body is not None:
                self._space.remove(self._body)
        self._space = space
        if space is not None:
            if self._body is not None:
                space.add(self._body)
            if self._shape is not None:
                space.add(self._shape)

    def own_body(self):
        return True

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, body):
        # shapes !!!
        if self._space is not None:
            if self._body is not None:
                self._space.remove(self._body)
            self._space.add(body)
        self._body = body
        if self._rect is not None:
            self._rect.center = body.position

    def local_to_world(self, pos):
        return self._body.local_to_world(pos)

    def world_to_local(self, pos):
        return self._body.world_to_local(pos)

    @property
    def mass(self):
        return self._body.mass

    @mass.setter
    def mass(self, m):
        self._body.mass = m

    @property
    def moment(self):
        return self._body.moment

    @moment.setter
    def moment(self, m):
        self._body.moment = m

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, shape):
        if shape.space:
            shape.space.remove(shape)
        if shape.body is not self._body:
            shape.body = self._body
        if self._space is not None:
            if self._shape is not None:
                self._space.remove(self._shape)
            self._space.add(shape)
        self._shape = shape

    @property
    def shapes(self):
        return self._body.shapes

    def add_shape(self, shape):
        if shape.space:
            shape.space.remove(shape)
        if shape.body is not self._body:
            shape.body = self._body
        if self._space is not None:
            self._space.add(shape)

    def remove_shape(self, shape):
        if self._space is not None:
            self._space.remove(shape)
        if shape is self._shape:
            self._shape = None
        shape.body = None

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, rect):
        self._rect = FRect(rect)
        if self._body is not None:
            self._body.position = self._rect.center

    @property
    def image(self):
        return self._image.read()

    # THIS MUST be used for drawing, not .image
    def read_image(self):
        return pygame.transform.rotate(self.image, -self.angle)

    @image.setter
    def image(self, surf):
        self._image = surf

    def handle_borders(self):
        pass

    def effect(self, obj, c_data):
        pass

    def pre_update(self):
        pass

    def update(self):
        pass

    def start_step(self, upd_time):
        self.step_time = upd_time

    def end_step(self):
        self.apply_rect()

    def apply_rect(self):
        self._rect.center = self._body.position

    def _get_pos(self):
        return self.body.position

    def _set_pos(self, p):
        self._rect.center = p
        self.body.position = p

    pos, center = property(_get_pos, _set_pos), property(_get_pos, _set_pos)

    def _get_angle(self):
        return math.degrees(self.body.angle)

    def _set_angle(self, ang):
        self._body.angle = math.radians(ang)

    ang, angle = property(_get_angle, _set_angle), property(_get_angle, _set_angle)

    def _get_velocity(self):
        return self._body.velocity

    def _set_velocity(self, vel):
        self._body.velocity = (vel[0], vel[1])

    vel, velocity = property(_get_velocity, _set_velocity), property(_get_velocity, _set_velocity)

    def kill(self):
        space = self._space
        if space is not None:
            if self.shapes:
                space.remove(*self.shapes)
            if self._body is not None:
                space.remove(self._body)
            self._space = None
        self._shape = None
        self._body = None
        super().kill()