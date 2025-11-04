// // Mock API service — replace with real endpoints when available.
// const EMBED_DIM = 32;

// const mockProducts = [
//   { product_id: 1, product_name: 'Banana', price: 0.69, health_factor_score: 0.9, category: 'Fruits', image_url: 'https://placehold.co/400x400/fef08a/422006?text=Banana' },
//   { product_id: 2, product_name: 'Organic Strawberries', price: 4.99, health_factor_score: 0.95, category: 'Fruits', image_url: 'https://placehold.co/400x400/fecaca/7f1d1d?text=Strawberries' },
//   { product_id: 3, product_name: 'Organic Avocado', price: 2.50, health_factor_score: 0.85, category: 'Fruits', image_url: 'https://placehold.co/400x400/d9f99d/3f6212?text=Avocado' },
//   // ... add more realistic items as needed
//   { product_id: 10, product_name: 'Organic Whole Milk', price: 3.99, health_factor_score: 0.6, category: 'Dairy', image_url: 'https://placehold.co/400x400/f0f9ff/0c4a6e?text=Milk' },
//   { product_id: 20, product_name: 'Organic Spinach', price: 3.29, health_factor_score: 0.99, category: 'Vegetables', image_url: 'https://placehold.co/400x400/dcfce7/14532d?text=Spinach' }
// ];

// const generateRandomVector = () => Array.from({ length: EMBED_DIM }, () => Math.random() * 2 - 1);
// const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);

// const mockProductEmbeddings = {};
// mockProducts.forEach(p => { mockProductEmbeddings[p.product_id] = generateRandomVector(); });
// const mockUserEmbeddings = { demo: generateRandomVector(), alice: generateRandomVector() };

// export const api = {
//   login: async (email, password) => {
//     // Mock login - return user object
//     await new Promise(r => setTimeout(r, 300));
//     if ((email === 'demo@smartcart.io' && password === 'password') || email.endsWith('@example.com')) {
//       const username = email.split('@')[0];
//       return { id: username, name: username[0].toUpperCase() + username.slice(1), instacart_user_id: username === 'demo' ? 'demo' : 'alice' };
//     }
//     throw new Error('Invalid credentials');
//   },

//   signup: async (name, email, password) => {
//     await new Promise(r => setTimeout(r, 400));
//     return { id: email.split('@')[0], name, instacart_user_id: 'demo' };
//   },

//   getAllProducts: async () => {
//     await new Promise(r => setTimeout(r, 200));
//     return mockProducts;
//   },

//   getProductsByIds: async (ids) => {
//     await new Promise(r => setTimeout(r, 120));
//     return mockProducts.filter(p => ids.includes(p.product_id));
//   },

//   getRecommendations: async (userId, basketIds = [], gamma = 0.5, k = 12) => {
//     // Compose a simple query vector (user embedding + basket average)
//     await new Promise(r => setTimeout(r, 300));
//     const userVec = mockUserEmbeddings[userId] || generateRandomVector();
//     let queryVec = userVec;
//     if (basketIds.length > 0) {
//       const basketVecs = basketIds.map(id => mockProductEmbeddings[id] || generateRandomVector());
//       const avg = new Array(EMBED_DIM).fill(0).map((_, i) => basketVecs.reduce((s, v) => s + v[i], 0) / basketVecs.length);
//       queryVec = userVec.map((v, i) => (v + avg[i]) / 2);
//     }
//     const scores = mockProducts
//       .filter(p => !basketIds.includes(p.product_id))
//       .map(p => {
//         const pref = dot(queryVec, mockProductEmbeddings[p.product_id] || generateRandomVector());
//         const finalScore = (1 - gamma) * pref + gamma * p.health_factor_score;
//         return { id: p.product_id, score: finalScore };
//       })
//       .sort((a, b) => b.score - a.score)
//       .slice(0, k)
//       .map(s => s.id);
//     return scores;
//   }
// };

import axios from 'axios';

// Create a pre-configured axios instance
const apiClient = axios.create({
  // All requests will now go to http://localhost:5173/api/...
  // and Vite will proxy them to http://localhost:8000/api/...
  baseURL: 'http://localhost:8000/api',
});

/**
 * This "interceptor" automatically attaches the user's auth token
 * to every single request they make after logging in.
 */
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('userToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// --- This is the new, real API object ---
export const api = {
  /**
   * Logs in a user.
   * On success, saves the user data and token to local storage.
   */
  login: async (email, password) => {
    // This call now goes to: POST http://localhost:8000/api/auth/login
    const response = await apiClient.post('/auth/login', { email, password });
    
    if (response.data.token) {
      localStorage.setItem('userToken', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data));
    }
    return response.data;
  },

  /**
   * Signs up a new user.
   * On success, saves the user data and token to local storage.
   */
  signup: async (name, email, password) => {
    // This call now goes to: POST http://localhost:8000/api/auth/signup
    const response = await apiClient.post('/auth/signup', { name, email, password });
    
    if (response.data.token) {
      localStorage.setItem('userToken', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data));
    }
    return response.data;
  },

  /**
   * Fetches the complete list of all products.
   */
  getAllProducts: async () => {
    // This call now goes to: GET http://localhost:8000/api/products
    const response = await apiClient.get('/products');
    return response.data;
  },

  /**
   * Gets AI-powered recommendations for the currently logged-in user.
   * The token is sent automatically by the interceptor.
   */
  getRecommendations: async (gamma = 0.5) => {
    // This call now goes to: POST http://localhost:8000/api/recommendations
    const response = await apiClient.post('/recommendations', { gamma });
    return response.data;
  },

  /**
   * Fetches the contents of the user's cart from the database.
   */
  getCart: async () => {
    // This call now goes to: GET http://localhost:8000/api/cart
    const response = await apiClient.get('/cart');
    // The backend returns just the list of CartItems
    return response.data;
  },

  /**
   * Adds an item to the user's cart.
   * Note: We only need to send the productId and quantity.
   */
  addToCart: async (product, quantity = 1) => {
    // This call now goes to: POST http://localhost:8000/api/cart
    const response = await apiClient.post('/cart', { 
      productId: product.productId, // Use productId (from database)
      quantity: quantity 
    });
    return response.data;
  },
  
  /**
   * Updates the quantity of an item in the cart.
   * (You will need to add this route to your Node.js backend)
   */
  updateQuantity: async (productId, quantity) => {
    await apiClient.put('/cart', { productId, quantity });
    console.log('API: updateQuantity not yet implemented in backend');
  },

  /**
   * Removes an item from the cart.
   * (You will need to add this route to your Node.js backend)
   */
  removeFromCart: async (productId) => {
    await apiClient.delete(`/cart/${productId}`);
    console.log('API: removeFromCart not yet implemented in backend');
  },

  /**
   * Helper function to get the saved user from local storage on app load.
   */
  getSavedUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  /**
   * Logs the user out by clearing local storage.
   */
  logout: () => {
    localStorage.removeItem('userToken');
    localStorage.removeItem('user');
  }
};
