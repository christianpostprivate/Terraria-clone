import pygame as pg

import settings as st
import functions as fn


vec = pg.math.Vector2
GRAVITY = vec(0, 1)
NULL = vec(0, 0)


class Physics_object(pg.sprite.Sprite):
    '''
    parent sprite for all sprites that experience physics
    '''
    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.pos = vec(0, 0)
        self.acc = vec(0, 0)
        self.vel = vec(0, 0)
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos
        
        self.speed = 0.5
        self.friction = -0.12
        self.gravity = vec(GRAVITY)
        
        
    def update(self, others):        
        self.acc += self.gravity

        self.vel += 0.5 * self.acc
        # cap falling speed
        if self.vel.y >= st.TILESIZE // 2:
            self.vel.y = st.TILESIZE // 2 - 1
        self.pos += self.vel
        self.acc *= 0
        # collision detection
        self.rect.left = self.pos.x
        fn.collide(self, others, 'x')
        self.rect.top = self.pos.y
        fn.collide(self, others, 'y')

        # kill if not in bounds
        if not - st.TILESIZE < self.pos.x < st.MAP_WIDTH + st.TILESIZE:
            self.kill()
        if not self.pos.y < st.MAP_HEIGHT + st.TILESIZE:
            self.kill()
            


class Player(Physics_object):
    def __init__(self, game, x, y):
        self.game = game
        self.image = pg.Surface((st.TILESIZE, int(st.TILESIZE * 1.5)), 
                                flags=pg.SRCALPHA)
        self.image.fill(st.RED)
        super().__init__()
        self.game.all_sprites.add(self)
        self.pos = vec(x, y)
        
        self.speed = 0.5
        self.friction = -0.12
        
        self.inventory = {}
        self.inventory_types = []
        self.inventory_selected = 0
        
        self.reach = 60
        
        
    def update(self, others):
        pressed = pg.key.get_pressed()
        move_left = pressed[pg.K_a]
        move_right = pressed[pg.K_d]
        
        self.acc.x = move_right - move_left       
        self.acc.x *= self.speed       
        self.acc.x += self.vel.x * self.friction
        
        super().update(others)
       
        # Add and remove blocks
        if self.game.mouseclickedleft:
            if len(self.inventory_types) > 0:
                type_ = self.inventory_types[self.inventory_selected]
                self.game.grid.player_add(self.game.block_pos, type_)
        
        if self.game.mouseclickedright:
            block = self.game.grid.get_at(self.game.block_pos)
            if block:
                block.hardness -= 1
                if block.hardness == 0:
                    self.game.grid.player_remove_at(self.game.block_pos)
                    block.kill()
                          
        for key in self.inventory:
            self.inventory[key] = min(self.inventory[key], 999)            
             
        # inventory stuff
        self.inventory_types = list(self.inventory)       
        
        
    def jump(self, blocks):
        self.rect.y += 1
        hits = pg.sprite.spritecollide(self, blocks, False)
        self.rect.y -= 1
        if hits:
            self.vel.y = -10

        
    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)
        


class Block(Physics_object):
    def __init__(self, game, type_, x, y):
        self.game = game
        self.type = type_
        self.image = pg.Surface((st.TILESIZE, st.TILESIZE))
        self.image.fill(st.BLOCK_TYPES[self.type]['color'])
        super().__init__()
        self.game.all_sprites.add(self)
        self.game.blocks.add(self)
        self.grid = self.game.grid
        self.pos = vec(x, y)
        self.rect.topleft = self.pos

        self.hardness = st.BLOCK_TYPES[self.type]['hardness']
        
        self.state = 'STATIC'
        self.age = 0
    
    
    def update(self, others):
        if self.type == 'dirt':
            # check if nothing is above on the map
            if (not self.grid.get_at((self.pos.x, self.pos.y - st.TILESIZE))
                and not self.grid.get_at((self.pos.x, 
                                             self.pos.y + st.TILESIZE)) == None):
                self.age += 1
                if self.age >= 600:
                    self.type = 'grass'
                    self.image.fill(st.BLOCK_TYPES[self.type]['color'])
                    self.age = 0
        
        if self.type == 'sand':
            # sands experiences gravity if no block is below it
            if (self.grid.get_at((self.pos.x, self.pos.y + st.TILESIZE))
                and self.state == 'STATIC'):
                return
            else:                
                super().update(others)
                                
                if self.vel.length_squared() == 0:
                    self.state = 'STATIC'
                else:
                    if self.state == 'STATIC':
                        self.game.grid.remove_at(self.pos)
                        self.state = 'MOVING'
                
                if self.state == 'STATIC':
                    if not self.game.grid.get_at(self.pos):
                        self.game.grid.block_add(self.pos, self)
        
        
        def draw(self, surface):
            surface.blit(self.image, self.rect.topleft)


    
