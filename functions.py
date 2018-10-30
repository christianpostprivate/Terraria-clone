import pygame as pg
from random import random

import sprites as spr
import settings as st

vec = pg.math.Vector2


def collide(sprite, group, dir_):
    '''
    collision function
    https://github.com/kidscancode/pygame_tutorials
    '''
    if dir_ == 'x':
        # horizontal collision
        hits = pg.sprite.spritecollide(sprite, group, False)
        if hits:
            for hit in hits:
                if hit == sprite:
                    continue
                # hit from left
                if hit.rect.left > sprite.rect.left:
                    sprite.pos.x = hit.rect.left - sprite.rect.w
                # hit from right
                elif hit.rect.right < sprite.rect.right:
                    sprite.pos.x = hit.rect.right
                                
                sprite.vel.x = 0
                sprite.rect.left = sprite.pos.x
                return True
            
    elif dir_ == 'y':
        # vertical collision
        hits = pg.sprite.spritecollide(sprite, group, False)
        if hits:
            for hit in hits:
                if hit == sprite:
                    continue
                # hit from top
                if hit.rect.top > sprite.rect.top:
                    sprite.pos.y = hit.rect.top - sprite.rect.h
                # hit from bottom
                elif hit.rect.top < sprite.rect.top:
                    sprite.pos.y = hit.rect.bottom
                    
                sprite.vel.y = 0
                sprite.rect.top = sprite.pos.y
                return True
    return False


