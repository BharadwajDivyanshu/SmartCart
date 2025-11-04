import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();

// @desc    Get all products
// @route   GET /api/products
const getAllProducts = async (req, res) => {
  try {
    const products = await prisma.product.findMany({
      where: {
        imageUrl: {
          not: null,
        },
      },
      take: 100,
    });
    res.json(products);
  } catch (error) {
    res.status(500).json({ message: "Could not fetch products", error: error.message });
  }
};

export { getAllProducts };