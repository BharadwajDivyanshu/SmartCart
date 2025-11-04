import React, { createContext, useContext, useMemo, useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from './AuthContext'; // We need the user to know *who* to fetch the cart for

const CartContext = createContext(null);
export const useCart = () => {
  const c = useContext(CartContext);
  if (!c) throw new Error('useCart must be used inside CartProvider');
  return c;
};

export const CartProvider = ({ children }) => {
  const [cartItems, setCartItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const { user } = useAuth(); // Get the currently logged-in user

  // --- EFFECT TO FETCH CART ON LOGIN ---
  useEffect(() => {
    // Only fetch the cart if the user is logged in
    if (user) {
      setIsLoading(true);
      api.getCart()
        .then(items => {
          // The backend returns CartItem objects, which include the product
          // We need to flatten them to match your old state structure
          const flattenedItems = items.map(cartItem => ({
            ...cartItem.product, // Spread the product details (name, price, etc.)
            quantity: cartItem.quantity, // Add the quantity
            cartItemId: cartItem.id // Save the cartItem ID for updates
          }));
          setCartItems(flattenedItems);
        })
        .catch(err => {
          console.error("Failed to fetch cart:", err);
          // Don't throw an error, just start with an empty cart
          setCartItems([]);
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      // If user logs out, clear the cart
      setCartItems([]);
      setIsLoading(false);
    }
  }, [user]); // This effect re-runs when the user logs in or out

  // --- API-CONNECTED CART FUNCTIONS ---

  const addToCart = async (product, quantity = 1) => {
    if (!product) return;
    
    // Tell the backend to add the item
    try {
      await api.addToCart(product, quantity);
      
      // Now, update the local state to match
      setCartItems(prev => {
        const found = prev.find(i => i.productId === product.productId);
        if (found) {
          return prev.map(i => i.productId === product.productId ? { ...i, quantity: i.quantity + quantity } : i);
        }
        return [...prev, { ...product, quantity }];
      });
    } catch (err) {
      console.error("Failed to add to cart:", err);
      // Optionally show an error to the user
    }
  };

  const removeFromCart = async (productId) => {
    try {
      // Tell the backend to remove the item
      await api.removeFromCart(productId);
      console.log(productId)
      
      // Now, update the local state
      setCartItems(prev => prev.filter(i => i.productId !== productId));
    } catch (err) {
      console.error("Failed to remove from cart:", err);
    }
  };

  const updateQuantity = async (productId, qty) => {
    if (qty <= 0) {
      // If quantity is 0, treat it as a removal
      return removeFromCart(productId);
    }
    
    try {
      // Tell the backend to update the quantity
      await api.updateQuantity(productId, qty);
      
      // Now, update the local state
      setCartItems(prev => prev.map(i => i.productId === productId ? { ...i, quantity: qty } : i));
    } catch (err) {
      console.error("Failed to update quantity:", err);
    }
  };

  // --- Memos (no change needed here) ---
  const cartCount = useMemo(() => cartItems.reduce((s, it) => s + (it.quantity || 0), 0), [cartItems]);
  const subtotal = useMemo(() => cartItems.reduce((s, it) => s + (it.quantity || 0) * (it.price || 0), 0), [cartItems]);

  const ctx = useMemo(() => ({
    cartItems,
    addToCart,
    removeFromCart,
    updateQuantity,
    cartCount,
    subtotal,
    isLoadingCart: isLoading // Expose loading state to the UI
  }), [cartItems, cartCount, subtotal, isLoading]);

  return <CartContext.Provider value={ctx}>{children}</CartContext.Provider>;
};