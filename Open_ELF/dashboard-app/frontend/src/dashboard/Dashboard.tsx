import React from 'react';
import { useState, useEffect } from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import errorHandler from '../utils/errorHandler';
import ErrorBoundary from '../components/ErrorBoundary';
import errorHandler, { CustomAppError } from '../utils/errorHandler';

// Mock component that might throw an error
const RiskyComponent = ({ shouldError }: { shouldError: boolean }) => {
  if (shouldError) {
    throw new Error('This is a simulated error!');
  }
  
  return <div className="p-4 bg-blue-50 rounded-lg">Dashboard Content</div>;
};

// Fallback component for error boundary
const ErrorFallback = ({ error, resetError }: { error: Error; resetError: () => void }) => {
  return (
    <div className="error-fallback p-6 bg-red-50 border border-red-200 rounded-lg text-center">
      <h2 className="text-2xl font-bold text-red-800 mb-2">Oops! Something went wrong.</h2>
      <p className="text-red-700 mb-4">We're sorry, but an unexpected error occurred.</p>
      <p className="text-red-600 mb-6">{error.message}</p>
      <div className="flex justify-center gap-4">
        <button 
          onClick={resetError}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
        <button 
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
        >
          Refresh Page
        </button>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [simulateError, setSimulateError] = useState(false);

  // Simulate async data fetching
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Simulate random error for demonstration
        if (Math.random() > 0.7) {
          throw errorHandler.createError(
            'Failed to fetch dashboard data',
            'NETWORK_ERROR',
            { endpoint: '/api/dashboard' }
          );
        }
        
        setLoading(false);
      } catch (error) {
        if (error instanceof Error) {
          const userMessage = errorHandler.getUserFriendlyMessage(error);
          setErrorMessage(userMessage);
          errorHandler.logError(error, { component: 'Dashboard', operation: 'fetchData' });
        }
        setHasError(true);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleRetry = () => {
    setHasError(false);
    setErrorMessage('');
    setSimulateError(false);
  };

  if (loading) {
    return (
      <div className="dashboard-loading flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-lg">Loading dashboard...</span>
      </div>
    );
  }

  return (
    <ErrorBoundary fallback={ErrorFallback}>
      <div className="dashboard p-6">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>
          <p className="text-gray-600">Welcome to your dashboard overview</p>
        </header>
        
        {hasError ? (
          <div className="dashboard-error p-6 bg-yellow-50 border border-yellow-200 rounded-lg text-center">
            <p className="text-yellow-800 mb-4">{errorMessage}</p>
            <button 
              onClick={handleRetry}
              className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : (
          <>
            <section className="dashboard-content mb-8">
              <RiskyComponent shouldError={simulateError} />
              <div className="mt-4">
                <button 
                  onClick={() => setSimulateError(true)}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                >
                  Simulate Component Error
                </button>
              </div>
            </section>
            
            <footer className="border-t pt-4">
              <p className="text-gray-500">Dashboard v1.0</p>
            </footer>
          </>
        )}
      </div>
    </ErrorBoundary>
  );
};

export default Dashboard;