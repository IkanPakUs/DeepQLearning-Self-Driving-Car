import pyglet
import math
import json
import numpy as np
from Physic import Physic
from pyglet import shapes
from pyglet.math import Vec2

images_dir = 'images/'

display_width = 1920
display_height = 960

batch = pyglet.graphics.Batch()

class Game:
    def __init__(self) -> None:
        self.Map = Map()
        self.Car = Car(self, self.Map)
        
        self.reward = 0
        
    def newEpisode(self):
        self.Car.reset()
        
    def getState(self):
        return self.Car.getCurrentState()
    
    def makeAction(self, action):
        action_no = int(action)
        self.Car.updateCarLocation(action_no)
        
        return self.reward
    
    def isEpisodeFinished(self):
        return self.Car.is_dead
    
    def draw(self):
        self.Map.draw()

class Car:
    def __init__(self, Game, Map) -> None:
        car_image = pyglet.resource.image(images_dir + 'car.png')
        car_image.anchor_x = car_image.width / 2
        car_image.anchor_y = car_image.height / 2
        
        self.action_size = 9
        
        self.accelerate = False
        self.reverse = False
        self.turn_left = False
        self.turn_right = False

        self.car = pyglet.sprite.Sprite(img=car_image, batch=batch)
        self.car.width = 40
        self.car.height = 20
        self.car.rotation = -180
        self.car.x = 300
        self.car.y = 120

        self.min_acc = 0
        self.acc = self.min_acc
        self.acc_step = 4
        self.max_acc = 100
        
        self.decrease_acc = False
        self.dec_acc_step = 6
        
        self.min_rev = self.min_acc / 2
        self.rev = self.min_rev
        self.rev_step = 2
        self.max_rev = self.max_acc / 2
        
        self.turning_speed = 3 # Turning speed rate from 1 to 3
        
        self.car_direction = Vec2(-1, 0)

        self.car_collision = True
        self.is_dead = False
        
        self.dt = 1/30
        
        self.Map = Map
        self.Game = Game
        self.CarHitbox = CarHitbox(self, Game, Map)
        self.CarLine = CarLine(self, Map)
        self.Physic = Physic()
        
    def reset(self):
        if (self.car_collision):
            self.Game.reward = 0
            
            self.Map = Map()
            self.CarHitbox = CarHitbox(self, self.Game, self.Map)
            self.CarLine = CarLine(self, self.Map)
            
            self.car.width = 40
            self.car.height = 20
            self.car.rotation = -180
            self.car.x = 300
            self.car.y = 120
            
            self.min_acc = 0
            self.acc = self.min_acc
            self.acc_step = 4
            self.max_acc = 300
            
            self.decrease_acc = False
            self.dec_acc_step = 6
            
            self.min_rev = self.min_acc / 2
            self.rev = self.min_rev
            self.rev_step = 2
            self.max_rev = self.max_acc / 2
            
            self.turning_speed = 2 # Turning speed rate from 1 to 3
            
            self.car_direction = Vec2(-1, 0)
            
            self.is_dead = False
        
    def updateCarLocation(self, do_action = 8):   
        if not self.is_dead:
            self.checkActions(int(do_action))
            self.decreaseAcc()
        
    def checkSituation(self):
        self.CarHitbox.checkCarCollision()
        self.CarHitbox.checkCarReward()
        
        self.CarLine.checkLineCollision()
        self.CarLine.checkClosestGate()
    
    def checkActions(self, do_no):
        do_no = 1
        
        self.accelerate = False
        self.reverse = False
        self.turn_left = False
        self.turn_right = False
        
        if do_no == 0:
            self.accelerate = True
        elif do_no == 1:
            self.reverse = True
        elif do_no == 2:
            self.turn_left = True
        elif do_no == 3:
            self.turn_right = True
        elif do_no == 4:
            self.accelerate = True
            self.turn_left = True
        elif do_no == 5:
            self.accelerate = True
            self.turn_right = True
        elif do_no == 6:
            self.reverse = True
            self.turn_left = True
        elif do_no == 7:
            self.reverse = True
            self.turn_right = True
        elif do_no == 8:
            pass
        
        self.Game.reward = 0
        
        for i in range(1):
            self.checkInput()
            self.checkSituation()
                    
    def checkInput(self):
        dt = self.dt
        
        if self.turn_left:
            if self.accelerate or self.reverse or self.decrease_acc:
                old_car_direction = self.car_direction
                self.car_direction = self.car_direction.rotate(math.radians(self.turning_speed))
                
                angle_radians = math.acos(old_car_direction.dot(self.car_direction))
                self.car.rotation -= math.degrees(angle_radians)     
                                
        elif self.turn_right:
            if self.accelerate or self.reverse or self.decrease_acc:
                old_car_direction = self.car_direction
                self.car_direction = self.car_direction.rotate(-math.radians(self.turning_speed))
                
                angle_radians = math.acos(old_car_direction.dot(self.car_direction))
                self.car.rotation += math.degrees(angle_radians)
                                
        if self.accelerate:
            self.acc = self.acc + self.acc_step if self.acc < self.max_acc else self.max_acc

            self.car.x += self.car_direction.x * self.acc * dt
            self.car.y += self.car_direction.y * self.acc * dt          
                                    
        elif self.reverse:
            self.rev = self.rev + self.rev_step if self.rev < self.max_rev else self.max_rev
            
            self.car.x -= self.car_direction.x * self.rev * dt
            self.car.y -= self.car_direction.y * self.rev * dt
                                            
    def decreaseAcc(self):
        dt = self.dt
        
        if self.acc >= self.min_acc and self.decrease_acc:    
            self.acc -= self.dec_acc_step
                 
            self.car.x += self.car_direction.x * self.acc * dt
            self.car.y += self.car_direction.y * self.acc * dt
                        
            if self.acc <= self.min_acc:
                self.acc = self.min_acc
                self.decrease_acc = False   
                
    def getCurrentState(self):    
        self.CarHitbox.checkCarCollision()
        self.CarHitbox.checkCarReward()
        
        self.CarLine.checkLineCollision()
        self.CarLine.checkClosestGate()
        
        normalized_vision_vector = [1 - (max(1.0, line) / self.CarLine.long_line) for line in self.CarLine.collision_distances]
        
        normalized_forward_velocity = max(.0, self.acc / self.max_acc)
        normalized_reverse_velocity = max(.0, self.rev / self.max_rev)
        
        normalized_closest_gate = max(.0, self.CarLine.gate_distance)
        
        car_direction = Vec2(self.car_direction.x, self.car_direction.y)
        to_gate_direction = Vec2(self.CarLine.direction_to_gate.x, self.CarLine.direction_to_gate.y)
        normalized_gate_direction = (self.Physic.getAngel(car_direction) - self.Physic.getAngel(to_gate_direction)) % 360
        
        if (normalized_gate_direction > 180):
            normalized_gate_direction = -1 * (360 -normalized_gate_direction)
            
        normalized_gate_direction /= 180 
        
        normalized_state = [*normalized_vision_vector, normalized_forward_velocity, normalized_reverse_velocity, normalized_closest_gate, normalized_gate_direction]
        
        return np.array(normalized_state, dtype=np.float32)

