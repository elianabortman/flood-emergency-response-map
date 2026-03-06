class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Point(x = {self.x}, y = {self.y})"

    def to_tuple(self):
        return self.x, self.y
