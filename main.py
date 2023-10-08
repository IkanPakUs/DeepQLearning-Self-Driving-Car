import pyglet
from pyglet import gl
from pyglet.window import key

from Game import Game
from Network import Network

keys = key.KeyStateHandler()

images_dir = 'images/'

display_width = 1920
display_height = 960

class GameWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.width = display_width
        self.height = display_height
        
        self.Game = Game()
        self.Car = self.Game.Car
        self.Map = self.Game.Map
        self.AI = Network(self.Game)
        
        gl.glClearColor(255,255, 255, 1, 0)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        cursor = self.get_system_mouse_cursor(self.CURSOR_CROSSHAIR)
        self.set_mouse_cursor(cursor)        
        
        pyglet.clock.schedule_interval(self.update, 1/30.)
        
    
    def on_draw(self):
        window.clear()
        self.Game.draw()
        
    def on_key_press(self, symbol, modifiers):
        # if symbol == key.W:
        #     self.Car.accelerate = True
        #     self.Car.acc = self.Car.min_acc
            
        # if symbol == key.A:
        #     self.Car.turn_left = True
            
        # if symbol == key.S:
        #     self.Car.reverse = True
        #     self.Car.rev = self.Car.min_rev
            
        # if symbol == key.D:
        #     self.Car.turn_right = True
            
        # if symbol == key.B:
        #     self.Map.drawing_mode = not self.Map.drawing_mode
            
        # if symbol == key.T:
        #     if not self.Map.drawing_mode:
        #         print ('Not in drawing mode')
                
        #     print(self.Map.type_line)
            
        # if symbol == key.E:
        #     self.Map.saveLine()
        
        # if symbol == key.Q:
        #     self.Map.cancelLine()
            
        # if symbol == key.Z:
        #     self.Map.undoLastLine()
            
        # if symbol == key.L:
        #     self.Map.switchTypeLine()
        
        if symbol == key.O:
            self.AI.training = not self.AI.training
            
    def on_key_release(self, symbol, modifiers):
        # if symbol == key.W:
        #     self.Car.accelerate = False
        #     self.Car.decrease_acc = True
            
        # if symbol == key.A:
        #     self.Car.turn_left = False

        # if symbol == key.S:
        #     self.Car.reverse = False
            
        # if symbol == key.D:
        #     self.Car.turn_right = False
        pass
            
            
    def on_mouse_press(self, x, y, buttons, modifiers):
        self.Map.createLine(x, y)        
        
    def update(self, dt):
        print('update')
        if self.AI.training:
            print('train')
            self.AI.train()
            return 
            
        # self.Car.updateCarLocation(1)
    
if __name__ == '__main__':
    window = GameWindow()

    window.push_handlers(keys)
    
    pyglet.app.run()