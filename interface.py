import pygame
import pymunk
from geometry import Vec2d, FRect


class Camera:

    def __init__(self, center, size, constraint, zoom_con=None):
        self._constraint = pygame.Rect(constraint)
        self.i_size = list(size)

        if zoom_con is None:
            self.zoom_con = [None, None]
        else:
            self.zoom_con = zoom_con
        self._zoom = 1
        if self.zoom_con[0] is not None and self._zoom < self.zoom_con[0]:
            self._zoom = self.zoom_con[0]
        if self.zoom_con[1] is not None and self._zoom > self.zoom_con[1]:
            self._zoom = self.zoom_con[1]

        self.move_speed = 6
        self.zoom_speed = 2

        self.rect = FRect(0, 0, *self.i_size)
        self.rect.center = center
        self.rect.clamp_ip(self._constraint)

        self.c_rect = FRect(self.rect)

    def update(self, upd_time):
        tc, cc = self.rect.center, self.c_rect.center
        ts, cs = self.rect.size, self.c_rect.size
        dis_x, dis_y = tc[0] - cc[0], tc[1] - cc[1]
        ds_x, ds_y = ts[0] - cs[0], ts[1] - cs[1]

        if abs(ds_x) < .5:
            self.c_rect.w = ts[0]
        else:
            self.c_rect.w += ds_x * self.zoom_speed * upd_time / 1000
        if abs(ds_y) < .5:
            self.c_rect.h = ts[1]
        else:
            self.c_rect.h += ds_y * self.zoom_speed * upd_time / 1000

        if abs(dis_x) < .5:
            self.c_rect.centerx = tc[0]
        else:
            self.c_rect.centerx = cc[0] + dis_x * self.move_speed * upd_time / 1000
        if abs(dis_y) < .5:
            self.c_rect.centery = tc[1]
        else:
            self.c_rect.centery = cc[1] + dis_y * self.move_speed * upd_time / 1000
        self.c_rect.clamp_ip(self._constraint)

    def get_rect(self):
        return self.c_rect
        rect = pygame.Rect(0, 0, 0, 0)
        rect.center = self.c_rect.center
        rect.inflate_ip(self.c_rect.width // 2 * 2, self.c_rect.height // 2 * 2)
        return rect

    def move(self, shift):
        self.rect.x += shift[0]
        self.rect.y += shift[1]
        self.rect.clamp_ip(self._constraint)

    def move_smooth(self, coef):
        self.rect.x += self.c_rect.width * coef[0] / 100
        self.rect.y += self.c_rect.height * coef[1] / 100
        self.rect.clamp_ip(self._constraint)

    def get_zoom(self):
        return self._zoom

    def set_zoom(self, zoom):
        if zoom <= 0:
            return
        center = self.rect.center
        if self.zoom_con[0] is not None and zoom < self.zoom_con[0]:
            zoom = self.zoom_con[0]
        if self.zoom_con[1] is not None and zoom > self.zoom_con[1]:
            zoom = self.zoom_con[1]
        premade = [e / zoom for e in self.i_size]
        if premade[0] > self._constraint.size[0] or premade[1] > self._constraint.size[1]:
            m_ind = min((0, 1), key=lambda e: self._constraint.size[e] - premade[e])
            self.set_zoom(self.i_size[m_ind] / self._constraint.size[m_ind])
            return
        self.rect.size = premade
        self.rect.center = center
        self.rect.clamp_ip(self._constraint)
        self._zoom = zoom
    zoom = property(get_zoom, set_zoom)

    def get_current_zoom(self):
        return self.i_size[0] / self.c_rect.width

    @property
    def center(self):
        return self.rect.center

    @center.setter
    def center(self, pos):
        self.rect.center = pos

    def get_constraint(self):
        return self._constraint

    def set_constraint(self, rect):
        self._constraint = rect
        self.set_zoom(self.get_zoom())
    constraint = property(get_constraint, set_constraint)

    def get_size(self):
        return self.i_size

    def set_size(self, size):
        self.i_size = size
        self.set_zoom(self.get_zoom())
    size = property(get_size, set_size)

    def world_to_local(self, pos):
        rect = self.get_rect()
        tl = rect.topleft
        zoom = self.get_current_zoom()
        return (Vec2d(pos) - tl) * zoom


class Level:

    def __init__(self, size=None, screen_size=None):
        self.size = size if size is not None else [6000, 6000]
        self.screen_size = screen_size if screen_size is not None else [600, 600]
        self.update_rect = pygame.Rect(0, 0, *self.size)

        self.camera = Camera([300, 300], self.screen_size, self.get_rect(), [None, 4])
        self.visible = self.camera.get_rect()

        self.player = None
        self.step_time = 1
        self.space_time_coef = 1
        self.groups = []
        self.pressed = []
        self.mouse_relative_prev = Vec2d(0, 0)
        self.mouse_absolute_prev = Vec2d(0, 0)
        self.mouse_relative = Vec2d(0, 0)
        self.mouse_absolute = Vec2d(0, 0)
        self.pregenerate()

    def pregenerate(self):
        pass

    def send_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.camera.zoom /= .75
            elif event.button == 5:
                self.camera.zoom *= .75
        elif event.type == pygame.VIDEORESIZE:
            self.screen_size = event.size
            self.camera.size = event.size

    def handle_keys(self):
        pressed = self.pressed
        if pressed[pygame.K_RIGHT]:
            self.camera.move_smooth([1, 0])
        if pressed[pygame.K_LEFT]:
            self.camera.move_smooth([-1, 0])
        if pressed[pygame.K_UP]:
            self.camera.move_smooth([0, -1])
        if pressed[pygame.K_DOWN]:
            self.camera.move_smooth([0, 1])
        if self.player:
            self.player.boost((
                int(pressed[pygame.K_d]) - int(pressed[pygame.K_a]),
                int(pressed[pygame.K_s]) - int(pressed[pygame.K_w])
            ))
            self.player.rotate_to((self.mouse_absolute - self.player.pos).angle)

    def start_step(self, upd_time, time_coef=1):
        self.step_time = upd_time * time_coef
        self.pressed = pygame.key.get_pressed()
        self.mouse_relative_prev = self.mouse_relative
        self.mouse_absolute_prev = self.mouse_absolute
        self.mouse_relative = Vec2d(pygame.mouse.get_pos())
        self.mouse_absolute = self.get_mouse()

    def end_step(self):
        pass

    def update(self):
        self.camera.update(self.step_time)
        self.visible = self.camera.get_rect()
        for group in self.groups:
            group.update(self.step_time, time_coef=self.space_time_coef)

    def draw(self, surface):
        for group in self.groups:
            group.draw(surface, self.camera)

    def get_rect(self):
        return pygame.Rect(0, 0, *self.size)

    def get_mouse(self):
        ms = pygame.mouse.get_pos()
        sc, vs = self.screen_size, self.visible.size
        zoom = max((sc[0] / vs[0], sc[1] / vs[1]))
        return Vec2d(ms) / zoom + self.visible.topleft


if __name__ == '__main__':
    from main_loop import Main
    import random
    drag_sprite = None


    class TestLevel(Level):

        def pregenerate(self):
            from physics import PhysicsGroup, PhysObject
            space = pymunk.Space()
            space.gravity = [0, 1000]

            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            shape = pymunk.Segment(body, [0, self.size[1]], [self.size[0], self.size[1]], 10)
            space.add(body, shape)

            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            shape = pymunk.Segment(body, [0, 0], [0, self.size[1]], 0)
            space.add(body, shape)

            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            shape = pymunk.Segment(body, [self.size[0], 0], [self.size[0], self.size[1]], 10)
            space.add(body, shape)

            group = PhysicsGroup(space)
            from Ships.Vessel import Ship
            ship = Ship()
            ship.pos = [10, 100]
            ship.add(group)
            for n in range(20):
                size = 100
                sprite = PhysObject()
                sprite.image = pygame.Surface([size] * 2).convert_alpha()
                sprite.image.fill((0, 0, 0, 0))
                pygame.draw.circle(sprite.image, (0, 0, 255), [size // 2] * 2, size // 2)
                sprite.rect = sprite.image.get_rect()
                sprite.body = pymunk.Body()
                sprite.shape = pymunk.Circle(sprite.body, size // 2)
                sprite.shape.density = 1

                sprite.pos = [random.randint(0, self.size[0]), random.randint(0, self.size[1])]
                sprite.vel = [10, 0]
                group.add(sprite)
                sprite.shape.friction = 1
                if n == 0:
                    sprite.pos = [0, 0]
                    pygame.draw.circle(sprite.image, (0, 255, 0), [size // 2] * 2, size // 2)
                    pygame.draw.line(sprite.image, (255, 0, 0), [size // 2] * 2, [size, size // 2])
                    group.uni = sprite

            self.groups.append(group)

        def get_mouse_sprite(self):
            for s in self.groups[0].sprites():
                if s.shape.point_query(self.mouse_absolute)[0] <= 0:
                    return s
            return None

        def send_event(self, event):
            super().send_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    global drag_sprite
                    if drag_sprite is None:
                        s = self.get_mouse_sprite()
                        if s is not None:
                            drag_sprite = s
                    else:
                        drag_sprite.vel = (self.mouse_absolute - self.mouse_absolute_prev) / self.step_time * 1000
                        drag_sprite = None
                elif event.button == 2:
                    s = self.get_mouse_sprite()
                    if s is not None:
                        s.vel = [0, -500]

        def end_step(self):
            super().end_step()
            global drag_sprite
            # print(drag_sprite, self.mouse_absolute)
            if drag_sprite is not None:
                drag_sprite.pos = self.mouse_absolute
                drag_sprite.vel = [0, 0]


    main = Main()
    main.size = [800, 600]
    level = TestLevel([800, 600], [800, 600])

    main.load_level(level)
    main.start()