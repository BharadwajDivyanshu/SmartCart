import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import ProductList from '../components/ProductList';

export default function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [q, setQ] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    api.getAllProducts().then((p) => {
      if (mounted) {
        setProducts(p);
        setLoading(false);
      }
    });
    return () => mounted = false;
  }, []);

  const filtered = products.filter(p => p.productName?.toLowerCase()?.includes(q?.toLowerCase()));

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">All Products</h1>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search products..." className="w-80 border px-3 py-2 rounded" />
      </div>
      {loading ? (<div className="grid grid-cols-4 gap-6"><div className="h-64 bg-gray-100 animate-pulse" /></div>) : <ProductList products={filtered} />}
    </div>
  );
}