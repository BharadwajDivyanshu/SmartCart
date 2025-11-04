import { PrismaClient } from '@prisma/client';
import pkg from 'bcryptjs';
const { genSalt, hash, compare } = pkg;
import jsonwebtoken from 'jsonwebtoken';
const { sign } = jsonwebtoken;

const prisma = new PrismaClient();

// Generate JWT
const generateToken = (id) => {
  return sign({ id }, process.env.JWT_SECRET, {
    expiresIn: '30d',
  });
};

// @desc    Register a new user
// @route   POST /api/auth/signup
const signup = async (req, res) => {
  const { name, email, password } = req.body;
  console.log(req.body)

  if (!name || !email || !password) {
    return res.status (400).json({ message: 'Please add all fields' });
  }

  const userExists = await prisma.user.findUnique({ where: { email } });

  if (userExists) {
    return res.status(400).json({ message: 'User already exists' });
  }

  const salt = await genSalt(10);
  const passwordHash = await hash(password, salt);

  try {
    const user = await prisma.user.create({
      data: {
        name,
        email,
        passwordHash,
      },
    });
    
    // Create an empty cart for the new user
    await prisma.cart.create({ data: { userId: user.id } });

    res.status(201).json({
      id: user.id,
      name: user.name,
      email: user.email,
      token: generateToken(user.id),
    });
  } catch (error) {
    res.status(500).json({ message: 'Invalid user data', error: error.message });
  }
};

// @desc    Authenticate a user
// @route   POST /api/auth/login
const login = async (req, res) => {
  console.log(req.body)
  const { email, password } = req.body;

  try {
    const user = await prisma.user.findUnique({ where: { email } });

    if (user && (await compare(password, user.passwordHash))) {
      res.json({
        id: user.id,
        name: user.name,
        email: user.email,
        instacartUserId: user.instacartUserId, // Send this to the frontend
        token: generateToken(user.id),
      });
    } else {
      res.status(401).json({ message: 'Invalid credentials' });
    }
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
};

export { signup, login };