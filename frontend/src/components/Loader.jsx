import React from 'react';

export default function Loader({ size = 'md', text = 'Loading...' }) {
  const spinnerSize = size === 'sm' ? 'h-5 w-5' : size === 'lg' ? 'h-12 w-12' : 'h-8 w-8';

  return (
    <div className="flex flex-col items-center justify-center text-gray-500">
      <svg
        className={`animate-spin ${spinnerSize} text-indigo-600 mb-2`}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
        />
      </svg>
      {text && <p className="text-sm">{text}</p>}
    </div>
  );
}