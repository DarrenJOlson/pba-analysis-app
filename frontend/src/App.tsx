import React from 'react';
import PBAAnalysisApp from './components/PBAAnalysisApp';

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-blue-800 text-white py-4">
        <div className="max-w-6xl mx-auto px-4">
          <h1 className="text-2xl font-bold">PBA Tournament Analysis System</h1>
          <p className="text-blue-200">Track performance, analyze patterns, and predict results</p>
        </div>
      </header>
      
      <main className="py-6">
        <PBAAnalysisApp />
      </main>
      
      <footer className="bg-gray-800 text-white py-4 mt-8">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p>&copy; {new Date().getFullYear()} PBA Tournament Analysis - Data Analysis Project</p>
        </div>
      </footer>
    </div>
  );
};

export default App;
