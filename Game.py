import pyglet
import math
import numpy as np
from Physic import Physic
from pyglet import shapes
from pyglet.math import Vec2

images_dir = 'images/'
display_width = 1920
display_height = 960
batch = pyglet.graphics.Batch()

class Car:
    def __init__(self, Map) -> None:
        car_image = pyglet.resource.image(images_dir + 'car.png')
        car_image.anchor_x = car_image.width / 2
        car_image.anchor_y = car_image.height / 2
        
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

        self.Map = Map
        self.CarHitbox = CarHitbox(self, Map)
        self.CarLine = CarLine(self, Map)
        self.Physic = Physic()

        self.min_acc = 50
        self.acc = self.min_acc
        self.acc_step = 5
        self.max_acc = 300
        
        self.decrease_acc = False
        self.dec_acc_step = 10
        
        self.min_rev = self.min_acc / 2
        self.rev = self.min_rev
        self.rev_step = 2
        self.max_rev = self.max_acc / 2
        
        self.turning_speed = 3 # Turning speed rate from 1 to 3
        
        self.car_direction = Vec2(-1, 0)
        
        self.car_collision = False
        
    def reset(self):
        if (self.car_collision):
            self.CarLine = CarLine(self, self.Map)
            self.CarHitbox = CarHitbox(self, self.Map)
            
            self.car.width = 40
            self.car.height = 20
            self.car.rotation = -180
            self.car.x = 300
            self.car.y = 120
            
            self.min_acc = 0
            self.acc = self.min_acc
            self.acc_step = 5
            self.max_acc = 200
            
            self.decrease_acc = False
            self.dec_acc_step = 10
            
            self.min_rev = self.min_acc / 2
            self.rev = self.min_rev
            self.rev_step = 2
            self.max_rev = self.max_acc / 2
            
            self.turning_speed = 3 # Turning speed rate from 1 to 3
            
            self.car_direction = Vec2(-1, 0)
        
    def updateCarLocation(self, dt):
        self.checkInput(dt)
        self.decreaseAcc(dt)
        
        self.CarLine.checkLineCollision()
            
    def checkInput(self, dt):
        if self.turn_left:
            if self.accelerate or self.reverse or self.decrease_acc:
                old_car_direction = self.car_direction
                self.car_direction = self.car_direction.rotate(math.radians(self.turning_speed))
                
                angle_radians = math.acos(old_car_direction.dot(self.car_direction))
                self.car.rotation -= math.degrees(angle_radians)
                
                self.CarHitbox.updateBoxRotation(angle_radians)
                self.CarLine.updateLineRotation(angle_radians)
                    
                
        elif self.turn_right:
            if self.accelerate or self.reverse or self.decrease_acc:
                old_car_direction = self.car_direction
                self.car_direction = self.car_direction.rotate(-math.radians(self.turning_speed))
                
                angle_radians = math.acos(old_car_direction.dot(self.car_direction))
                self.car.rotation += math.degrees(angle_radians)
                
                self.CarHitbox.updateBoxRotation(-angle_radians)
                self.CarLine.updateLineRotation(-angle_radians)
                
        if self.accelerate:
            self.acc = self.acc + self.acc_step if self.acc < self.max_acc else self.max_acc

            self.car.x += self.car_direction.x * self.acc * dt
            self.car.y += self.car_direction.y * self.acc * dt           
            
            self.CarHitbox.updateBoxLocation(self.car_direction.x * self.acc * dt, self.car_direction.y * self.acc * dt) 
            
        elif self.reverse:
            self.rev = self.rev + self.rev_step if self.rev < self.max_rev else self.max_rev
            
            self.car.x -= self.car_direction.x * self.rev * dt
            self.car.y -= self.car_direction.y * self.rev * dt
            
            self.CarHitbox.updateBoxLocation(-self.car_direction.x * self.rev * dt, -self.car_direction.y * self.rev * dt) 
            
        self.CarLine.updateLinePosition(self.car.x, self.car.y)  
        
    def decreaseAcc(self, dt):
        if self.acc >= self.min_acc and self.decrease_acc:    
            self.acc -= self.dec_acc_step
                 
            self.car.x += self.car_direction.x * self.acc * dt
            self.car.y += self.car_direction.y * self.acc * dt
            
            self.CarHitbox.updateBoxLocation(self.car_direction.x * self.acc * dt, self.car_direction.y * self.acc * dt) 
            self.CarLine.updateLinePosition(self.car.x, self.car.y)
            
            if self.acc <= self.min_acc:
                self.acc = self.min_acc
                self.decrease_acc = False
                
