'''
Simple engine for a Terraria-style game

'''

import pygame as pg
import traceback
from random import random, choice

# some constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 300
SCREEN_SCALE = 2

TILESIZE = 16
TILESIZE_SQUARED = TILESIZE ** 2
MAP_WIDTH = 340 * TILESIZE
MAP_HEIGHT = 80 * TILESIZE
GUI_HEIGHT = 3 * TILESIZE

vec = pg.math.Vector2

GRAVITY = vec(0, 0.5)
NULL = vec(0, 0)

# colors (no way)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARKGREY = (60, 60, 60)
RED = (255, 0, 0)
RUBY = (130, 0, 20)
GREEN = (100, 180, 0)
DARKGREEN = (60, 150, 0)
LIGHTGREEN = (150, 255, 150, 130)
BLUE = (0, 50, 170)
SKYBLUE = (200, 200, 255)
LIGHTBLUE = (180, 180, 255)
BROWN = (100, 60, 20)
YELLOW = (250, 200, 100)
SILVER = (92, 92, 130)

# dict for the different blocks and their values
BLOCK_TYPES = {
        'grass': {
                'color': DARKGREEN,
                'hardness': 1,
                'weight': 1
                },
        'dirt': {
                'color': BROWN,
                'hardness': 1,
                'weight': 1
                }, 
        'sand': {
                'color': YELLOW,
                'hardness': 1,
                'weight': 2
                }, 
        'stone': {
                'color': DARKGREY,
                'hardness': -1,
                'weight': 1
                },
        'ruby': {
                'color': RUBY,
                'hardness': 5,
                'weight': 1
                },
        'ore': {
                'color': SILVER,
                'hardness': 3,
                'weight': 1
                },       
        }



def collide(sprite, group, dir_):
    '''
    collision function
    https://github.com/kidscancode/pygame_tutorials
    '''
    if dir_ == 'x':
        # horizontal collision
        hits = pg.sprite.spritecollide(sprite, group, False)
        if hits:
            if hits[0] == sprite:
                return False
            # hit from left
            if hits[0].rect.left > sprite.rect.left:
                sprite.pos.x = hits[0].rect.left - sprite.rect.w
            # hit from right
            elif hits[0].rect.right < sprite.rect.right:
                sprite.pos.x = hits[0].rect.right
                            
            sprite.vel.x = 0
            sprite.rect.left = sprite.pos.x
            return True
            
    elif dir_ == 'y':
        # vertical collision
        hits = pg.sprite.spritecollide(sprite, group, False)
        if hits:
            if hits[0] == sprite:
                return False
            # hit from top
            if hits[0].rect.top > sprite.rect.top:
                sprite.pos.y = hits[0].rect.top - sprite.rect.h
            # hit from bottom
            elif hits[0].rect.top < sprite.rect.top:
                sprite.pos.y = hits[0].rect.bottom
                
            sprite.vel.y = 0
            sprite.rect.top = sprite.pos.y
            return True
    return False



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
        self.acc = self.gravity
        
        self.vel += self.acc
        pos_change = self.vel + 0.5 * self.acc
        if pos_change.length_squared() >= TILESIZE_SQUARED:
            pos_change.scale_to_length(TILESIZE_SQUARED - 1)
        self.pos += pos_change
        # collision detection
        self.rect.left = self.pos.x
        collide(self, others, 'x')
        self.rect.top = self.pos.y
        collide(self, others, 'y')

        # kill if not in bounds
        if not -TILESIZE < self.pos.x < MAP_WIDTH + TILESIZE:
            self.kill()
        if not - 5 * TILESIZE < self.pos.y < MAP_HEIGHT + TILESIZE:
            self.kill()
            


class Player(Physics_object):
    def __init__(self, game, x, y):
        self.game = game
        self.image = pg.Surface((TILESIZE, int(TILESIZE * 1.5)), flags=pg.SRCALPHA)
        self.image.fill(RED)
        super().__init__()
        self.game.all_sprites.add(self)
        self.pos = vec(x, y)
        
        self.speed = 0.5
        self.friction = -0.12
        
        self.inventory = {}
        self.inventory_types = []
        self.inventory_selected = 0
        
        self.reach = 60
        
        
    def update(self):
        pressed = pg.key.get_pressed()
        move_left = pressed[pg.K_a]
        move_right = pressed[pg.K_d]
        
        self.acc.x = move_right - move_left       
        self.acc.x *= self.speed       
        self.acc.x += self.vel.x * self.friction
        
        super().update(self.game.blocks)
       
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
        


