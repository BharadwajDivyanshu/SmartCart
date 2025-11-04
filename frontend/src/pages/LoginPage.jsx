import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

export default function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState('demo@smartcart.io');
  const [password, setPassword] = useState('password');
  const [err, setErr] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setErr('');
    try {
      await login(email, password);
      nav('/');
    } catch (e) {
      setErr(e.message || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12">
      <div className="max-w-md w-full bg-white p-8 rounded shadow">
        <h2 className="text-2xl font-bold mb-4">Sign in</h2>
        <form onSubmit={submit} className="space-y-4">
          <input className="w-full border px-3 py-2 rounded" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
          <input className="w-full border px-3 py-2 rounded" placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
          {err && <div className="text-red-600 text-sm">{err}</div>}
          <button className="w-full bg-indigo-600 text-white py-2 rounded">Sign in</button>
        </form>
        <p className="mt-4 text-sm text-gray-600">Don't have an account? <Link to="/signup" className="text-indigo-600">Create one</Link></p>
        <p className="mt-2 text-xs text-gray-500">Demo: demo@smartcart.io / password</p>
      </div>
    </div>
  );
}