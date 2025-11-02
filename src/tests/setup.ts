import dotenv from 'dotenv';

// Load environment variables for tests
dotenv.config({ path: 'env.test' });
dotenv.config(); // Fallback to main .env

// Set test environment
process.env.NODE_ENV = 'test';
process.env.LOG_LEVEL = 'debug';
