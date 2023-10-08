from pyglet.math import Vec2


new_line_x, new_line_y = (Vec2(3, 3).normalize() * 1)
print(new_line_x, new_line_y)
print(Vec2(6, 6) + Vec2(new_line_x, new_line_y))