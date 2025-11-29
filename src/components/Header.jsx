import React from 'react';
import { motion } from 'framer-motion';

const Header = () => {
    const scrollToSection = (id) => {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    };

    return (
        <motion.header
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200"
        >
            <div className="container h-16 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <img src="/src/assets/cornell-logo.svg" alt="Cornell University" className="h-8 md:h-10" />
                    <div className="hidden md:block w-px h-6 bg-gray-300 mx-2"></div>
                    <span className="hidden md:block font-semibold text-gray-800 tracking-tight">Sam Belliveau</span>
                </div>
            </div>
        </motion.header>
    );
};

export default Header;
