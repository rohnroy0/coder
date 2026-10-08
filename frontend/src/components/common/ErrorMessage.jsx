import React from 'react';
import { AlertCircle, X } from 'lucide-react';

export const ErrorMessage = ({ message, onClose }) => {
  if (!message) return null;

  return (
    <div className="flex items-center justify-between p-4 mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg shadow-xs">
      <div className="flex items-center space-x-2">
        <AlertCircle className="w-5 h-5 text-red-500 shrink-0" />
        <span>{message}</span>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="p-1 text-red-500 hover:text-red-700 hover:bg-red-100 rounded-md transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;