class Block(pg.sprite.Sprite):
    def __init__(self, game, type_, x, y):
        pg.sprite.Sprite.__init__(self)
        self.game = game
        self.grid = self.game.grid
        self.type = type_
        self.game.all_sprites.add(self)
        self.game.blocks.add(self)
        self.pos = vec(x, y)
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(BLOCK_TYPES[self.type]['color'])
        self.rect = self.image.get_rect()
        self.rect.topleft = self.pos
        
        self.acc = vec(0, 0)
        self.vel = vec(0, 0)
        self.gravity = vec(GRAVITY)
        
        self.hardness = BLOCK_TYPES[self.type]['hardness']
        self.weight = BLOCK_TYPES[self.type]['weight']
        
        self.state = 'STATIC'
        self.age = 0
    
    
    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)
    
    
    def update(self):
        if self.type == 'dirt':
            # check if nothing is above on the map
            if (not self.grid.get_at((self.pos.x, self.pos.y - TILESIZE))
                and not self.grid.get_at((self.pos.x, 
                                             self.pos.y + TILESIZE)) == None):
                self.age += 1
                if self.age >= 600:
                    self.type = 'grass'
                    self.image.fill(BLOCK_TYPES[self.type]['color'])
                    self.age = 0
        
        if self.type == 'sand':
            # sands experiences gravity if no block is below it
            if (self.grid.get_at((self.pos.x, self.pos.y + TILESIZE))
                and self.state == 'STATIC'):
                return
            else:
                self.acc = self.gravity * self.weight
                
                self.vel += self.acc  
                if self.vel.length_squared() >= TILESIZE_SQUARED:
                    self.vel.scale_to_length(TILESIZE - 1)
                self.pos += self.vel + 0.5 * self.acc
                
                blocks = self.game.blocks
                self.rect.left = self.pos.x
                collide(self, blocks, 'x')
                self.rect.top = self.pos.y
                collide(self, blocks, 'y')       
                self.rect.topleft = self.pos
                if self.vel.length_squared() == 0:
                    self.state = 'STATIC'
                else:
                    if self.state == 'STATIC':
                        self.game.grid.remove_at(self.pos)
                        self.state = 'MOVING'
                
                if self.state == 'STATIC':
                    if not self.game.grid.get_at(self.pos):
                        self.game.grid.block_add(self.pos, self)
    
    
    
class Block_drop(Physics_object):
    def __init__(self, game, type_, pos):
        self.game = game
        self.type = type_
        self.image = pg.Surface((10, 10))
        self.image.fill(BLOCK_TYPES[self.type]['color'])
        super().__init__()
        self.game.all_sprites.add(self)
        self.game.drops.add(self)        
        self.pos = vec(pos)
        self.rect.topleft = self.pos

    
    def update(self):
        # if not in camera range, kill
        rect = pg.Rect((0, 0), (SCREEN_WIDTH, SCREEN_HEIGHT))
        rect.topleft = self.game.camera.apply_point(rect.topleft)
        if not self.rect.colliderect(rect):
            self.kill()
            return
        
        # apply physics
        
        blocks = self.game.blocks
        super().update(blocks)
        
        player = self.game.player
        
        # object is drawn towards player
        self_to_player = player.pos - self.pos  
        if self_to_player.length_squared() < TILESIZE_SQUARED * 3:
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
                
        if dist.length_squared() < 25:
            # if they are less than 5 pixels apart, change their position
            self.pos += dist.normalize()      
            
            
         
