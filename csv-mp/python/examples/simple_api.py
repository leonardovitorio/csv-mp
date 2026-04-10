"""
CSV-MP Simple API Usage Examples (Python)
"""

from src import (
    deserialize,
    to_csv_mp,
    from_csv_mp,
    read_csv_mp,
    write_csv_mp
)

# Example 1: Simple Serialization - Objects to CSV-MP
user_data = {
    'User': [
        {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'age': 30},
        {'id': 2, 'name': 'Bob', 'email': 'bob@example.com', 'age': 25},
        {'id': 3, 'name': 'Carol', 'email': 'carol@example.com', 'age': 35}
    ],
    'Order': [
        {'orderId': 101, 'userId': 1, 'product': 'Laptop', 'quantity': 1},
        {'orderId': 102, 'userId': 2, 'product': 'Mouse', 'quantity': 2}
    ]
}

# Convert objects to CSV-MP format
csv_mp_content = to_csv_mp(user_data, {
    'author': 'my-app',
    'version': '1.0'
})

print('CSV-MP Content:')
print(csv_mp_content)

# Example 2: Simple Deserialization - CSV-MP to Objects
parsed_data = deserialize(csv_mp_content)

print('\nParsed Users:')
for user in parsed_data['User']:
    print(f"  - {user['name']} ({user['email']})")

print('\nParsed Orders:')
for order in parsed_data['Order']:
    print(f"  - Order {order['orderId']}: {order['product']} x{order['quantity']}")

# Example 3: File I/O
def file_example():
    # Write to file
    write_csv_mp('example.csv.mp', user_data, {
        'author': 'my-app',
        'version': '1.0'
    })
    
    # Read from file
    loaded_data = read_csv_mp('example.csv.mp')
    print('\nLoaded from file:', loaded_data)

# Example 4: Round-trip conversion
def round_trip_example():
    original = {
        'Product': [
            {'sku': 'P001', 'name': 'Widget', 'price': 9.99, 'inStock': True},
            {'sku': 'P002', 'name': 'Gadget', 'price': 19.99, 'inStock': False}
        ]
    }
    
    # Serialize
    serialized = to_csv_mp(original)
    
    # Deserialize
    deserialized = from_csv_mp(serialized)
    
    print('\nRound-trip successful:', 
          original['Product'] == deserialized['Product'])

# Run examples
if __name__ == '__main__':
    file_example()
    round_trip_example()
