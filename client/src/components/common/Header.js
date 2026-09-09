// Unused top nav bar for the Dashboard flow; App.js renders its own inline headers instead.
import React from 'react';

const Header = () => {
  return (
    <header className="bg-blue-600 text-white p-4 shadow-lg">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-2xl font-bold">Bruin AI Career Assistant</h1>
        <nav>
          <a href="/" className="hover:text-blue-200 transition-colors">
            Dashboard
          </a>
        </nav>
      </div>
    </header>
  );
};

export default Header;