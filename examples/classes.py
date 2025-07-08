class Point(object):
    x: int = 0
    y: int = 0
    
    def __init__(self: "Point", x: int, y: int):
        self.x = x
        self.y = y
    
    def distance_from_origin(self: "Point") -> int:
        return self.x * self.x + self.y * self.y

class ColorPoint(Point):
    color: str = "red"
    
    def __init__(self: "ColorPoint", x: int, y: int, color: str):
        self.x = x
        self.y = y 
        self.color = color

p: Point = None
# p = Point()
# p.__init__(3, 4)

# Complex ChocoPy program with various features

# Global variables
numbers: [int] = [1, 2, 3, 4, 5]
message: str = "Hello, ChocoPy!"

def sum_list(items: [int]) -> int:
    total: int = 0
    for item in items:
        total = total + item
    return total

def is_even(n: int) -> bool:
    return n % 2 == 0

def filter_evens(items: [int]) -> [int]:
    result: [int] = []
    for item in items:
        if is_even(item):
            result = result + [item]
    return result

def main():
    total: int = sum_list(numbers)
    evens: [int] = filter_evens(numbers)
    
    print(total)
    print(len(evens))
    
    max_val: int = 10 if total > 20 else 5
    print(max_val)

main()