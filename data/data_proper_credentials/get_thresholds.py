import mysql.connector
import argparse


def connect_to_database(database):
    return mysql.connector.connect(
        host='192.168.10.42',
        port=3377,
        user='jcontramestre',
        password='904OBol6PY0mcIpN',
        database=database
    )

def get_variant_id(customer_variant):
    query = """
        SELECT idVariant
        FROM Variants
        WHERE variantName = %s
    """
    with connect_to_database('GapfillerRobot') as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (customer_variant,))
            result = cursor.fetchone()
    return result[0] if result else None

def get_variant_thresholds(id_variant):
    query = """
        SELECT variantThresholds
        FROM Variants
        WHERE idVariant = %s
    """
    with connect_to_database('GapfillerRobot') as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (id_variant,))
            result = cursor.fetchone()
    return result[0] if result else None

def extract_thresholds(variant_thresholds_text):
    lines = variant_thresholds_text.strip().split('\n')
    second_elements = [str(line.split(',')[1]) for line in lines]
    return second_elements

def main(customer_variant):
    id_variant = get_variant_id(customer_variant)
    if id_variant:
        variant_thresholds_text = get_variant_thresholds(id_variant)
        if variant_thresholds_text:
            thresholds_array = extract_thresholds(variant_thresholds_text)
            return thresholds_array
        else:
            return []  # Return an empty list if no thresholds found
    else:
        return []  # Return an empty list if the variant is not found

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Retrieve thresholds for a given customer variant.')
    parser.add_argument('customer_variant', type=str, help='Customer Variant to retrieve thresholds for')
    args = parser.parse_args()
    thresholds_array = main(args.customer_variant)
    print(thresholds_array)