class CarHitbox:
    def __init__(self, Car, Game, Map) -> None:
        self.Car = Car
        self.Map = Map
        self.Game = Game
        self.Physic = Physic()
        
        self.car_hitboxes = []
        self.show_hitbox = True
        
        self.createHitBox()
                        
    def createHitBox(self):
        self.car_hitboxes = []

        opacity = 255 if self.show_hitbox else 0
        self.Car.car.opacity = 50 if self.show_hitbox else 255
        
        width = self.Car.car.width / 2
        
        init_width_line = Vec2(self.Car.car_direction.x, self.Car.car_direction.y) * width
        
        top_left_point = self.Physic.rotate(self.Car.car.x, self.Car.car.y, init_width_line.x, init_width_line.y, math.radians(20))
        top_right_point = self.Physic.rotate(self.Car.car.x, self.Car.car.y, init_width_line.x, init_width_line.y, math.radians(-20))
        bottom_left_point = self.Physic.rotate(self.Car.car.x, self.Car.car.y, init_width_line.x, init_width_line.y, math.radians(160))
        bottom_right_point = self.Physic.rotate(self.Car.car.x, self.Car.car.y, init_width_line.x, init_width_line.y, math.radians(-160))
                
        self.car_hitboxes.append(shapes.Line(top_left_point.x, top_left_point.y, top_right_point.x, top_right_point.y, 2, (0, 0, 0, opacity), batch=batch))
        self.car_hitboxes.append(shapes.Line(bottom_left_point.x, bottom_left_point.y, bottom_right_point.x, bottom_right_point.y, 2, (0, 0, 0, opacity), batch=batch))
        self.car_hitboxes.append(shapes.Line(top_left_point.x, top_left_point.y, bottom_left_point.x, bottom_left_point.y, 2, (0, 0, 0, opacity), batch=batch))
        self.car_hitboxes.append(shapes.Line(top_right_point.x, top_right_point.y, bottom_right_point.x, bottom_right_point.y, 2, (0, 0, 0, opacity), batch=batch))
            
    def checkCarCollision(self):
        self.createHitBox()
        
        for car_box in self.car_hitboxes:
            x1 = car_box.x
            y1 = car_box.y
            x2 = car_box.x2
            y2 = car_box.y2
            
            for wall in self.Map.walls:
                x3 = wall.x
                y3 = wall.y
                x4 = wall.x2
                y4 = wall.y2
                
                collision_point = self.Physic.checkCollision(x1, y1, x2, y2, x3, y3, x4, y4)
                
                if collision_point is not None:
                    self.Game.reward = -100
                    self.Car.is_dead = True
                    
    def checkCarReward(self):
        for car_box in self.car_hitboxes:
            x1 = car_box.x
            y1 = car_box.y
            x2 = car_box.x2
            y2 = car_box.y2
            
            for gate in self.Map.reward_gates:
                x3 = gate.x
                y3 = gate.y
                x4 = gate.x2
                y4 = gate.y2
                
                collision_point = self.Physic.checkCollision(x1, y1, x2, y2, x3, y3, x4, y4)
                
                if collision_point is not None:
                    gate.delete()
                    self.Map.reward_gates.remove(gate)
                    
                    self.Game.reward += 5
                    break
                
