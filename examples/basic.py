# Basic ChocoPy program
# Variable definitions (must use literals only)
x: int = 5
y: int = 10
result: int = 0
fact: int = 1

# Function definitions
def add(a: int, b: int) -> int:
    return a + b

def factorial(n: int) -> int:
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

# Statements (can use expressions and function calls)
result = add(x, y)
fact = factorial(5)
print(result)
print(fact)
