import React, { useState, useEffect } from 'react';

const STORAGE_KEY = 'hasSeenRenderNotice';

export default function RenderNoticeModal() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const hasSeen = localStorage.getItem(STORAGE_KEY);
    if (!hasSeen) {
      setIsOpen(true);
    }
  }, []);

  const handleClose = () => {
    localStorage.setItem(STORAGE_KEY, 'true');
    setIsOpen(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4 animate-in fade-in duration-200">
      <div className="bg-black/20 backdrop-blur-md border border-white/10 rounded-lg shadow-xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <h2 className="text-xl font-bold text-white">Welcome to F1 Dashboard</h2>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-all duration-200 text-gray-400 hover:text-white"
          >
            <span className="text-lg">✕</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <p className="text-gray-300 leading-relaxed">
            This site is hosted on <span className="text-white font-medium">Render</span>. 
            The backend may be asleep if no one has used it recently.
          </p>
          <p className="text-gray-300 leading-relaxed">
            <span className="text-amber-400 font-medium">Initial database load takes 1–2 minutes</span> on first request. 
            Please be patient while data loads — subsequent requests will be faster.
          </p>
          <p className="text-gray-400 text-sm leading-relaxed">
            On a paid plan, the service stays warm and this delay would not happen.
          </p>
        </div>

        {/* Footer */}
        <div className="p-6 pt-0">
          <button
            onClick={handleClose}
            className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-500 hover:to-blue-600 transition-all duration-200 font-medium"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}
