import axios from 'axios';
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

const FLASK_ML_SERVICE_URL = process.env.FLASK_URL || 'http://127.0.0.1:5000';

/**
 * Fetches a generic list of popular products for new users with empty carts.
 */

async function getPopularProducts() {
  try {
    const products = await prisma.product.findMany({
      // ADD THIS 'where' BLOCK
      where: {
        imageUrl: {
          not: null, // This ensures imageUrl is not null
        },
      },
      take: 12,
      orderBy: {
        healthFactorScore: 'desc',
      },
    });
    return products;
  } catch (error) {
    console.error('Error fetching popular products:', error.message);
    return [];
  }
}

/**
 * @desc    Get AI-powered product recommendations
 * @route   POST /api/recommendations
 * @access  Private
 */
const getRecommendations = async (req, res) => {
    const { gamma } = req.body;
    const user = req.user;
    console.log(user.instacartUserId)

    try {
        // 1. Get the user's current basket from the database
        const cart = await prisma.cart.findUnique({
            where: { userId: user.id },
            select: { items: { select: { productId: true } } }
        });
        const basketIds = cart ? cart.items.map(item => item.productId) : [];

        // --- (FIXED) NEW USER LOGIC ---
        // Scenario 1: User is new (no instacartUserId) AND their basket is empty.
        if (!user.instacartUserId && basketIds.length === 0) {
            console.log(`[Node.js] New user ${user.id} has empty cart. Serving popular products.`);
            const popularProducts = await getPopularProducts();
            return res.json(popularProducts);
        }
        // --- (END OF FIX) ---

        // At this point, the user is either:
        // A) An existing user (with user.instacartUserId)
        // B) A new user who has items in their basket (session-based recommendation)

        // 2. Call the external Flask ML service
        const mlResponse = await axios.post(`${FLASK_ML_SERVICE_URL}/recommend`, {
            // Send the instacartUserId (which will be 'null' for new users)
            user_id: user.instacartUserId, 
            basket_ids: basketIds,
            gamma: gamma
        });

        const recommendedIds = mlResponse.data.recommendations;

        if (!recommendedIds || recommendedIds.length === 0) {
            return res.json([]);
        }

        // 3. Fetch full product details from our database
        const recommendedProducts = await prisma.product.findMany({
            where: {
                productId: { in: recommendedIds }
            }
        });
        
        // 4. Sort the products to match the order from the ML service
        const sortedProducts = recommendedIds.map(id => 
            recommendedProducts.find(p => p.productId === id)
        ).filter(Boolean); 

        // 5. Send the final list to the frontend
        res.json(sortedProducts);

    } catch (error) {
        console.error("Error getting recommendations:", error.message);
        res.status(500).json({ message: "Could not fetch recommendations", error: error.message });
    }
};

export {
    getRecommendations,
};