import React from 'react';

interface ErrorDisplayProps {
  message: string;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ message }) => (
  <div className="bg-red-900/50 border border-red-600 text-red-300 px-4 py-3 rounded-lg relative max-w-2xl mx-auto" role="alert">
    <strong className="font-bold">发生错误!</strong>
    <span className="block sm:inline ml-2">{message}</span>
  </div>
);

export default ErrorDisplay;
