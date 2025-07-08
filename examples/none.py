# Test if None is supported as a literal

def test() -> int:
    return 5

result: int = 0

result = test()
print(result)
