import React from 'react';
import { Plus } from 'lucide-react';
import { useCart } from '../context/CartContext';

export default function ProductCard({ product }) {
  const { addToCart } = useCart();
  return (
    <div className="bg-white rounded-lg shadow hover:shadow-lg transition overflow-hidden">
      <div className="relative h-56">
        <img src={product.imageUrl} alt={product.productName} className="w-full h-full object-cover" />
      </div>
      <div className="p-4">
        <h3 className="text-sm font-semibold">{product.productName}</h3>
        <div className="flex items-center justify-between mt-2">
          <div className="text-lg font-bold">${(product.price || 0).toFixed(2)}</div>
          <button onClick={() => addToCart(product)} className="flex items-center gap-2 text-indigo-600 px-3 py-1 border border-indigo-100 rounded hover:bg-indigo-50">
            <Plus size={16}/> Add
          </button>
        </div>
      </div>
    </div>
  );
}