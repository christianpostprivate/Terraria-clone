import pygame as pg
from random import choice
import traceback

import sprites as spr
import functions as fn
import settings as st

'''
Simple engine for a Terraria-style game

To Do list:
    - add trees and bushes
    - quad trees for collision
    - mini map
    - collide function with only 1 spritecollide call
'''

vec = pg.math.Vector2


class Game:
    def __init__(self):
        # initialize pygame
        pg.init()
        self.screen = pg.Surface((st.SCREEN_WIDTH,st. SCREEN_HEIGHT + st.GUI_HEIGHT))
        self.monitor_screen = pg.display.set_mode((self.screen.get_width() * 
                                                   st.SCREEN_SCALE, 
                                    self.screen.get_height() * st.SCREEN_SCALE))
        self.clock = pg.time.Clock()
        #pg.mouse.set_visible(False)
        
        self.mouseclickedleft = False
        self.mouseclickedright = False
        self.block_pos = vec(0, 0)

        
        self.all_sprites = pg.sprite.Group()
        self.blocks = pg.sprite.Group()            
        self.drops = pg.sprite.Group()
        
        self.tiles_w = st.MAP_WIDTH // st.TILESIZE
        self.tiles_h =st.MAP_HEIGHT // st.TILESIZE
        self.grid = fn.Grid(self, self.tiles_w, self.tiles_h)

        self.background = pg.Surface((st.SECTOR_WIDTH * st.TILESIZE * 10 , 
                                      st.SECTOR_HEIGHT * st.TILESIZE * 10))
        self.background_rect = self.background.get_rect()
        self.background.fill(st.SKYBLUE)
        
        self.gui = spr.GUI(self)
        
        self.started = False
        
    
    def start_game(self):
        spawn_pos = self.find_spawn_position()
        
        self.player = spr.Player(self, spawn_pos.x, spawn_pos.y)
        self.camera = fn.Camera(st.MAP_WIDTH, st.MAP_HEIGHT)
        
        self.grid.manage_blocks_initial()
        
        # quadtree stuff
        self.qt_rect = pg.Rect(0, 0, 40 * st.TILESIZE, 60 * st.TILESIZE)
        
        self.started = True
      
        # ------- debugging!
        self.player.inventory['dirt'] = 99
        self.player.inventory['sand'] = 99

    
    def find_spawn_position(self):
        spawn_positions = []
        # find empty position:
        for i in range(1, self.grid.horizon):
            for j in range(1, self.grid.width - 1):
                if (self.grid.map_blueprint[i][j] == None 
                        and self.grid.map_blueprint[i - 1][j] == None
                        and self.grid.map_blueprint[i + 1][j] != None):
                    spawn_positions.append(vec(j * st.TILESIZE, i * st.TILESIZE))
        return choice(spawn_positions)
    
    
    def save_world_image(self):
        surf = pg.Surface((self.grid.width * 4, self.grid.height * 4))
        surf.fill(st.LIGHTBLUE)
        for i in range(self.grid.height):
            for j in range(self.grid.width):
                if self.grid.map_blueprint[i][j]:
                    color = st.BLOCK_TYPES[self.grid.map_blueprint[i][j]]['color']
                    pg.draw.rect(surf, color, ((j * 4, i * 4), (4, 4)))
        
        pg.image.save(surf, 'world.png')
        
    
    def draw_sectors(self):
        # draw the sector boundaries
        sector_xs = [x * st.SECTOR_WIDTH * st.TILESIZE for x in range(st.NO_SECTORS_W)]
        sector_ys = [y * st.SECTOR_HEIGHT * st.TILESIZE for y in range(st.NO_SECTORS_H)]
        
        for x in sector_xs:
            start = self.camera.apply_point_reverse((x, 0))
            end = self.camera.apply_point_reverse((x, st.MAP_HEIGHT))
            pg.draw.line(self.screen, st.GREEN, start, end)
            
        for y in sector_ys:
            start = self.camera.apply_point_reverse((0, y))
            end = self.camera.apply_point_reverse((st.MAP_WIDTH, y))
            pg.draw.line(self.screen, st.GREEN, start, end)
                

    
    def update(self):
        self.grid.manage_blocks()
        
        caption = ('Sector_w: ' + str(self.grid.sector_w)
            + '  Sector_h: ' + str(self.grid.sector_h)
            + ' | ' + str(len(self.all_sprites)) + ' sprites | FPS: ' 
            + str(round(self.clock.get_fps(), 2)))
        
        pg.display.set_caption(caption)
        
        
        # quadtree stuff             
        self.qtree_rects = []
        self.qt_rect.center = self.player.rect.center
        self.qt = fn.Quadtree(self.qt_rect, 4)
    
        for sprite in self.all_sprites:
            self.qt.insert(sprite)
            if not isinstance(sprite, spr.Block_drop):
                if sprite == self.player:
                     sprite.update(self.blocks)
                else:
                    sprite.update(self.all_sprites)
            else:
                rect = pg.Rect(sprite.pos, (40, 40))
                rect.center = sprite.rect.center
                self.qtree_rects.append(self.camera.apply_rect(rect))
                neighbors = self.qt.query(rect)
                sprite.update(neighbors)
            
        self.camera.update(self.player)

        self.m_pos = vec(pg.mouse.get_pos())
        self.m_pos /= st.SCREEN_SCALE
        self.m_pos = self.camera.apply_point(self.m_pos)

        self.p_to_mouse = self.m_pos - self.player.rect.center
        # scale player_to_mouse vector
        #if 0 < self.p_to_mouse.length() > self.player.reach:
        #    self.p_to_mouse.scale_to_length(self.player.reach)
        
        # block cursor for mining and placing blocks
        self.block_pos.x = (self.player.rect.centerx + 
                            self.p_to_mouse.x) // st.TILESIZE * st.TILESIZE
        self.block_pos.y = (self.player.rect.centery + 
                            self.p_to_mouse.y) // st.TILESIZE * st.TILESIZE
        self.block_pos.y = min(self.block_pos.y, st.MAP_HEIGHT - st.TILESIZE)   

        self.mouseclickedleft = False
        self.mouseclickedright = False
        
        
        
    def draw(self):
        self.background_rect.centerx = self.player.rect.centerx
        self.screen.blit(self.background, self.camera.apply_rect(self.background_rect))
        
        # get the rect position of the player on the screen
        rect = self.camera.apply(self.player)
        
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, self.camera.apply(sprite))

        # draw a line from player to mouse
        pg.draw.line(self.screen, st.BLACK, rect.center, 
                     rect.center + self.p_to_mouse, 2)       
        
        block_surf = pg.Surface((st.TILESIZE, st.TILESIZE)).convert_alpha()      
        pg.draw.rect(block_surf, st.LIGHTGREEN, ((0, 0), (st.TILESIZE, st.TILESIZE)))
        block_rect = block_surf.get_rect()
        block_rect.topleft = self.block_pos
        self.screen.blit(block_surf, self.camera.apply_rect(block_rect))
        
        # draw quadtree rects
        #for rect in self.qtree_rects:
            #pg.draw.rect(self.screen, (0, 255, 0), rect, 1)

        #pg.draw.rect(self.screen, (0, 255, 0), self.camera.apply_rect(self.qt_rect), 2)
        
        #self.draw_sectors()
        
        self.gui.draw()
        
        transformed_screen = pg.transform.scale(self.screen, 
                                    (self.monitor_screen.get_width(),
                                    self.monitor_screen.get_height()))
        self.monitor_screen.blit(transformed_screen, (0, 0))
     
        pg.display.update()
        
    
    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.save_world_image()
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
            
            if not self.grid.done:
                self.grid.generate()
                self.gui.draw_loading_screen()
            else:
                if not self.started:
                    self.start_game()
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