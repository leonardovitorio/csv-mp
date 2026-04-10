/**
 * CSV-MP Simple API Usage Examples (TypeScript)
 */

import { 
  deserialize, 
  toCsvMp, 
  fromCsvMp, 
  readCsvMp, 
  writeCsvMp 
} from './src/index';

// Example 1: Simple Serialization - Objects to CSV-MP
const userData = {
  User: [
    { id: 1, name: 'Alice', email: 'alice@example.com', age: 30 },
    { id: 2, name: 'Bob', email: 'bob@example.com', age: 25 },
    { id: 3, name: 'Carol', email: 'carol@example.com', age: 35 }
  ],
  Order: [
    { orderId: 101, userId: 1, product: 'Laptop', quantity: 1 },
    { orderId: 102, userId: 2, product: 'Mouse', quantity: 2 }
  ]
};

// Convert objects to CSV-MP format
const csvMpContent = toCsvMp(userData, {
  author: 'my-app',
  version: '1.0'
});

console.log('CSV-MP Content:');
console.log(csvMpContent);

// Example 2: Simple Deserialization - CSV-MP to Objects
const parsedData = deserialize<{ User: any[], Order: any[] }>(csvMpContent);

console.log('\nParsed Users:');
parsedData.User.forEach(user => {
  console.log(`  - ${user.name} (${user.email})`);
});

console.log('\nParsed Orders:');
parsedData.Order.forEach(order => {
  console.log(`  - Order ${order.orderId}: ${order.product} x${order.quantity}`);
});

// Example 3: File I/O (Node.js)
async function fileExample() {
  // Write to file
  await writeCsvMp('example.csv.mp', userData, {
    author: 'my-app',
    version: '1.0',
    description: 'User and order data'
  });
  
  // Read from file
  const loadedData = await readCsvMp('example.csv.mp');
  console.log('\nLoaded from file:', loadedData);
}

// Example 4: Round-trip conversion
function roundTripExample() {
  const original = {
    Product: [
      { sku: 'P001', name: 'Widget', price: 9.99, inStock: true },
      { sku: 'P002', name: 'Gadget', price: 19.99, inStock: false }
    ]
  };
  
  // Serialize
  const serialized = toCsvMp(original);
  
  // Deserialize
  const deserialized = fromCsvMp(serialized);
  
  console.log('\nRound-trip successful:', 
    JSON.stringify(original.Product) === JSON.stringify(deserialized.Product));
}

// Run examples
fileExample().catch(console.error);
roundTripExample();
