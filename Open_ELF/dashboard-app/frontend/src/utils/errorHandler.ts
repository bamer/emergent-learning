// Error classification types
export type ErrorType = 'USER_ERROR' | 'SYSTEM_ERROR' | 'NETWORK_ERROR' | 'VALIDATION_ERROR';

export interface AppError extends Error {
  type: ErrorType;
  context?: Record<string, unknown>;
  timestamp: Date;
}

// Create a custom error class
export class CustomAppError extends Error implements AppError {
  type: ErrorType;
  context?: Record<string, unknown>;
  timestamp: Date;

  constructor(
    message: string,
    type: ErrorType = 'SYSTEM_ERROR',
    context?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'CustomAppError';
    this.type = type;
    this.context = context;
    this.timestamp = new Date();
    
    // Maintains proper stack trace for where our error was thrown
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, CustomAppError);
    }
  }
}

// Error handler utility functions
export const errorHandler = {
  // Log error to console
  logError: (error: Error, context?: Record<string, unknown>): void => {
    if (process.env.NODE_ENV === 'development') {
      console.error('Application Error:', error);
      if (context) {
        console.error('Error Context:', context);
      }
    }
    
    // In production, you would send this to an error tracking service
    // Example: Sentry.captureException(error, { contexts: { app: context } });
  },

  // Classify error type
  classifyError: (error: Error): ErrorType => {
    // Network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      return 'NETWORK_ERROR';
    }
    
    // Validation errors
    if (error.name === 'ValidationError' || error.message.includes('validation')) {
      return 'VALIDATION_ERROR';
    }
    
    // User errors (based on status codes or custom properties)
    if ((error as any).statusCode >= 400 && (error as any).statusCode < 500) {
      return 'USER_ERROR';
    }
    
    // Default to system error
    return 'SYSTEM_ERROR';
  },

  // Generate user-friendly error message
  getUserFriendlyMessage: (error: Error): string => {
    const errorType = errorHandler.classifyError(error);
    
    switch (errorType) {
      case 'NETWORK_ERROR':
        return 'Unable to connect to the server. Please check your internet connection and try again.';
      case 'VALIDATION_ERROR':
        return error.message || 'Please check your input and try again.';
      case 'USER_ERROR':
        return error.message || 'An error occurred with your request. Please try again.';
      case 'SYSTEM_ERROR':
      default:
        return 'An unexpected error occurred. Please try again later.';
    }
  },

  // Handle API errors
  handleApiError: async (response: Response): Promise<void> => {
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      
      try {
        const errorData = await response.json();
        if (errorData.message) {
          errorMessage = errorData.message;
        }
      } catch (e) {
        // If parsing fails, use the default message
      }
      
      const error = new CustomAppError(
        errorMessage,
        response.status >= 400 && response.status < 500 ? 'USER_ERROR' : 'SYSTEM_ERROR',
        { statusCode: response.status, url: response.url }
      );
      
      errorHandler.logError(error);
      throw error;
    }
  },

  // Create error with context
  createError: (
    message: string,
    type: ErrorType = 'SYSTEM_ERROR',
    context?: Record<string, unknown>
  ): CustomAppError => {
    return new CustomAppError(message, type, context);
  }
};

export default errorHandler;