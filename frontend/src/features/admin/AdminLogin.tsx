import { useState } from 'react';
import { GraduationCap } from 'lucide-react';

// MVP: universidad ID → nombre + clave de acceso
// En producción esto vendría de una base de datos
const UNIVERSITIES: Record<string, { name: string; password: string }> = {
  laguardia: { name: 'LaGuardia Community College', password: 'bounce2026' },
  cuny: { name: 'CUNY', password: 'bounce2026' },
};

interface AdminLoginProps {
  onLogin: (universityId: string, universityName: string) => void;
}

export function AdminLogin({ onLogin }: AdminLoginProps) {
  const [universityId, setUniversityId] = useState('laguardia');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const uni = UNIVERSITIES[universityId.trim().toLowerCase()];
    if (!uni || password !== uni.password) {
      setError('Invalid university ID or password.');
      return;
    }
    onLogin(universityId.trim().toLowerCase(), uni.name);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl border border-slate-200 shadow-sm p-8 space-y-6">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-teal-600 flex items-center justify-center">
            <GraduationCap size={22} className="text-white" />
          </div>
          <div className="text-center">
            <h1 className="text-lg font-semibold text-slate-800">Bounce Admin</h1>
            <p className="text-sm text-slate-500">University portal</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">University ID</label>
            <input
              type="text"
              value={universityId}
              onChange={e => { setUniversityId(e.target.value); setError(''); }}
              placeholder="laguardia"
              className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-teal-400 transition-colors"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => { setPassword(e.target.value); setError(''); }}
              placeholder="••••••••"
              className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-teal-400 transition-colors"
            />
          </div>

          {error && (
            <p className="text-xs text-red-500">{error}</p>
          )}

          <button
            type="submit"
            className="w-full py-2.5 rounded-xl text-sm font-medium bg-teal-600 text-white hover:bg-teal-700 transition-colors"
          >
            Sign in
          </button>
        </form>

        <p className="text-center text-xs text-slate-400">
          Student chat? <a href="/" className="text-teal-600 hover:underline">Go here</a>
        </p>
      </div>
    </div>
  );
}
