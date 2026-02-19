import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
    // Log error to error tracking service
    this.logError(error, errorInfo);
  }

  private logError = (error: Error, _errorInfo: ErrorInfo) => {
    // In a real application, you would send this to an error tracking service
    // like Sentry, Bugsnag, etc.
    if (process.env.NODE_ENV === 'development') {
      console.error('Error caught by boundary:', error);
    }
    
    // Here you could integrate with error tracking services
    // Example: Sentry.captureException(error, { contexts: { react: _errorInfo } });
  };

  private resetError = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      // If a fallback component is provided, use it
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return <FallbackComponent error={this.state.error!} resetError={this.resetError} />;
      }

      // Default fallback UI
      return (
        <div className="error-boundary p-4 bg-red-50 border border-red-200 rounded-lg">
          <h2 className="text-xl font-bold text-red-800 mb-2">Something went wrong.</h2>
          <details className="whitespace-pre-wrap text-sm text-red-700 mb-4">
            {this.state.error && this.state.error.toString()}
          </details>
          <button 
            onClick={this.resetError}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;