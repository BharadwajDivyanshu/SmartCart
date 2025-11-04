import React from 'react';
import { useCart } from '../context/CartContext';

export default function CartItem({ item }) {
  const { updateQuantity, removeFromCart } = useCart();
  return (
    <div className="flex gap-4 items-center border-b py-4">
      <img src={item.imageUrl} alt={item.productName} className="w-20 h-20 object-cover rounded" />
      <div className="flex-1">
        <div className="font-semibold">{item.productName}</div>
        <div className="text-sm text-gray-500">${(item.price || 0).toFixed(2)}</div>
      </div>
      <div className="flex items-center gap-2">
        <input type="number" min="1" value={item.quantity} onChange={(e) => updateQuantity(item.product_id, parseInt(e.target.value) || 1)} className="w-16 border rounded px-2 py-1" />
        <button onClick={() => removeFromCart(item.productId)} className="text-red-600 text-sm">Remove</button>
      </div>
    </div>
  );
}