import { Router } from 'express';
const router = Router();
import { getAllProducts } from '../controllers/productController.js';

router.get('/', getAllProducts);

export default router;