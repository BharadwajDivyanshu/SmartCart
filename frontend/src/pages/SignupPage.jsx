import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function SignupPage() {
  const { signup } = useAuth();
  const nav = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    try {
      await signup(name || 'New', email, password);
      nav('/');
    } catch (e) {
      setErr(e.message || 'Signup failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12">
      <div className="max-w-md w-full bg-white p-8 rounded shadow">
        <h2 className="text-2xl font-bold mb-4">Create account</h2>
        <form onSubmit={submit} className="space-y-4">
          <input className="w-full border px-3 py-2 rounded" placeholder="Full name" value={name} onChange={e => setName(e.target.value)} />
          <input className="w-full border px-3 py-2 rounded" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
          <input className="w-full border px-3 py-2 rounded" placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
          {err && <div className="text-red-600 text-sm">{err}</div>}
          <button className="w-full bg-indigo-600 text-white py-2 rounded">Create account</button>
        </form>
      </div>
    </div>
  );
}