class Block_drop(Physics_object):
    def __init__(self, game, type_, pos):
        self.game = game
        self.type = type_
        self.image = pg.Surface((10, 10))
        self.image.fill(st.BLOCK_TYPES[self.type]['color'])
        super().__init__()
        self.game.all_sprites.add(self)
        self.game.drops.add(self)        
        self.pos = vec(pos)
        self.rect.topleft = self.pos

    
    def update(self, others):
        # if not in camera range, kill
        rect = pg.Rect((0, 0), (st.SCREEN_WIDTH, st.SCREEN_HEIGHT))
        rect.topleft = self.game.camera.apply_point(rect.topleft)
        if not self.rect.colliderect(rect):
            self.kill()
            return
        
        # apply physics
        # exclude player from collision
        player = self.game.player 
        sprites = [other for other in others if other != player]
        super().update(sprites)
                    
        # object is drawn towards player
        self_to_player = player.rect.center - self.pos  
        if self_to_player.length_squared() < st.TILESIZE_SQUARED * 3:
            self.gravity = NULL
            self.pos += self_to_player.normalize() * 2     
        
        # check for collision with player
        if pg.sprite.collide_rect(self, player):
            self.kill()
            if self.type in player.inventory:
                player.inventory[self.type] += 1
            else:
                player.inventory[self.type] = 1
        
        self.seperate()
        
    
    def seperate(self):
        # seperate the block drops if they fall onto each other
        if len(self.game.drops) <= 1:
            return
        for drop in self.game.drops:
            if drop != self:
                dist = self.pos - drop.pos
                
        if 0 < dist.length_squared() < 25:
            # if they are less than 5 pixels apart, change their position
            self.pos += dist.normalize()  
            
class GUI:
    def __init__(self, game):
        self.game = game
        self.surf = pg.Surface((st.SCREEN_WIDTH, st.GUI_HEIGHT))
        self.surf.fill(st.BLACK)
        self.rect = self.surf.get_rect()
        self.pos = vec(0, st.SCREEN_HEIGHT)
        self.rect.topleft = self.pos 
        self.font = pg.font.SysFont('Arial', 12)
    
    
    def draw(self):
        screen = self.game.screen
        screen.blit(self.surf, self.rect)
        
        # draw blocks:
        player = self.game.player
        for i, key in enumerate(player.inventory):
            color = st.BLOCK_TYPES[key]['color']
            rect = pg.Rect((st.TILESIZE + i * st.TILESIZE * 3, 
                            st.SCREEN_HEIGHT + st.TILESIZE), 
                           (st.TILESIZE, st.TILESIZE))
            pg.draw.rect(screen, color, rect)
            # draw amount
            text = ' x ' + str(player.inventory[key])
            text_surf = self.font.render(text, False, st.WHITE)
            screen.blit(text_surf, (2 * st.TILESIZE + i * st.TILESIZE * 3,
                                    st.SCREEN_HEIGHT + st.TILESIZE))
        
        rect = pg.Rect((st.TILESIZE + self.game.player.inventory_selected 
                        * st.TILESIZE * 3, 
                       st.SCREEN_HEIGHT + st.TILESIZE), 
                           (st.TILESIZE, st.TILESIZE))
        if len(self.game.player.inventory_types) > 0:
            pg.draw.rect(screen, st.WHITE, rect, 2)
            
    
    def draw_loading_screen(self):
        self.game.screen.fill(st.RED)
        step = self.game.grid.step - 1
        pct = str(round(step / self.game.grid.no_of_steps, 2))
        text = 'Loading world map: {0}%  '.format(pct) + '|||||' * step
        text_surf = self.font.render(text, False, st.WHITE)
        self.game.screen.blit(text_surf,
                              (st.SCREEN_WIDTH // 4, st.SCREEN_HEIGHT // 2))
                              
        transformed_screen = pg.transform.scale(self.game.screen, 
                                    (self.game.monitor_screen.get_width(),
                                    self.game.monitor_screen.get_height()))
        self.game.monitor_screen.blit(transformed_screen, (0, 0))
        pg.display.update()