import express, { json } from 'express';
import cors from 'cors';
import 'dotenv/config';

import authRoutes from './routes/authRoutes.js';
import productRoutes from './routes/productRoutes.js';
import cartRoutes from './routes/cartRoutes.js';
import recommendationRoutes from './routes/recommendationRoutes.js';
import { protect } from './middleware/authMiddleware.js';

const app = express();

// Middleware
app.use(cors());
app.use(json());

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/products', productRoutes);
app.use('/api/cart', protect, cartRoutes);
app.use('/api/recommendations', protect, recommendationRoutes);

// Centralized Error Handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send('Something broke!');
});

const PORT = process.env.PORT || 8000;
app.listen(PORT, () => {
  console.log(`Node.js server running on http://localhost:${PORT}`);
});