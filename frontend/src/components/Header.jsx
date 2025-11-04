import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShoppingCart } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';

export default function Header() {
  const { cartCount } = useCart();
  const { user, logout } = useAuth();
  const nav = useNavigate();
  return (
    <header className="bg-white border-b">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-3">
            <ShoppingCart className="text-indigo-600" />
            <div className="text-xl font-bold">SmartCart</div>
          </Link>
          <nav className="hidden md:flex gap-4 text-gray-600">
            <Link to="/products" className="hover:text-indigo-600">Products</Link>
            <Link to="/categories" className="hover:text-indigo-600">Categories</Link>
            <Link to="/deals" className="hover:text-indigo-600">Deals</Link>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          {user ? (
            <>
              <div className="text-sm text-gray-700 hidden sm:block">Hi, <strong className="text-indigo-600">{user.name}</strong></div>
              <button onClick={() => { logout(); nav('/login'); }} className="text-sm px-3 py-1 rounded bg-gray-100 hover:bg-gray-200">Logout</button>
            </>
          ) : (
            <Link to="/login" className="px-3 py-1 text-sm bg-indigo-600 text-white rounded">Sign in</Link>
          )}
          <Link to="/cart" className="relative">
            <div className="p-2 rounded-full hover:bg-gray-100">
              <ShoppingCart />
            </div>
            {cartCount > 0 && <span className="absolute -top-1 -right-1 bg-indigo-600 text-white rounded-full text-xs px-1.5">{cartCount}</span>}
          </Link>
        </div>
      </div>
    </header>
  );
}