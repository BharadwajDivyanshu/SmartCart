import React from 'react';
import { useCart } from '../context/CartContext';
import CartItem from '../components/CartItem';
import { useNavigate } from 'react-router-dom';

export default function CartPage() {
  const { cartItems, subtotal } = useCart();
  const nav = useNavigate();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow">
        <h2 className="text-xl font-semibold mb-4">Shopping Cart</h2>
        {cartItems.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-700">Your cart is empty.</p>
            <button onClick={() => nav('/products')} className="mt-4 bg-indigo-600 text-white px-4 py-2 rounded">Start shopping</button>
          </div>
        ) : (
          cartItems.map(it => <CartItem key={it.productId} item={it} />)
        )}
      </div>

      <aside className="bg-white p-6 rounded-xl shadow">
        <h3 className="text-lg font-semibold mb-4">Order Summary</h3>
        <div className="flex justify-between text-gray-700 mb-2"><span>Subtotal</span><span>${subtotal.toFixed(2)}</span></div>
        <div className="text-sm text-gray-500 mb-6">Taxes & shipping calculated at checkout</div>
        <button className="w-full bg-indigo-600 text-white py-3 rounded">Proceed to Checkout</button>
      </aside>
    </div>
  );
}