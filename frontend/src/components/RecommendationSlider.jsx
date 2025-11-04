import React from 'react';

export default function RecommendationSlider({ gamma, onChange }) {
  const getGammaLabel = (v) => {
    if (v < 0.33) return 'Preference';
    if (v < 0.66) return 'Balanced';
    return 'Healthy';
  };

  return (
    <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-4">
      <label className="text-sm text-gray-700">Preference</label>
      <input
        type="range"
        min="0"
        max="1"
        step="0.01"
        value={gamma}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-56 accent-indigo-600 cursor-pointer"
      />
      <label className="text-sm text-gray-700">Healthy</label>
      <span className="text-sm font-medium text-indigo-600 sm:ml-3">
        {getGammaLabel(gamma)}
      </span>
    </div>
  );
}