class Grid:
    '''
    object that generates and holds a 2D array of Block objects 
    and also has methods for placing and removing them
    '''
    def __init__(self, game, width, height):
        self.game = game
        self.width = width
        self.height = height
        self.map = [[False for i in range(width)] for j in range(height)]
        
        self.death_limit = 3
        self.birth_limit = 4
        self.no_of_steps = 5
        
        self.treasure_limit = 5
        
        self.horizon = 20
        
    
    def generate(self):
        '''
        generates a cave 
        credits to:
        https://gamedevelopment.tutsplus.com/tutorials/
        generate-random-cave-levels-using-cellular-automata--gamedev-9664
        '''
        placement_chance = 0.38
        
        # generates a grid with values True or False, than later fills
        # it with blocks
        for y in range(self.horizon, self.height - 1):
            for x in range(self.width):
                if random() < placement_chance:
                    self.map[y][x] = True
                    
        for i in range(self.no_of_steps):
            self.map = self.simulation_step(self.map)
        
        # place block or None
        for y in range(self.height - 1):
            for x in range(self.width):
                if y < self.horizon:
                    self.map[y][x] = None
                else:
                    if self.map[y][x]:
                        pos_x = x * TILESIZE
                        pos_y = y * TILESIZE
                        self.map[y][x] = Block(self.game, 'dirt', pos_x, pos_y)
                    else:
                        self.map[y][x] = None
    
    
    def simulation_step(self, old_map):
        new_map = [[None for x in range(self.width)] 
                      for y in range(self.height)]       
        for y in range(self.height):
            for x in range(self.width):
                nbs = self.count_alive_neighbors(old_map, x, y)
                
                if old_map[y][x]:
                    if nbs < self.death_limit:
                        new_map[y][x] = False
                    else:
                        new_map[y][x] = True
                else:
                    if nbs < self.birth_limit:
                        new_map[y][x] = False
                    else:
                        new_map[y][x] = True
        return new_map
                          
    
    def count_alive_neighbors(self, map_,  x, y):
        count = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                neighbor_x = x + i
                neighbor_y = y + j
                if i == 0 and j == 0:
                    # middle point
                    pass
                elif (neighbor_x < 0 or neighbor_y < 0 or 
                      neighbor_x >= self.width or neighbor_y >= self.height):
                    count += 1
                elif map_[neighbor_y][neighbor_x]:
                    count += 1    
        return count
    
    
    def place_grass(self):
        # place grass block if there is a block below and 
        # no block above
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if (self.map[y][x] != None 
                        and self.map[y - 1][x] == None
                        and self.map[y + 1][x] != None):
                    pos_x = x * TILESIZE
                    pos_y = y * TILESIZE
                    self.map[y][x].kill()
                    self.map[y][x] = Block(self.game, 'grass', pos_x, pos_y)
                    
    
    def place_treasure(self):
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.map[y][x] == None:
                    nbs = self.count_alive_neighbors(self.map, x, y)
                    if nbs >= self.treasure_limit:
                        pos_x = x * TILESIZE
                        pos_y = y * TILESIZE
                        self.map[y][x] = Block(self.game, 'ore', pos_x, pos_y)
                    
    
    def add(self, pos, type_):
        grid_x = int(pos.x // TILESIZE)
        grid_y = int(pos.y // TILESIZE)
        if not self.map[grid_y][grid_x]:
            b = Block(self.game, type_, pos.x, pos.y)
            self.map[grid_y][grid_x] = b
            
    def set(self, pos, type_):
        grid_x = int(pos.x // TILESIZE)
        grid_y = int(pos.y // TILESIZE)
        b = Block(self.game, type_, pos.x, pos.y)
        self.map[grid_y][grid_x] = b
            
    
    def block_add(self, pos, block):
        grid_x = int(pos.x // TILESIZE)
        grid_y = int(pos.y // TILESIZE)
        if self.map[grid_y][grid_x] == None:
            self.map[grid_y][grid_x] = block
            
    
    def player_add(self, pos, type_):
        grid_x = int(pos.x // TILESIZE)
        grid_y = int(pos.y // TILESIZE)
        if self.map[grid_y][grid_x] == None:
            inv = self.game.player.inventory
            if type_ in inv:
                if inv[type_] > 0:
                    inv[type_] -= 1
                    b = Block(self.game, type_, pos.x, pos.y)
                    self.map[grid_y][grid_x] = b
            
    
    def remove_at(self, pos):
        grid_x = int(pos.x // TILESIZE)
        grid_y = int(pos.y // TILESIZE)
        block = self.map[grid_y][grid_x]
        if block:
            self.map[grid_y][grid_x] = None
            
    
    def player_remove_at(self, pos):
        grid_x = int(pos.x // TILESIZE)
        grid_y = int(pos.y // TILESIZE)
        block = self.map[grid_y][grid_x]
        if block:
            Block_drop(block.game, block.type, (block.rect.centerx - 5
                                                + random() - 0.5,
                                                block.rect.centery))
            self.map[grid_y][grid_x] = None
            
    
    def get_at(self, pos):
        grid_x = int(pos[0] // TILESIZE)
        grid_y = int(pos[1] // TILESIZE)
        return self.map[grid_y][grid_x]
    


class GUI:
    def __init__(self, game):
        self.game = game
        self.surf = pg.Surface((SCREEN_WIDTH, GUI_HEIGHT))
        self.surf.fill(BLACK)
        self.rect = self.surf.get_rect()
        self.pos = vec(0, SCREEN_HEIGHT)
        self.rect.topleft = self.pos 
        self.font = pg.font.SysFont('Arial', 18)
    
    
    def draw(self):
        screen = self.game.screen
        screen.blit(self.surf, self.rect)
        
        # draw blocks:
        player = self.game.player
        for i, key in enumerate(player.inventory):
            color = BLOCK_TYPES[key]['color']
            rect = pg.Rect((TILESIZE + i * TILESIZE * 3, SCREEN_HEIGHT + TILESIZE), 
                           (TILESIZE, TILESIZE))
            pg.draw.rect(screen, color, rect)
            # draw amount
            text = ' x ' + str(player.inventory[key])
            text_surf = self.font.render(text, False, WHITE)
            screen.blit(text_surf, (2 * TILESIZE + i * TILESIZE * 3,
                                    SCREEN_HEIGHT + TILESIZE))
        
        rect = pg.Rect((TILESIZE + self.game.player.inventory_selected * TILESIZE * 3, 
                        SCREEN_HEIGHT + TILESIZE), 
                           (TILESIZE, TILESIZE))
        if len(self.game.player.inventory_types) > 0:
            pg.draw.rect(screen, WHITE, rect, 2)
        


class Camera:
    '''
    credits to http://kidscancode.org/lessons/
    '''
    def __init__(self, width, height):
        self.camera = pg.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)
    
    def apply_point(self, point):
        return point - vec(self.camera.x, self.camera.y)

    def update(self, target):
        x = -target.rect.x + SCREEN_WIDTH // 2
        y = -target.rect.y + SCREEN_HEIGHT // 2

        # limit scrolling to map size
        x = min(0, x) # left
        x = max(-(self.width - SCREEN_WIDTH), x) # right
        y = min(0, y) # top
        y = max(-(self.height - SCREEN_HEIGHT), y) # bottom
        
        self.camera = pg.Rect(x, y, self.width, self.height)
           
         
        
class Game:
    def __init__(self):
        # initialize pygame
        pg.init()
        self.screen = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT + GUI_HEIGHT))
        self.monitor_screen = pg.display.set_mode((self.screen.get_width() * 
                                                   SCREEN_SCALE, 
                                    self.screen.get_height() * SCREEN_SCALE))
        self.clock = pg.time.Clock()
        #pg.mouse.set_visible(False)
        
        self.mouseclickedleft = False
        self.mouseclickedright = False
        self.block_pos = vec(0, 0)
        
        self.all_sprites = pg.sprite.Group()
        self.blocks = pg.sprite.Group()
        self.drops = pg.sprite.Group()
        
        self.tiles_w = MAP_WIDTH // TILESIZE
        self.tiles_h = MAP_HEIGHT // TILESIZE
        self.grid = Grid(self, self.tiles_w, self.tiles_h)
        self.grid.generate()
        self.grid.place_treasure()    
        self.grid.place_grass()

        # add bottom row
        for i in range(self.tiles_w):
            pos = vec(i * TILESIZE, MAP_HEIGHT - TILESIZE)
            self.grid.set(pos, 'stone')
            
        self.background = pg.Surface((MAP_WIDTH, MAP_HEIGHT))
        self.background_rect = self.background.get_rect()
        self.background.fill(SKYBLUE)
        
        spawn_pos = self.find_spawn_position()
        
        self.player = Player(self, spawn_pos.x, spawn_pos.y)
        self.gui = GUI(self)
        self.camera = Camera(MAP_WIDTH, MAP_HEIGHT)
           
        
        # ------- debugging!
        #self.player.inventory['dirt'] = 999
        self.player.inventory['sand'] = 99
        
    
    def find_spawn_position(self):
        spawn_positions = []
        # find empty position:
        for i in range(1, self.grid.height - 1):
            for j in range(1, self.grid.width - 1):
                if (self.grid.map[i][j] == None 
                        and self.grid.map[i - 1][j] == None
                        and self.grid.map[i + 1][j] != None):
                    spawn_positions.append(vec(j * TILESIZE, i * TILESIZE))
        return choice(spawn_positions)
    
    
    def save_world_image(self):
        surf = pg.Surface((self.grid.width, self.grid.height))
        surf.fill(LIGHTBLUE)
        for i in range(self.grid.height):
            for j in range(self.grid.width):
                if self.grid.map[i][j]:
                    color = BLOCK_TYPES[self.grid.map[i][j].type]['color']
                    pg.draw.rect(surf, color, ((j, i), (1, 1)))
        
        pg.image.save(surf, 'world.png')
                

    
    def update(self):
        pg.display.set_caption(str(round(self.clock.get_fps(), 2)))

        for sprite in self.all_sprites:
             if (abs(sprite.pos.x - self.player.pos.x) < 
                    (SCREEN_WIDTH // 2 + TILESIZE) and
               (abs(sprite.pos.y - self.player.pos.y)) <
                    SCREEN_HEIGHT):
                    # only update what's on the screen
                    sprite.update()          
        self.camera.update(self.player)

        self.m_pos = vec(pg.mouse.get_pos())
        self.m_pos /= SCREEN_SCALE
        self.m_pos = self.camera.apply_point(self.m_pos)

        self.p_to_mouse = self.m_pos - self.player.rect.center
        # scale player_to_mouse vector
        #if 0 < self.p_to_mouse.length() > self.player.reach:
        #    self.p_to_mouse.scale_to_length(self.player.reach)
        
        self.block_pos.x = (self.player.rect.centerx + 
                            self.p_to_mouse.x) // TILESIZE * TILESIZE
        self.block_pos.y = (self.player.rect.centery + 
                            self.p_to_mouse.y) // TILESIZE * TILESIZE
        self.block_pos.y = min(self.block_pos.y, MAP_HEIGHT - TILESIZE)
         
        self.mouseclickedleft = False
        self.mouseclickedright = False
        
        
    def draw(self):
        self.screen.blit(self.background, self.camera.apply_rect(self.background_rect))
        
        # get the rect position of the player on the screen
        rect = self.camera.apply(self.player)
        
        for sprite in self.all_sprites:
            if (abs(sprite.pos.x - self.player.pos.x) < (
                    SCREEN_WIDTH // 2 + TILESIZE) and
               (abs(sprite.pos.y - self.player.pos.y)) < (
                    SCREEN_HEIGHT // 2 + TILESIZE)):
                # only blit what's on the screen
                self.screen.blit(sprite.image, self.camera.apply(sprite))

        # draw a line from player to mouse
        pg.draw.line(self.screen, BLACK, rect.center, 
                     rect.center + self.p_to_mouse, 2)       


        block_surf = pg.Surface((TILESIZE, TILESIZE)).convert_alpha()      
        pg.draw.rect(block_surf, LIGHTGREEN, ((0, 0), (TILESIZE, TILESIZE)))
        block_rect = block_surf.get_rect()
        block_rect.topleft = self.block_pos
        self.screen.blit(block_surf, self.camera.apply_rect(block_rect))
                     
        self.gui.draw()
        
        transformed_screen = pg.transform.scale(self.screen, 
                                    (self.monitor_screen.get_width(),
                                    self.monitor_screen.get_height()))
        self.monitor_screen.blit(transformed_screen, (0, 0))

        
        pg.display.update()
        
    
    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            # MEMO: EXPORT THE PRESSED KEYS TO A FUNCTION
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    self.player.jump(self.blocks)
                if event.key == pg.K_r:
                    if len(self.player.inventory_types) > 0:
                        self.player.inventory_selected = (
                                (self.player.inventory_selected + 1) % len(
                                self.player.inventory_types))
                        
            if event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouseclickedleft = True
                elif event.button == 3:
                    self.mouseclickedright = True


    def run(self):
        # game loop
        self.running = True 
        while self.running:
            self.clock.tick(60)
    
            self.events()
            
            self.update()
            self.draw()

        pg.quit()
   
    
    
if __name__ == '__main__':
    try:       
        game = Game()
        game.run()
    
    except Exception:
        traceback.print_exc()
        pg.quit()