class CarHitbox:
    def __init__(self, Car, Map) -> None:
        self.Car = Car
        self.Map = Map
        self.Physic = Physic()
        
        self.car_hitboxes = []
        self.show_hitbox = False
        
        self.createHitBox()
        
    def createHitBox(self):
        opacity = 255 if self.show_hitbox else 0
        
        width = self.Car.car.width / 2.2
        height = self.Car.car.height / 3
        
        left_point = self.Car.car.x - width
        right_point = self.Car.car.x + width
        top_point = self.Car.car.y + height
        bottom_point = self.Car.car.y - height
        
        self.car_hitboxes.append(shapes.Line(left_point, top_point, right_point, top_point, 1, (0, 0, 0, opacity), batch=batch))
        self.car_hitboxes.append(shapes.Line(left_point, bottom_point, right_point, bottom_point, 1, (0, 0, 0, opacity), batch=batch))
        self.car_hitboxes.append(shapes.Line(left_point, top_point, left_point, bottom_point, 1, (0, 0, 0, opacity), batch=batch))
        self.car_hitboxes.append(shapes.Line(right_point, top_point, right_point, bottom_point, 1, (0, 0, 0, opacity), batch=batch))
        
    def updateBoxLocation(self, x, y):
        for hitbox in self.car_hitboxes:
            hitbox.x += x
            hitbox.y += y
            hitbox.x2 += x
            hitbox.y2 += y
            
        self.checkCarCollision()
            
    def updateBoxRotation(self, angle_radians):
        for car_box in self.car_hitboxes:
            x1 = car_box.x
            y1 = car_box.y
            x2 = car_box.x2
            y2 = car_box.y2
            
            origin_x1 = (x1 - self.Car.car.x)
            origin_y1 = (y1 - self.Car.car.y)
            origin_x2 = (x2 - self.Car.car.x)
            origin_y2 = (y2 - self.Car.car.y)
            
            theta_cos = math.cos(angle_radians)
            theta_sin = math.sin(angle_radians)
            
            new_x = self.Car.car.x + theta_cos * origin_x1 - theta_sin * origin_y1
            new_y = self.Car.car.y + theta_sin * origin_x1 + theta_cos * origin_y1
            new_x2 = self.Car.car.x + theta_cos * origin_x2 - theta_sin * origin_y2
            new_y2 = self.Car.car.y + theta_sin * origin_x2 + theta_cos * origin_y2
            
            car_box.x, car_box.y = Vec2(new_x, new_y)
            car_box.x2, car_box.y2 = Vec2(new_x2, new_y2)
            
    def checkCarCollision(self):
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
                    self.Car.reset()
                
