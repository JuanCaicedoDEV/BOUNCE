import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { LoginScreen } from './features/auth/LoginScreen';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowUp, GraduationCap, Paperclip, X, FileText } from 'lucide-react';
import axios from 'axios';

const QUICK_REPLIES = [
  'Looking for better pay',
  'Want more stability',
  'Interested in changing fields',
];

type Message = { role: 'user' | 'assistant'; content: string };

export default function App() {
  const [user, setUser] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        "Thanks for connecting today. To get started, what made you decide to explore new career options at this point in your life?",
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [cvFile, setCvFile] = useState<{ name: string; content: string } | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target?.result as string;
      setCvFile({ name: file.name, content });
      // Notify the conversation
      const notice: Message = {
        role: 'user',
        content: `[CV uploaded: ${file.name}]\n\n${content.slice(0, 3000)}${content.length > 3000 ? '...' : ''}`,
      };
      setMessages((prev) => [...prev, notice]);
    };
    reader.readAsText(file);
    // Reset input so same file can be re-uploaded
    e.target.value = '';
  };

  const handleSend = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || isLoading) return;

    const userMsg: Message = { role: 'user', content };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8001/chat', {
        messages: updatedMessages,
        user_id: user || 'guest',
        cv_data: cvFile?.content ?? null,
      });
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.data.content },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I had trouble connecting to the system. Please try again.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) {
    return <LoginScreen onLogin={(email) => setUser(email)} />;
  }

  const userInitial = user.charAt(0).toUpperCase();

  return (
    <div className="h-screen w-screen bg-white flex flex-col overflow-hidden">

      {/* ── HEADER ── */}
      <header className="flex items-center gap-3 px-5 py-4 border-b border-slate-100 bg-white shrink-0">
        <div className="w-10 h-10 rounded-full bg-teal-600 flex items-center justify-center shrink-0 shadow-sm">
          <GraduationCap size={20} className="text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-base font-semibold text-slate-800 leading-tight">
            Career Advisor — LaGuardia
          </h1>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 block shrink-0" />
            <span className="text-xs text-slate-400 font-medium">Online</span>
          </div>
        </div>
        {/* CV badge in header */}
        {cvFile && (
          <div className="flex items-center gap-1.5 bg-teal-50 border border-teal-200 rounded-full px-3 py-1 shrink-0">
            <FileText size={12} className="text-teal-600" />
            <span className="text-xs text-teal-700 font-medium max-w-[120px] truncate">{cvFile.name}</span>
            <button onClick={() => setCvFile(null)} className="text-teal-400 hover:text-teal-600 ml-0.5">
              <X size={12} />
            </button>
          </div>
        )}
      </header>

      {/* ── MESSAGES ── */}
      <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8 lg:px-16 xl:px-32 space-y-4 bg-slate-50">
        <div className="max-w-3xl mx-auto space-y-4">
          <AnimatePresence initial={false}>
            {messages.map((m, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, ease: 'easeOut' }}
                className={`flex items-end gap-2 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {m.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-full bg-teal-600 flex items-center justify-center shrink-0">
                    <GraduationCap size={13} className="text-white" />
                  </div>
                )}
                <div className={`max-w-[78%] px-4 py-3 rounded-2xl text-base leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-teal-600 text-white rounded-br-sm'
                    : 'bg-white text-slate-700 shadow-sm rounded-bl-sm border border-slate-100'
                }`}>
                  {/* Show CV uploads with an icon */}
                  {m.content.startsWith('[CV uploaded:') ? (
                    <div className="flex items-center gap-2 text-teal-100">
                      <FileText size={16} />
                      <span className="text-sm font-medium">
                        {m.content.match(/\[CV uploaded: (.+?)\]/)?.[1] ?? 'CV uploaded'}
                      </span>
                    </div>
                  ) : m.role === 'assistant' ? (
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                        ul: ({ children }) => <ul className="list-disc pl-4 space-y-1 mt-1">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal pl-4 space-y-1 mt-1">{children}</ol>,
                        li: ({ children }) => <li>{children}</li>,
                        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                      }}
                    >
                      {m.content}
                    </ReactMarkdown>
                  ) : (
                    m.content
                  )}
                </div>
                {m.role === 'user' && (
                  <div className="w-7 h-7 rounded-full bg-teal-700 flex items-center justify-center shrink-0 text-xs font-bold text-white">
                    {userInitial}
                  </div>
                )}
              </motion.div>
            ))}

            {/* Typing indicator */}
            {isLoading && (
              <motion.div
                key="typing"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="flex items-end gap-2 justify-start"
              >
                <div className="w-7 h-7 rounded-full bg-teal-600 flex items-center justify-center shrink-0">
                  <GraduationCap size={13} className="text-white" />
                </div>
                <div className="bg-white border border-slate-100 shadow-sm px-4 py-3.5 rounded-2xl rounded-bl-sm flex gap-1.5 items-center">
                  {[0, 160, 320].map((delay) => (
                    <span
                      key={delay}
                      className="w-2 h-2 rounded-full bg-slate-300 block animate-bounce"
                      style={{ animationDelay: `${delay}ms`, animationDuration: '900ms' }}
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={chatEndRef} />
        </div>
      </div>

      {/* ── INPUT AREA ── */}
      <div className="bg-white border-t border-slate-100 px-4 pt-3 pb-5 shrink-0">
        <div className="max-w-3xl mx-auto">
          {/* Quick reply chips */}
          <div className="flex gap-2 flex-wrap mb-3">
            {QUICK_REPLIES.map((reply) => (
              <button
                key={reply}
                onClick={() => handleSend(reply)}
                disabled={isLoading}
                className="text-sm px-3.5 py-1.5 rounded-full border border-slate-200 text-slate-500 bg-slate-50 hover:border-teal-400 hover:text-teal-700 hover:bg-teal-50 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {reply}
              </button>
            ))}
          </div>

          {/* Input row */}
          <div className="flex items-center gap-2">
            {/* CV upload button */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.pdf,.doc,.docx"
              onChange={handleFileUpload}
              className="hidden"
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => fileInputRef.current?.click()}
              title="Upload CV"
              className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0 border border-slate-200 bg-slate-50 text-slate-400 hover:text-teal-600 hover:border-teal-300 hover:bg-teal-50 transition-colors"
            >
              <Paperclip size={18} />
            </motion.button>

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type your response here..."
              disabled={isLoading}
              className="flex-1 bg-slate-50 border border-slate-200 focus:border-teal-400 focus:outline-none rounded-xl px-4 py-3 text-base text-slate-800 placeholder:text-slate-400 transition-colors disabled:opacity-50"
            />

            <motion.button
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.94 }}
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 transition-colors ${
                input.trim() && !isLoading
                  ? 'bg-teal-600 text-white hover:bg-teal-700'
                  : 'bg-slate-100 text-slate-300 cursor-not-allowed'
              }`}
            >
              <ArrowUp size={18} />
            </motion.button>
          </div>

          <p className="text-xs text-slate-300 mt-3 text-center">
            Bounce · Affila Career Services
          </p>
        </div>
      </div>
    </div>
  );
}