class CarLine:
    def __init__(self, Car, Map) -> None:
        self.Car = Car
        self.Map = Map
        self.Physic = Physic()
        
        self.lines = 30
        self.car_lines = []
        self.long_line = 400
        self.show_lines = True
        
        self.collision_distances = []
        self.line_collision_points = []
        
        self.circles = {}
        self.show_collision_circle = True
        
        self.gate_point = {}
        self.gate_distance = 0
        self.line_collision_gate = []
        self.direction_to_gate = Vec2(0, 0)
                        
        self.setupLine()
                        
    def setupLine(self):   
        self.car_lines = []
        
        for i in range(0, self.lines):
            self.car_lines.append(self.createLine(self.Car.car.x, self.Car.car.y, i * (360 / self.lines)))
        
    def createLine(self, x, y, angle):
        opacity = 255 if self.show_lines else 0
        
        x2, y2 = Vec2(self.Car.car_direction.x, self.Car.car_direction.y) * self.long_line
        
        x2 = x + x2
        y2 = y + y2

        angle_radians = math.radians(angle)
        
        new_x2, new_y2 = self.Physic.rotate(x, y, (x2 - x), (y2 - y), angle_radians)
        
        return shapes.Line(x, y, new_x2, new_y2, 1, (255, 255, 0, opacity), batch=batch)

    def checkLineCollision(self):
        self.setupLine()
         
        self.line_collision_points = []
        self.collision_distances = []
        
        for vindex, vision in enumerate(self.car_lines):
            x1 = vision.x
            y1 = vision.y
            x2 = vision.x2
            y2 = vision.y2
            
            closest_point = Vec2(0, 0)
            min_dist = 2 * display_width
            
            for wall in self.Map.walls:
                x3 = wall.x
                y3 = wall.y
                x4 = wall.x2
                y4 = wall.y2
                
                collision_point = self.Physic.checkCollision(x1, y1, x2, y2, x3, y3, x4, y4)
                
                if collision_point is None:
                    continue
                
                if (collision_point.distance(Vec2(self.Car.car.x, self.Car.car.y)) < min_dist):
                    min_dist = collision_point.distance(Vec2(self.Car.car.x, self.Car.car.y))
                    closest_point = collision_point

            if (self.circles.get(vindex) is not None):
                self.circles[vindex].delete()
                del self.circles[vindex]

            if (closest_point.x == 0 and closest_point.y == 0):
                self.collision_distances.append(self.long_line)
                
            if (closest_point.x != 0 and closest_point.y != 0):
                opacity = 255 if self.show_collision_circle else 0
                
                self.circles[vindex] = shapes.Circle(closest_point.x, closest_point.y, 3, color=(255, 0, 0, opacity), batch=batch)
                self.collision_distances.append(closest_point.distance(Vec2(self.Car.car.x, self.Car.car.y)))
                
                vision.x2 = closest_point.x
                vision.y2 = closest_point.y
                
    def checkClosestGate(self):
        self.line_collision_gate = []
        self.gate_point = {}
        
        car_origin = Vec2(self.Car.car.x, self.Car.car.y)
        closest_vision = Vec2(0, 0)
        
        for vision in self.car_lines:
            x1 = vision.x
            y1 = vision.y
            x2 = vision.x2
            y2 = vision.y2
            
            closest_gate = Vec2(0, 0)
            
            for gate in self.Map.reward_gates:
                x3 = gate.x
                y3 = gate.y
                x4 = gate.x2
                y4 = gate.y2
                
                collision_gate = self.Physic.checkCollision(x1, y1, x2, y2, x3, y3, x4, y4)
                
                if (collision_gate is None):
                    continue
                    
                if (collision_gate.distance(car_origin) < closest_gate.distance(car_origin)):
                    closest_gate = collision_gate
            
            if (closest_gate.x != 0 and closest_gate.y != 0):
                if (closest_gate.distance(car_origin) < closest_vision.distance(car_origin)):
                    closest_vision = closest_gate
                    
        if (closest_vision.x != 0 and closest_vision.y != 0):
            self.gate_point = shapes.Circle(closest_vision.x, closest_vision.y, 3, color=(255, 0, 255), batch=batch)
            self.gate_distance = closest_vision.distance(Vec2(self.Car.car.x, self.Car.car.y))
            self.direction_to_gate = closest_vision - car_origin

                            
