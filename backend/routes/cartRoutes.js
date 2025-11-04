import { Router } from 'express';
const router = Router();
import { getCart, addItemToCart, updateCartItemQuantity, removeCartItem } from '../controllers/cartController.js';
// Note: The 'protect' authMiddleware would be applied in your main server file before these routes.

// Maps GET /api/cart to the getCart controller function
router.get('/', getCart);

// Maps POST /api/cart to the addItemToCart controller function
router.post('/', addItemToCart);
router.put('/', updateCartItemQuantity);
router.delete('/:productId', removeCartItem);

export default router;