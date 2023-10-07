import pyglet
from pyglet import gl
from pyglet.window import key

from Game import Car
from Game import Map

keys = key.KeyStateHandler()
images_dir = 'images/'
display_width = 1920
display_height = 960

class GameWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.width = display_width
        self.height = display_height
        
        gl.glClearColor(255,255, 255, 1, 0)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        self.map = Map()
        self.car = Car(self.map)
        
        pyglet.clock.schedule_interval(self.update, 1/60.)
        
    
    def on_draw(self):
        window.clear()
        self.map.draw()
        
    def on_key_press(self, symbol, modifiers):
        if symbol == key.W:
            self.car.accelerate = True
            self.car.acc = self.car.min_acc
            
        if symbol == key.A:
            self.car.turn_left = True
            
        if symbol == key.S:
            self.car.reverse = True
            self.car.rev = self.car.min_rev
            
        if symbol == key.D:
            self.car.turn_right = True
            
    def on_key_release(self, symbol, modifiers):
        if symbol == key.W:
            self.car.accelerate = False
            self.car.decrease_acc = True
            
        if symbol == key.A:
            self.car.turn_left = False

        if symbol == key.S:
            self.car.reverse = False
            
        if symbol == key.D:
            self.car.turn_right = False
        
    def update(self, dt):
        self.car.updateCarLocation(dt)
    
if __name__ == '__main__':
    window = GameWindow()

    window.push_handlers(keys)
    pyglet.app.run()