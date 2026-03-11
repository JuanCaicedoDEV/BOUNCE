import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Trash2, FileText, CheckCircle, AlertCircle, LogOut, GraduationCap, Plus } from 'lucide-react';
import axios from 'axios';

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8001';

interface Program {
  doc_id: string;
  program_name: string;
  filename: string;
}

interface AdminDashboardProps {
  universityId: string;
  universityName: string;
  onLogout: () => void;
}

export function AdminDashboard({ universityId, universityName, onLogout }: AdminDashboardProps) {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [programName, setProgramName] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3500);
  };

  const fetchPrograms = async () => {
    try {
      const { data } = await axios.get(`${API}/admin/programs/${universityId}`);
      setPrograms(data.programs);
    } catch {
      showToast('error', 'Could not load programs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPrograms(); }, []);

  const handleUpload = async () => {
    if (!selectedFile || !programName.trim()) return;
    setUploading(true);
    const form = new FormData();
    form.append('university_id', universityId);
    form.append('program_name', programName.trim());
    form.append('file', selectedFile);
    try {
      await axios.post(`${API}/admin/upload`, form);
      showToast('success', `"${programName}" indexed successfully.`);
      setProgramName('');
      setSelectedFile(null);
      fetchPrograms();
    } catch {
      showToast('error', 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: string, name: string) => {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    try {
      await axios.delete(`${API}/admin/programs/${universityId}/${docId}`);
      showToast('success', `"${name}" removed.`);
      setPrograms(p => p.filter(x => x.doc_id !== docId));
    } catch {
      showToast('error', 'Could not delete program.');
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) setSelectedFile(file);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-teal-600 flex items-center justify-center">
            <GraduationCap size={18} className="text-white" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-slate-800">Bounce Admin</h1>
            <p className="text-xs text-slate-500">{universityName}</p>
          </div>
        </div>
        <button
          onClick={onLogout}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors"
        >
          <LogOut size={15} />
          Sign out
        </button>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-10 space-y-8">

        {/* Upload card */}
        <section className="bg-white rounded-2xl border border-slate-200 p-6 space-y-5">
          <div className="flex items-center gap-2">
            <Plus size={18} className="text-teal-600" />
            <h2 className="text-base font-semibold text-slate-800">Add a Program</h2>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Program name</label>
            <input
              type="text"
              value={programName}
              onChange={e => setProgramName(e.target.value)}
              placeholder="e.g. Medical Assistant Certificate"
              className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-teal-400 transition-colors"
            />
          </div>

          {/* Drop zone */}
          <div
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              dragOver ? 'border-teal-400 bg-teal-50' : 'border-slate-200 hover:border-teal-300 hover:bg-slate-50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt"
              className="hidden"
              onChange={e => setSelectedFile(e.target.files?.[0] ?? null)}
            />
            {selectedFile ? (
              <div className="flex items-center justify-center gap-2 text-teal-700">
                <FileText size={18} />
                <span className="text-sm font-medium">{selectedFile.name}</span>
                <button
                  onClick={e => { e.stopPropagation(); setSelectedFile(null); }}
                  className="ml-2 text-slate-400 hover:text-slate-600"
                >✕</button>
              </div>
            ) : (
              <div className="space-y-1">
                <Upload size={22} className="mx-auto text-slate-400" />
                <p className="text-sm text-slate-500">Drop a PDF or click to browse</p>
                <p className="text-xs text-slate-400">PDF or TXT, up to 10MB</p>
              </div>
            )}
          </div>

          <button
            onClick={handleUpload}
            disabled={!selectedFile || !programName.trim() || uploading}
            className="w-full py-2.5 rounded-xl text-sm font-medium transition-colors bg-teal-600 text-white hover:bg-teal-700 disabled:bg-slate-100 disabled:text-slate-400 disabled:cursor-not-allowed"
          >
            {uploading ? 'Indexing...' : 'Upload & Index'}
          </button>
        </section>

        {/* Programs list */}
        <section className="space-y-3">
          <h2 className="text-base font-semibold text-slate-800">
            Indexed Programs
            <span className="ml-2 text-sm font-normal text-slate-400">({programs.length})</span>
          </h2>

          {loading ? (
            <div className="text-sm text-slate-400 py-6 text-center">Loading...</div>
          ) : programs.length === 0 ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-sm text-slate-400">
              No programs yet. Upload your first PDF above.
            </div>
          ) : (
            <AnimatePresence>
              {programs.map(p => (
                <motion.div
                  key={p.doc_id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="bg-white rounded-xl border border-slate-200 px-5 py-4 flex items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-teal-50 flex items-center justify-center shrink-0">
                      <FileText size={15} className="text-teal-600" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-800 truncate">{p.program_name}</p>
                      <p className="text-xs text-slate-400 truncate">{p.filename}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(p.doc_id, p.program_name)}
                    className="shrink-0 p-2 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                  >
                    <Trash2 size={15} />
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </section>
      </main>

      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className={`fixed bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 px-5 py-3 rounded-xl shadow-lg text-sm font-medium ${
              toast.type === 'success'
                ? 'bg-emerald-600 text-white'
                : 'bg-red-600 text-white'
            }`}
          >
            {toast.type === 'success'
              ? <CheckCircle size={16} />
              : <AlertCircle size={16} />
            }
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