class Grid:
    '''
    object that generates and holds a 2D array of Block objects 
    and also has methods for placing and removing them
    '''
    def __init__(self, game, width, height):
        self.game = game
        self.width = width
        self.height = height
        self.map_blueprint = [[None for i in range(width)] for j in range(height)]
        self.map = [[None for i in range(width)] for j in range(height)]
        
        self.death_limit = 3
        self.birth_limit = 4
        self.no_of_steps = 5
        self.done = False
        self.step = 0
        
        self.treasure_limit = 5
        # height in tiles that are only sky        
        self.horizon = 20 
        # the ID of the sector the player is in (see manage_blocks())
        self.sector = 0
        
    
    def generate(self):
        '''
        generates a cave 
        credits to:
        https://gamedevelopment.tutsplus.com/tutorials/
        generate-random-cave-levels-using-cellular-automata--gamedev-9664
        '''
        if self.step <= self.no_of_steps:
            string = ('Loading map: ' + str(self.step) + ' / ' + str(self.no_of_steps))
            pg.display.set_caption(string)
        if self.step == 0:
            placement_chance = 0.38
            
            for y in range(self.horizon, self.height - 1):
                for x in range(self.width):
                    if random() < placement_chance:
                        self.map_blueprint[y][x] = 'dirt'
                    
            self.step += 1
        
        elif 1 <= self.step <= self.no_of_steps:           
            self.map_blueprint = self.simulation_step(self.map_blueprint)
            self.step += 1
            
        else:
            # erase sky
            for y in range(self.horizon):
                for x in range(self.width):
                    self.map_blueprint[y][x] = None
                    
            # place solid blocks around the map
            for y in range(self.height):
                self.map_blueprint[y][0] = 'stone'
                self.map_blueprint[y][self.width - 1] = 'stone'
            for x in range(self.width):
                self.map_blueprint[self.height - 1][x] = 'stone'
            
            self.place_grass()
            self.place_treasure()
            self.done = True
    
    
    def simulation_step(self, old_map):
        new_map = [[None for x in range(self.width)] 
                      for y in range(self.height)]       
        for y in range(self.height):
            for x in range(self.width):
                nbs = self.count_alive_neighbors(old_map, x, y)
                
                if old_map[y][x] == 'dirt':
                    if nbs < self.death_limit:
                        new_map[y][x] = None
                    else:
                        new_map[y][x] = 'dirt'
                else:
                    if nbs < self.birth_limit:
                        new_map[y][x] = None
                    else:
                        new_map[y][x] = 'dirt'
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
                if (self.map_blueprint[y][x] != None 
                        and self.map_blueprint[y - 1][x] == None
                        and self.map_blueprint[y + 1][x] != None):
                    self.map_blueprint[y][x] = 'grass'
                    
    
    def place_treasure(self):
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.map_blueprint[y][x] == None:
                    nbs = self.count_alive_neighbors(self.map_blueprint, x, y)
                    if nbs >= self.treasure_limit:
                        self.map_blueprint[y][x] = 'ore'
    
    
    def manage_blocks_initial(self):
        player = self.game.player
        self.sector = int((player.pos.x / st.MAP_WIDTH) * st.NO_OF_SECTORS)
        for i in range(self.width):
            # load sector the player is in
            # and the ones left and right
            if (i >= (self.sector - 1) * st.SECTOR_SIZE 
                and i < (self.sector + 2) * st.SECTOR_SIZE):
                for j in range(self.height):
                    if self.map_blueprint[j][i]:
                        b_x = int(i * st.TILESIZE)
                        b_y = int(j * st.TILESIZE)
                        self.map[j][i] = spr.Block(self.game, 
                                self.map_blueprint[j][i], b_x, b_y)
    
    
    def manage_blocks(self):
        '''
        creates and deletes blocks around the players FOV
        '''                    
        player = self.game.player
        # calculating the sector the player is in
        change = 0
        sector = int((player.pos.x / st.MAP_WIDTH) * st.NO_OF_SECTORS)
        if sector != self.sector:
            change = sector - self.sector
            self.sector = sector
        
        if change != 0:
            # if the player went to a different sector
            # load blocks in sector based on direction
            for i in range(self.width):
                if change == 1:
                    # load sector the player is going to
                    if (i >= (self.sector + 1) * st.SECTOR_SIZE and 
                        i < (self.sector + 2) * st.SECTOR_SIZE):
                        for j in range(self.height):
                            if self.map_blueprint[j][i]:
                                b_x = int(i * st.TILESIZE)
                                b_y = int(j * st.TILESIZE)
                                self.map[j][i] = spr.Block(self.game, 
                                        self.map_blueprint[j][i], b_x, b_y)

                    # unload the sector the player is leaving
                    if (i < (self.sector - 1) * st.SECTOR_SIZE):
                        for j in range(self.height):
                            if self.map[j][i]:
                                self.map[j][i].kill()
                                self.map[j][i] = None
                                
                elif change == -1:           
                    # load sector the player is going to
                    if (i < self.sector * st.SECTOR_SIZE and 
                        i >= (self.sector - 1) * st.SECTOR_SIZE):
                        for j in range(self.height):
                            if self.map_blueprint[j][i]:
                                b_x = int(i * st.TILESIZE)
                                b_y = int(j * st.TILESIZE)
                                self.map[j][i] = spr.Block(self.game, 
                                        self.map_blueprint[j][i], b_x, b_y)
                                
                    # unload the sector the player is leaving
                    if (i >= (self.sector + 2) * st.SECTOR_SIZE):
                        for j in range(self.height):
                            if self.map[j][i]:
                                self.map[j][i].kill()
                                self.map[j][i] = None    
                                
    
    def add(self, pos, type_):
        grid_x = int(pos.x // st.TILESIZE)
        grid_y = int(pos.y // st.TILESIZE)
        if not self.map[grid_y][grid_x]:
            b = spr.Block(self.game, type_, pos.x, pos.y)
            self.map[grid_y][grid_x] = b
            
            
    def set_at(self, pos, type_):
        grid_x = int(pos.x // st.TILESIZE)
        grid_y = int(pos.y // st.TILESIZE)
        b = spr.Block(self.game, type_, pos.x, pos.y)
        self.map[grid_y][grid_x] = b
            
    
    def block_add(self, pos, block):
        grid_x = int(pos.x // st.TILESIZE)
        grid_y = int(pos.y // st.TILESIZE)
        if self.map[grid_y][grid_x] == None:
            self.map[grid_y][grid_x] = block
            
    
    def player_add(self, pos, type_):
        grid_x = int(pos.x // st.TILESIZE)
        grid_y = int(pos.y // st.TILESIZE)
        if self.map[grid_y][grid_x] == None:
            inv = self.game.player.inventory
            if type_ in inv:
                if inv[type_] > 0:
                    inv[type_] -= 1
                    b = spr.Block(self.game, type_, pos.x, pos.y)
                    self.map[grid_y][grid_x] = b
                    self.map_blueprint[grid_y][grid_x] = type_
            
    
    def remove_at(self, pos):
        grid_x = int(pos.x // st.TILESIZE)
        grid_y = int(pos.y // st.TILESIZE)
        block = self.map[grid_y][grid_x]
        if block:
            self.map[grid_y][grid_x] = None
            
    
    def player_remove_at(self, pos):
        grid_x = int(pos.x // st.TILESIZE)
        grid_y = int(pos.y // st.TILESIZE)
        block = self.map[grid_y][grid_x]
        if block:
            spr.Block_drop(block.game, block.type, (block.rect.centerx - 5
                                                + random() - 0.5,
                                                block.rect.centery))
            self.map[grid_y][grid_x] = None
            self.map_blueprint[grid_y][grid_x] = None
            
    
    def get_at(self, pos):
        grid_x = int(pos[0] // st.TILESIZE)
        grid_y = int(pos[1] // st.TILESIZE)
        return self.map[grid_y][grid_x]
        


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
        x = -target.rect.x + st.SCREEN_WIDTH // 2
        y = -target.rect.y + st.SCREEN_HEIGHT // 2

        # limit scrolling to map size
        x = min(0, x) # left
        x = max(-(self.width - st.SCREEN_WIDTH), x) # right
        y = min(0, y) # top
        y = max(-(self.height - st.SCREEN_HEIGHT), y) # bottom
        
        self.camera = pg.Rect(x, y, self.width, self.height)
           
     
        
class Point(vec):
    '''
    subclass of Vector2 with reference to a sprite
    used for quadtree
    '''
    def __init__(self, pos, data=None):
        super().__init__()
        self.x = pos[0]
        self.y = pos[1]
        self.data = data
        


class Quadtree:
    def __init__(self, boundary, capacity):
        # boundary has to be a pg.Rect object
        if not isinstance(boundary, pg.Rect):
            print('boundary has to be a Rect object')
        self.boundary = boundary
        self.capacity = capacity
        self.sprites = []
        self.divided = False
    
    
    def subdivide(self):
        x = self.boundary.x
        y = self.boundary.y
        w = self.boundary.w / 2
        h = self.boundary.h / 2
        
        ne = pg.Rect(x, y, w, h)
        self.northeast = Quadtree(ne, self.capacity)
        nw = pg.Rect(x + w, y, w, h)
        self.northwest = Quadtree(nw, self.capacity)
        se = pg.Rect(x, y + h, w, h)
        self.southeast = Quadtree(se, self.capacity)
        sw = pg.Rect(x + w, y + h, w, h)
        self.southwest = Quadtree(sw, self.capacity)
        
        self.divided = True
        
    
    def insert(self, sprite):
        if not self.boundary.collidepoint(sprite.pos):
            return False
        
        if len(self.sprites) < self.capacity:
            self.sprites.append(sprite)
            return True
        
        if not self.divided:
            self.subdivide()
            
        return (self.northeast.insert(sprite) or self.northwest.insert(sprite)
                or self.southeast.insert(sprite) or self.southwest.insert(sprite))
        
        
    def query(self, rect, found=None):
        if found == None:
            found = []
            
        if not rect.colliderect(self.boundary):
            return found
        
        for s in self.sprites:
            if rect.collidepoint(s.pos):
                found.append(s)
                
        if self.divided:
            self.northwest.query(rect, found)
            self.northeast.query(rect, found)
            self.southwest.query(rect, found)
            self.southeast.query(rect, found)

        return found
    
    
    def draw(self, screen):
        pg.draw.rect(screen, (100, 100, 100), self.boundary, 1)
        
        if self.divided:
            self.northwest.draw(screen)
            self.northeast.draw(screen)
            self.southwest.draw(screen)
            self.southeast.draw(screen)