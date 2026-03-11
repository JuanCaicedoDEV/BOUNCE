import { useState } from 'react';
import { GlassBox, DynamicButton, Reveal } from '../../components/ui';
import { motion } from 'framer-motion';
import { Shield, Sparkles, MoveRight } from 'lucide-react';

export function LoginScreen({ onLogin }: { onLogin: (user: string) => void }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (email && password) {
            onLogin(email);
        }
    };

    return (
        <main className="min-h-screen bg-[#0A0A0B] relative flex items-center justify-center p-6 sm:p-12 overflow-hidden">
            {/* Decorative Elements */}
            <div className="absolute top-[-10%] right-[-5%] w-[40%] h-[40%] bg-brand/10 blur-[120px] rounded-full" />
            <div className="absolute bottom-[-10%] left-[-5%] w-[30%] h-[30%] bg-accent-mint/5 blur-[100px] rounded-full" />

            <GlassBox className="w-full max-w-[480px] p-10 sm:p-12 relative z-10 overflow-hidden border-white/10 shadow-2xl">
                {/* Branding Header */}
                <div className="flex justify-between items-center mb-10">
                    <Reveal>
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg bg-brand flex items-center justify-center shadow-glow-brand">
                                <Shield className="text-white w-5 h-5" />
                            </div>
                            <span className="text-xs font-bold tracking-[0.2em] uppercase text-white/60">Affila • Bounce</span>
                        </div>
                    </Reveal>
                    <Reveal delay={0.2}>
                        <Sparkles className="text-brand/40 animate-pulse-glow" size={20} />
                    </Reveal>
                </div>

                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                    className="space-y-2 mb-10"
                >
                    <h1 className="text-4xl font-bold tracking-tight text-white leading-tight">
                        Descubre tu <span className="text-brand">potencial</span> real.
                    </h1>
                    <p className="text-white/40 text-sm font-medium">
                        Accede a tu consejero profesional personalizado impulsado por IA.
                    </p>
                </motion.div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <Reveal delay={0.4}>
                        <div className="space-y-1.5 text-left">
                            <label className="text-[10px] font-bold text-white/30 uppercase tracking-widest px-1">Identidad Digital</label>
                            <input
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="glass-input w-full"
                                placeholder="tu@correo.com"
                            />
                        </div>
                    </Reveal>

                    <Reveal delay={0.5}>
                        <div className="space-y-1.5 text-left">
                            <label className="text-[10px] font-bold text-white/30 uppercase tracking-widest px-1">Clave de Acceso</label>
                            <input
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="glass-input w-full"
                                placeholder="••••••••"
                            />
                        </div>
                    </Reveal>

                    <Reveal delay={0.6}>
                        <DynamicButton type="submit" className="w-full flex items-center justify-center gap-3">
                            Comenzar Exploración <MoveRight size={18} />
                        </DynamicButton>
                    </Reveal>
                </form>

                <div className="mt-12 pt-8 border-t border-white/[0.04] flex justify-between items-center">
                    <span className="text-[10px] font-medium text-white/20 uppercase tracking-widest font-sans">© 2026 Affila Project</span>
                    <div className="flex gap-4">
                        <div className="w-1.5 h-1.5 rounded-full bg-accent-mint animate-pulse" title="System Online" />
                    </div>
                </div>
            </GlassBox>
        </main>
    );
}
