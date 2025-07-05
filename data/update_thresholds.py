import mysql.connector
import argparse
import os
from typing import List

def connect_to_database(database: str) -> mysql.connector.MySQLConnection:
    """
    Establish a connection to the specified MySQL database.

    Args:
        database (str): The name of the database to connect to.

    Returns:
        mysql.connector.MySQLConnection: The MySQL connection object.
    """
    return mysql.connector.connect(
        host='192.168.10.42',
        port=3377,
        user='jcontramestre',
        password='904OBol6PY0mcIpN',
        database=database
    )

def get_variant_id(customer_variant: str) -> int:
    """
    Retrieve the ID of a variant from the database based on its name.

    Args:
        customer_variant (str): The name of the variant to look up.

    Returns:
        int: The ID of the variant if found.
    """
    query = """
        SELECT idVariant
        FROM Variants
        WHERE variantName = %s
    """
    with connect_to_database('GapfillerRobot') as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (customer_variant,))
            result = cursor.fetchone()
    if result:
        return result[0]
    raise ValueError(f"No variant found with name {customer_variant}")

def update_variant_thresholds(id_variant: int, variant_thresholds: str) -> None:
    """
    Update the variant thresholds in the database for the specified variant ID.

    Args:
        id_variant (int): The ID of the variant to update.
        variant_thresholds (str): The new thresholds to set.
    """
    query = """
        UPDATE Variants
        SET variantThresholds = %s
        WHERE idVariant = %s
    """
    with connect_to_database('GapfillerRobot') as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (variant_thresholds, id_variant))
            conn.commit()

def generate_variant_thresholds(matrix: List[List[float]]) -> str:
    """
    Generate a formatted string of variant thresholds from a 2D matrix.

    Args:
        matrix (List[List[float]]): The 2D matrix to convert.

    Returns:
        str: The formatted thresholds as a multi-line string.
    """
    return "\n".join([f"{int(row[0])},{row[1]}" for row in matrix])

def main(customer_variant: str, matrix: List[List[float]]) -> str:
    """
    Main function to update the variant thresholds for a given customer variant.

    Args:
        customer_variant (str): The name of the customer variant to update.
        matrix (List[List[float]]): The 2D matrix to convert to thresholds.

    Returns:
        str: A message indicating the success or failure of the operation.
    """
    try:
        id_variant = get_variant_id(customer_variant)
        variant_thresholds = generate_variant_thresholds(matrix)
        update_variant_thresholds(id_variant, variant_thresholds)
        return f"Variant {customer_variant} updated successfully."
    except ValueError as e:
        return str(e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update variant thresholds for a given customer variant.')
    parser.add_argument('customer_variant', type=str, help='Customer Variant to update')
    parser.add_argument('matrix', type=list, help='2D matrix to be converted to variantThresholds')
    args = parser.parse_args()
    result = main(args.customer_variant, args.matrix)
    print(result)