class Map:
    def __init__(self) -> None:        
        circuit_image = pyglet.image.load(images_dir + 'circuit.jpg')
        
        self.circuit_sprite = pyglet.sprite.Sprite(circuit_image)
        
        self.circuit_sprite.x = 0
        self.circuit_sprite.y = 0
        self.circuit_sprite.opacity = 255
        
        self.drawing_mode = False
        
        self.show_map_line = True
        self.walls = []
        self.temp_wall = {}
        
        self.show_map_gate = True
        self.reward_gates = []
        self.temp_gate = {}
        
        self.type_line = 'wall'
        
        self.create_line = False
        
        self.loadWalls()
        self.loadGates()
        
    def resetRewardGate(self):
        self.reward_gates = []

        self.loadGates()
                        
    def draw(self):
        self.circuit_sprite.draw()
        batch.draw()
        
    def switchTypeLine(self):
        if self.drawing_mode:
            self.type_line = 'wall' if self.type_line == 'gate' else 'gate'
        
    def createLine(self, x, y):
        if self.drawing_mode:
            self.create_line = not self.create_line
            
            if self.type_line == 'wall':
                self.drawWall(x, y)
            else:
                self.drawRewardGate(x, y)
                    
    def saveLine(self):
        if self.drawing_mode:
            if (self.type_line == 'wall' and type(self.temp_wall) is pyglet.shapes.Line):
                self.walls.append(self.temp_wall)
                self.temp_wall = {}

                self.saveWalls()
                
            elif (self.type_line == 'gate' and type(self.temp_gate) is pyglet.shapes.Line):
                self.reward_gates.append(self.temp_gate)
                self.temp_gate = {}
                
                self.saveGates()
            
    def cancelLine(self):
        if self.drawing_mode:
            if (self.type_line == 'wall' and type(self.temp_wall) is pyglet.shapes.Line):
                self.temp_wall.delete()
                self.temp_wall = {}
                
            elif (self.type_line == 'gate' and type(self.temp_gate) is pyglet.shapes.Line):
                self.temp_gate.delete()
                self.temp_gate = {}
            
    def undoLastLine(self):
        if self.drawing_mode:
            if (self.type_line == 'wall'):
                self.walls[-1].delete()
                self.walls.pop()
                
                self.saveWalls()                
                
            if (self.type_line == 'gate'):
                self.reward_gates[-1].delete()
                self.reward_gates.pop()
                
                self.saveGates()
        
    def drawWall(self, x, y):
        if self.create_line:
            self.temp_wall = self.createWalls(x, y, x, y)
        else:
            if (type(self.temp_wall) is pyglet.shapes.Line):
                self.temp_wall.x2 = x
                self.temp_wall.y2 = y
        
    def createWalls(self, x, y, x2, y2):
        opacity = 255 if self.show_map_line else 0
        return shapes.Line(x, y, x2, y2, 2, (0, 0, 255, opacity), batch=batch)
    
    def drawRewardGate(self, x, y):
        if self.create_line:
            self.temp_gate = self.createRewardGate(x, y, x, y)
        else:
            if (type(self.temp_gate) is pyglet.shapes.Line):
                self.temp_gate.x2 = x
                self.temp_gate.y2 = y
    
    def createRewardGate(self, x, y, x2, y2):
        opacity = 255 if self.show_map_gate else 0
        return shapes.Line(x, y, x2, y2, 2, (0, 255, 255, opacity), batch=batch)
    
    def loadWalls(self):
        with open('map_walls.json', 'r') as file:
            walls_coor = json.load(file)
            
            for wall in list(walls_coor):
                self.walls.append(self.createWalls(wall['x'], wall['y'], wall['x2'], wall['y2']))
                
    def loadGates(self):
        with open('map_gates.json', 'r') as file:
            gates_coor = json.load(file)
            
            for gindex, gate in enumerate(list(gates_coor)):
                reward_gate = self.createRewardGate(gate['x'], gate['y'], gate['x2'], gate['y2'])
                self.reward_gates.append(reward_gate)
            
    def saveWalls(self):
        walls_coor = map( lambda wall: { 'x': wall.x, 'y': wall.y, 'x2': wall.x2, 'y2': wall.y2 }, self.walls)
        walls = json.dumps(list(walls_coor), indent=1)
        
        with open('map_walls.json', 'w') as file:
            file.write(walls)
            
    def saveGates(self):
        gates_coor = map( lambda gate: { 'x': gate.x, 'y': gate.y, 'x2': gate.x2, 'y2': gate.y2 }, self.reward_gates)
        gates = json.dumps(list(gates_coor), indent=1)
        
        with open('map_gates.json', 'w') as file:
            file.write(gates)