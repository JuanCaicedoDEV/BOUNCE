import React from 'react';
import { motion } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface PanelProps {
    children: React.ReactNode;
    className?: string;
    delay?: number;
}

export const Panel: React.FC<PanelProps> = ({ children, className, delay = 0 }) => (
    <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay, ease: [0.16, 1, 0.3, 1] }}
        className={cn('panel', className)}
    >
        {children}
    </motion.div>
);

// Alias for backward compatibility with LoginScreen
export const GlassBox = Panel;

export const Reveal: React.FC<{ children: React.ReactNode; delay?: number }> = ({ children, delay = 0 }) => (
    <motion.div
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, delay, ease: 'easeOut' }}
    >
        {children}
    </motion.div>
);

export const DynamicButton: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' }> = ({
    children,
    className,
    variant = 'primary',
    ...props
}) => (
    <motion.button
        whileHover={{ y: -1 }}
        whileTap={{ scale: 0.97 }}
        className={cn(variant === 'primary' ? 'btn-primary' : 'btn-secondary', className)}
        {...props}
    >
        {children}
    </motion.button>
);
