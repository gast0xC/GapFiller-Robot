mapping = {
    '3AH': '41H',
    '3BH': '42H',
    '3CH': '43H',
    '3DH': '44H',
    '3EH': '45H',
    '3FH': '46H'
}

def convert_hex_to_custom_format(hex_string):
    hex_string  = hex_string[2:]
    #integer_value = int(hex_string, 16)
    result = ''.join(format(int('3' + char, 16), 'x') + 'H' for char in hex_string)  
    print(result)
    pairs = [result.upper()[i:i+3] for i in range(0, len(result), 3)]
    transformed_pairs = [mapping.get(pair, pair) for pair in pairs]
    transformed_string = ''.join(transformed_pairs)
    return transformed_string

decimal = 244
decimal_hex = hex(decimal)
format = convert_hex_to_custom_format(decimal_hex)
print(format)


# For acc, dcc, vel should be 4 bytes. For position should be 3 bytes
# beware of missing bytes in the high significant zone