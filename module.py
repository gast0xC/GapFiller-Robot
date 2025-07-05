def scale_array(x, slope):
    OFFSET = 0  # or whatever value you need
    result = []
    for item in x:
        result.append(item * slope + OFFSET)
    return result
