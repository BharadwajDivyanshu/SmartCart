import { Router } from 'express';
const router = Router();
import { getRecommendations } from '../controllers/recommendationController.js';

// Optional middleware for authentication
// const { protect } = require('../middleware/authMiddleware');
// router.use(protect);

router.post('/', getRecommendations);

export default router;