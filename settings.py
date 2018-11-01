SCREEN_SCALE = 2
SCREEN_WIDTH = 800 // SCREEN_SCALE
SCREEN_HEIGHT = 600 // SCREEN_SCALE


TILESIZE = 16
TILESIZE_SQUARED = TILESIZE ** 2
MAP_WIDTH = 420 * TILESIZE
MAP_HEIGHT = 120 * TILESIZE
GUI_HEIGHT = 3 * TILESIZE
SECTOR_WIDTH = 14
SECTOR_HEIGHT = 12
NO_SECTORS_W = MAP_WIDTH // (SECTOR_WIDTH * TILESIZE)
NO_SECTORS_H = MAP_HEIGHT // (SECTOR_HEIGHT * TILESIZE)


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

BLOCK_TYPES = {
        'grass': {
                'color': DARKGREEN,
                'hardness': 1
                },
        'dirt': {
                'color': BROWN,
                'hardness': 1
                }, 
        'sand': {
                'color': YELLOW,
                'hardness': 1
                }, 
        'stone': {
                'color': DARKGREY,
                'hardness': -1
                },
        'ruby': {
                'color': RUBY,
                'hardness': 5
                },
        'ore': {
                'color': SILVER,
                'hardness': 3
                },       
        }