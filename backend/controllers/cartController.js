import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

/**
 * @desc    Get the current user's cart contents
 * @route   GET /api/cart
 * @access  Private
 */
const getCart = async (req, res) => {
    try {
        const cart = await prisma.cart.findUnique({
            where: { userId: req.user.id },
            include: { 
                items: { 
                    include: { product: true }, 
                    orderBy: { product: { productName: 'asc' }} 
                } 
            }
        });
        // Return the items array, or an empty array if no cart/items exist
        res.json(cart?.items || []);
    } catch (error) {
        console.error("Error fetching cart:", error);
        res.status(500).json({ message: "Could not fetch cart", error: error.message });
    }
};

/**
 * @desc    Add an item to the user's cart
 * @route   POST /api/cart
 * @access  Private
 */
const addItemToCart = async (req, res) => {
    const { productId, quantity } = req.body;

    if (!productId || !quantity || quantity < 1) {
        return res.status(400).json({ message: "Invalid request data. productId and quantity are required." });
    }

    try {
        // Find the user's cart
        const cart = await prisma.cart.findUnique({ where: { userId: req.user.id } });
        if (!cart) {
            return res.status(404).json({ message: "User cart not found." });
        }
        
        // Check if the item already exists in the cart
        const existingItem = await prisma.cartItem.findFirst({
            where: { cartId: cart.id, productId: productId }
        });

        if (existingItem) {
            // If it exists, increment the quantity
            await prisma.cartItem.update({
                where: { id: existingItem.id },
                data: { quantity: { increment: quantity } }
            });
        } else {
            // If it doesn't exist, create a new cart item
            await prisma.cartItem.create({
                data: { 
                    cartId: cart.id, 
                    productId: productId, 
                    quantity: quantity 
                }
            });
        }
        
        res.status(200).json({ message: "Item added to cart successfully" });
    } catch (error) {
        console.error("Error adding item to cart:", error);
        res.status(500).json({ message: "Could not add item to cart", error: error.message });
    }
};

// --- NEW FUNCTION ---
/**
 * @desc    Update an item's quantity in the cart
 * @route   PUT /api/cart
 * @access  Private
 */
const updateCartItemQuantity = async (req, res) => {
    const { productId, quantity } = req.body;

    // Validate input
    if (!productId || typeof quantity === 'undefined' || quantity < 0) {
        return res.status(400).json({ message: "Invalid data. productId and a non-negative quantity are required." });
    }

    try {
        const cart = await prisma.cart.findUnique({ where: { userId: req.user.id } });
        if (!cart) {
            return res.status(404).json({ message: "User cart not found." });
        }

        // Find the specific cart item
        const existingItem = await prisma.cartItem.findFirst({
            where: { cartId: cart.id, productId: productId }
        });

        if (!existingItem) {
            return res.status(404).json({ message: "Item not found in cart." });
        }

        if (quantity === 0) {
            // If quantity is 0, remove the item
            await prisma.cartItem.delete({
                where: { id: existingItem.id }
            });
            return res.status(200).json({ message: "Item removed from cart." });
        } else {
            // Otherwise, update the quantity
            await prisma.cartItem.update({
                where: { id: existingItem.id },
                data: { quantity: quantity }
            });
            return res.status(200).json({ message: "Item quantity updated." });
        }
    } catch (error) {
        console.error("Error updating cart item:", error);
        res.status(500).json({ message: "Could not update item quantity", error: error.message });
    }
};

// --- NEW FUNCTION ---
/**
 * @desc    Remove an item from the cart
 * @route   DELETE /api/cart/:productId
 * @access  Private
 */
const removeCartItem = async (req, res) => {
    const { productId } = req.params; // Get productId from route parameters
    console.log(productId)

    try {
        const cart = await prisma.cart.findUnique({ where: { userId: req.user.id } });
        if (!cart) {
            return res.status(404).json({ message: "User cart not found." });
        }

        // Find the item to delete
        const itemToDelete = await prisma.cartItem.findFirst({
            where: {
                cartId: cart.id,
                productId: parseInt(productId) // Ensure productId is an integer
            }
        });

        if (!itemToDelete) {
            return res.status(404).json({ message: "Item not found in cart." });
        }

        // Delete the item
        await prisma.cartItem.delete({
            where: { id: itemToDelete.id }
        });

        res.status(200).json({ message: "Item removed from cart." });
    } catch (error) {
        console.error("Error removing cart item:", error);
        res.status(500).json({ message: "Could not remove item from cart", error: error.message });
    }
};

export {
    getCart,
    addItemToCart,
    updateCartItemQuantity,
    removeCartItem
};