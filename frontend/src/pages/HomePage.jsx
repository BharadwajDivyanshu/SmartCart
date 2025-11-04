import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import RecommendationSlider from '../components/RecommendationSlider';
import ProductList from '../components/ProductList';
import Loader from '../components/Loader';

export default function HomePage() {
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [gamma, setGamma] = useState(0.5);
  const [loading, setLoading] = useState(false);
  const [basketIds, setBasketIds] = useState([]); // for demo, could be derived from cart

  useEffect(() => {
    let mounted = true;
    if (!user) return;
    setLoading(true);

    // 1. Call the API with ONLY the 'gamma' value.
    // 2. The backend returns the FULL, sorted list of products.
    api.getRecommendations(gamma)
      .then(products => {
        // 3. Set the products directly. No second call needed.
        if (mounted) {
          setRecommendations(products);
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });

    return () => mounted = false;

    // You can remove basketIds from the dependency array, 
    // since the server gets it from the database automatically.
  }, [user, gamma]);

  return (
    <div>
      <div className="flex items-center justify-between bg-white p-6 rounded-xl mb-6">
        <div>
          <h2 className="text-2xl font-bold">Hello{user ? `, ${user.name}` : ''}</h2>
          <p className="text-gray-600">Recommended for you — adjust balance between preference and health</p>
        </div>
        {/* <div className="flex items-center gap-3">
          <label className="text-sm text-gray-700">Preference</label>
          <input type="range" min="0" max="1" step="0.01" value={gamma} onChange={(e) => setGamma(parseFloat(e.target.value))} className="w-60" />
          <label className="text-sm text-gray-700">Healthy</label>
        </div> */}
        <RecommendationSlider gamma={gamma} onChange={setGamma} />
      </div>

      {loading ? <Loader text="Loading products..." /> : <ProductList products={recommendations} />}
    </div>
  );
}