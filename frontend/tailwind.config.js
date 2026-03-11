/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
            },
            colors: {
                brand: {
                    DEFAULT: '#8251EE',
                    light: '#A37EF5',
                    dark: '#5B35C1',
                },
                surface: {
                    DEFAULT: '#141414',
                    raised: '#1C1C1C',
                    overlay: '#242424',
                    border: '#2A2A2A',
                },
                accent: {
                    green: '#22C55E',
                },
            },
            boxShadow: {
                'sm': '0 1px 3px rgba(0,0,0,0.4)',
                'md': '0 4px 12px rgba(0,0,0,0.4)',
                'lg': '0 8px 24px rgba(0,0,0,0.5)',
                'brand': '0 0 0 1px rgba(130, 81, 238, 0.4)',
            },
            animation: {
                'fade-in': 'fadeIn 0.3s ease-out',
                'slide-up': 'slideUp 0.3s ease-out',
                'blink': 'blink 1.2s ease-in-out infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { opacity: '0', transform: 'translateY(8px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                blink: {
                    '0%, 100%': { opacity: '0.3' },
                    '50%': { opacity: '1' },
                },
            },
        },
    },
    plugins: [],
}
