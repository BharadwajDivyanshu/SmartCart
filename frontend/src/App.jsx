import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import Header from './components/Header';
import HomePage from './pages/HomePage';
import ProductsPage from './pages/ProductsPage';
import CartPage from './pages/CartPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';

/**
 * A helper component that wraps your main application layout.
 * This ensures the Cart is only loaded *after* a user is logged in.
 */
function AppLayout() {
  return (
    <CartProvider>
      <div className="min-h-screen bg-slate-50">
        <Header />
        <main className="max-w-7xl mx-auto p-6">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/products" element={<ProductsPage />} />
            <Route path="/cart" element={<CartPage />} />
            {/* Any other private routes go here */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </CartProvider>
  );
}

/**
 * A helper component to protect routes.
 * It checks if a user is logged in. If not, it redirects to the /login page.
 */
function PrivateRoute({ children }) {
  const { user } = useAuth();
  // If you add an 'isLoading' state to AuthContext, you can show a spinner here
  return user ? children : <Navigate to="/login" replace />;
}

/**
 * The main App component now handles routing logic.
 * AuthProvider wraps everything so auth state is always available.
 */
export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* PUBLIC ROUTES: These are accessible without login */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* PRIVATE ROUTES: All other routes are wrapped in PrivateRoute */}
        <Route
          path="/*"
          element={
            <PrivateRoute>
              <AppLayout />
            </PrivateRoute>
          }
        />
      </Routes>
    </AuthProvider>
  );
}