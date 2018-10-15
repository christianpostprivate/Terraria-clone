import pygame as pg
import traceback

WIDTH = 800
HEIGHT = 600
TILESIZE = 20

vec = pg.math.Vector2

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (100, 180, 0)
DARKGREEN = (60, 150, 0)
LIGHTGREEN = (150, 255, 150, 130)
BLUE = (0, 50, 170)

GRAVITY = 0.6

class Player(pg.sprite.Sprite):
    def __init__(self, x, y):
        pg.sprite.Sprite.__init__(self)
        self.pos = vec(x, y)
        self.acc = vec(0, 0)
        self.vel = vec(0, 0)
        self.image = pg.Surface((20, 30), flags=pg.SRCALPHA)
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
        
        self.speed = 0.5
        self.friction = -0.12
        
        
    def update(self, blocks):
        self.acc = vec(0, GRAVITY)
        
        pressed = pg.key.get_pressed()
        move_left = pressed[pg.K_a]
        move_right = pressed[pg.K_d]
        
        self.acc.x = move_right - move_left       
        self.acc.x *= self.speed       
        self.acc.x += self.vel.x * self.friction
        
        self.vel += self.acc  
        self.pos += self.vel + 0.5 * self.acc
        
        self.rect.centerx = self.pos.x
        collide_with_blocks(self, blocks, 'x')
        self.rect.centery = self.pos.y
        collide_with_blocks(self, blocks, 'y')
        
        self.pos.x = max(self.rect.w // 2, 
                         min(self.pos.x, WIDTH - self.rect.w // 2))
        self.pos.y = max(self.rect.h // 2, 
                         min(self.pos.y, HEIGHT - self.rect.h // 2))
        
        self.rect.center = self.pos
         
        
    def jump(self, blocks):
        self.rect.y += 1
        hits = pg.sprite.spritecollide(self, blocks, False)
        self.rect.y -= 1
        if hits:
            self.vel.y = -10

        
    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)
        


class Block(pg.sprite.Sprite):
     def __init__(self, game, x, y):
         pg.sprite.Sprite.__init__(self)
         self.game = game
         self.game.blocks.add(self)
         self.pos = vec(x, y)
         self.image = pg.Surface((TILESIZE, TILESIZE))
         self.image.fill(BLUE)
         self.rect = self.image.get_rect()
         self.rect.topleft = self.pos
    
    
     def draw(self, surface):
         surface.blit(self.image, self.rect.topleft)
         
         
         
class Grid:
    def __init__(self, game, width, height):
        self.game = game
        self.width = width
        self.height = height
        self.blocks = [[None for i in range(width)] for j in range(height)]
    
    
    def add(self, pos):
        grid_x = int(pos.x // TILESIZE)
        grid_y = int(pos.y // TILESIZE)
        if self.blocks[grid_y][grid_x] == None:
            b = Block(self.game, pos.x, pos.y)
            print('added at', grid_x, grid_y)
            self.blocks[grid_y][grid_x] = b
            
    
    def remove_at(self, pos):
        grid_x = int(pos.x // TILESIZE)
        grid_y = int(pos.y // TILESIZE)
        if self.blocks[grid_y][grid_x]:
            print('removed at', grid_x, grid_y)
            self.blocks[grid_y][grid_x].kill()
            self.blocks[grid_y][grid_x] = None
         
        
         
def collide_with_blocks(sprite, group, dir_):
    if dir_ == 'x':
        hits = pg.sprite.spritecollide(sprite, group, False)
        if hits:
            # hit from left
            if hits[0].rect.centerx > sprite.rect.centerx:
                sprite.pos.x = hits[0].rect.left - sprite.rect.w / 2
            # hit from right
            elif hits[0].rect.centerx < sprite.rect.centerx:
                sprite.pos.x = hits[0].rect.right + sprite.rect.w / 2
                            
            sprite.vel.x = 0
            sprite.rect.centerx = sprite.pos.x
            return True
            
    elif dir_ == 'y':
        hits = pg.sprite.spritecollide(sprite, group, False)
        if hits:
            # hit from top
            if hits[0].rect.centery > sprite.rect.centery:
                sprite.pos.y = hits[0].rect.top - sprite.rect.h / 2
            # hit from bottom
            elif hits[0].rect.centery < sprite.rect.centery:
                sprite.pos.y = hits[0].rect.bottom + sprite.rect.h / 2
                
            sprite.vel.y = 0
            sprite.rect.centery = sprite.pos.y
            return True
    return False
      
   
         
class Game:
    def __init__(self):
        # initialize pygame
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()
        pg.mouse.set_visible(False)
        
        self.mouseclickedleft = False
        self.mouseclickedright = False
        self.block_pos = vec(0, 0)
        
        self.p = Player(200, 200)
        
        self.tiles_w = WIDTH // TILESIZE
        self.tiles_h = HEIGHT // TILESIZE
        self.grid = Grid(self, self.tiles_w, self.tiles_h)
        
        self.blocks = pg.sprite.Group()
        # add bottom row
        for i in range(self.tiles_w):
            pos = vec(i * TILESIZE, HEIGHT - TILESIZE)
            self.grid.add(pos)

    
    def update(self):
        pg.display.set_caption(str(len(self.blocks)))
        
        self.p.update(self.blocks)
        
        self.m_pos = vec(pg.mouse.get_pos())
        self.p_to_mouse = self.m_pos - self.p.pos
        if 0 < self.p_to_mouse.length() > 100:
            self.p_to_mouse.scale_to_length(100)
        
        self.block_pos.x = (self.p.pos.x + self.p_to_mouse.x) // TILESIZE * TILESIZE
        self.block_pos.y = (self.p.pos.y + self.p_to_mouse.y) // TILESIZE * TILESIZE
        
        if self.mouseclickedleft:         
            self.grid.add(self.block_pos)
        
        if self.mouseclickedright:
            self.grid.remove_at(self.block_pos)
         
        self.mouseclickedleft = False
        self.mouseclickedright = False
        
        
    def draw(self):
        self.screen.fill(GREEN)
        
        for i in range(self.tiles_h):
            pg.draw.line(self.screen, DARKGREEN, (0, i * TILESIZE), 
                         (WIDTH, i * TILESIZE))
        for i in range(self.tiles_w):
            pg.draw.line(self.screen, DARKGREEN, (i * TILESIZE, 0), 
                         (i * TILESIZE, HEIGHT))   
        
        self.p.draw(self.screen)
        
        for block in self.blocks:
            block.draw(self.screen)
        
        # draw a line from player to mouse
        pg.draw.line(self.screen, BLACK, self.p.pos, self.p.pos + self.p_to_mouse, 2)
        
        circle_pos = (int(self.p.pos.x + self.p_to_mouse.x), 
                      int(self.p.pos.y + self.p_to_mouse.y))
        pg.draw.circle(self.screen, BLACK, circle_pos, 4)

        block_surf = pg.Surface((TILESIZE, TILESIZE)).convert_alpha()      
        pg.draw.rect(block_surf, LIGHTGREEN, ((0, 0), (TILESIZE, TILESIZE)))      
        self.screen.blit(block_surf, self.block_pos)
        
        pg.display.update()
        
    
    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    self.p.jump(self.blocks)
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