class CarLine:
    def __init__(self, Car, Map) -> None:
        self.Car = Car
        self.Map = Map
        self.Physic = Physic()
        
        self.car_lines = []
        self.long_line = 300
        self.show_lines = False
        
        self.circles = {}
        self.show_collision_circle = True
        
        self.setupLine()
        
    def setupLine(self):
        lines = 30
        
        for i in range(0, lines):
            self.car_lines.append(self.createLine(300, 120, i * (360 / lines)))
        
    def createLine(self, x, y, angle):
        opacity = 255 if self.show_lines else 0
        
        x2, y2 = Vec2(0, 1) * self.long_line
        
        x2 = x + x2
        y2 = y + y2

        angle_radians = math.radians(angle)
        
        theta_cos = math.cos(angle_radians)
        theta_sin = math.sin(angle_radians)
        
        new_x2 = x + theta_cos * (x2 - x) - theta_sin * (y2 - y)
        new_y2 = y + theta_sin * (x2 - x) + theta_cos * (y2 - y)
        
        return shapes.Line(x, y, new_x2, new_y2, 1, (255, 255, 0, opacity), batch=batch)
        
    def updateLinePosition(self, x, y):
        for car_line in self.car_lines:
            diff_x = car_line.x2 - car_line.x
            diff_y = car_line.y2 - car_line.y
            
            car_line.x = x
            car_line.y = y
            
            car_line.x2 = car_line.x + diff_x
            car_line.y2 = car_line.y + diff_y
            
    def updateLineRotation(self, angle_radians):
        for car_line in self.car_lines:
            origin_x = (car_line.x2 - car_line.x)
            origin_y = (car_line.y2 - car_line.y)
            
            theta_cos = math.cos(angle_radians)
            theta_sin = math.sin(angle_radians)
            
            new_x2 = car_line.x + theta_cos * origin_x - theta_sin * origin_y
            new_y2 = car_line.y + theta_sin * origin_x + theta_cos * origin_y
            
            car_line.x2, car_line.y2 = Vec2(new_x2, new_y2)
            
    def checkLineCollision(self):
        self.line_collision_points = []
        
        for vindex, vision in enumerate(self.car_lines):
            x1 = vision.x
            y1 = vision.y
            x2 = vision.x2
            y2 = vision.y2
            
            closest_point = Vec2(0, 0)
            
            for wall in self.Map.walls:
                x3 = wall.x
                y3 = wall.y
                x4 = wall.x2
                y4 = wall.y2
                
                collision_point = self.Physic.checkCollision(x1, y1, x2, y2, x3, y3, x4, y4)
                
                if collision_point is None:
                    continue
                
                if (collision_point.distance(Vec2(self.Car.car.x, self.Car.car.y)) < closest_point.distance(Vec2(self.Car.car.x, self.Car.car.y))):
                    closest_point = collision_point

            if (self.circles.get(vindex) is not None):
                if (type(self.circles[vindex]) == pyglet.shapes.Circle):
                    self.circles[vindex].delete()
                    del self.circles[vindex]
            
            if (closest_point.x != 0 and closest_point.y != 0):
                opacity = 255 if self.show_collision_circle else 0
                
                self.circles[vindex] = shapes.Circle(closest_point.x, closest_point.y, 3, color=(255, 0, 0, opacity), batch=batch)
                            
class Map:
    def __init__(self) -> None:        
        circuit_image = pyglet.image.load(images_dir + 'circuit.jpg')
        
        self.circuit_sprite = pyglet.sprite.Sprite(circuit_image, batch=batch)
        
        self.circuit_sprite.x = 0
        self.circuit_sprite.y = 0
        
        self.walls = []
                
        self.setWalls()
        
    def draw(self):
        batch.draw()
        
    def setWalls(self):
        self.walls.append(self.createWalls(410, 160, 250, 160))
        self.walls.append(self.createWalls(250, 160, 230, 163))
        self.walls.append(self.createWalls(230, 163, 210, 169))
        self.walls.append(self.createWalls(210, 169, 190, 182))
        self.walls.append(self.createWalls(190, 182, 183, 187))
        self.walls.append(self.createWalls(183, 187, 125, 245))
        self.walls.append(self.createWalls(125, 245, 115, 258))
        self.walls.append(self.createWalls(115, 258, 105, 278))
        self.walls.append(self.createWalls(105, 278, 99, 295))
        self.walls.append(self.createWalls(99, 295, 97, 310))
        self.walls.append(self.createWalls(98, 310, 98, 704))
        self.walls.append(self.createWalls(98, 704, 100, 720))
        self.walls.append(self.createWalls(100, 720, 110, 750))
        self.walls.append(self.createWalls(110, 750, 185, 830))
        self.walls.append(self.createWalls(185, 830, 215, 850))
        self.walls.append(self.createWalls(215, 850, 230, 853))
        self.walls.append(self.createWalls(230, 853, 250, 855))
        self.walls.append(self.createWalls(250, 855, 1665, 855))
        # self.walls.append(shapes.Line(1813, 720, 1813, 310, 1, (255, 255, 255), batch=batch))
        # self.walls.append(shapes.Line(1420, 160, 1670, 160, 1, (255, 255, 255), batch=batch))
        # self.walls.append(shapes.Line(1302, 195, 1090, 195, 1, (255, 255, 255), batch=batch))
        # self.walls.append(shapes.Line(974, 160, 875, 160, 1, (255, 255, 255), batch=batch))
        
    def createWalls(self, x, y, x2, y2):
        return shapes.Line(x, y, x2, y2, 1, (255, 255, 255), batch=batch)