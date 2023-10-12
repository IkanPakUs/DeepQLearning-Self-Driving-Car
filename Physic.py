from pyglet.math import Vec2
import math

class Physic:
    def checkCollision(self, x1, y1, x2, y2, x3, y3, x4, y4):
        if (((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)) != 0):
            uA = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1))
            uB = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1))

            if 0 <= uA <= 1 and 0 <= uB <= 1:
                intersect_x = x1 + (uA * (x2 - x1))
                intersect_y = y1 + (uA * (y2 - y1))
                
                return Vec2(intersect_x, intersect_y)
            
        return None
    
    def rotate(self, origin_x, origin_y, x, y, angle_radians):
        theta_cos = math.cos(angle_radians)
        theta_sin = math.sin(angle_radians)
        
        new_x = origin_x + theta_cos * x - theta_sin * y
        new_y = origin_y + theta_sin * x + theta_cos * y
        
        return Vec2(new_x, new_y)
    
    def getAngel(self, vec):
        return math.degrees(math.atan2(vec.y, vec.x))
