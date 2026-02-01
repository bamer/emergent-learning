import React, { useState, useCallback } from 'react';
import type { TaskActionsProps } from '../types';

export const TaskActions: React.FC<TaskActionsProps> = ({
  task,
  onStart,
  onStop,
  onRestart,
}) => {
  // Local state to track if task is running for button display
  const [isRunning, setIsRunning] = useState(task.status === 'running');
  const [isLoading, setIsLoading] = useState(false);

  // Update isRunning when task status changes
  React.useEffect(() => {
    setIsRunning(task.status === 'running');
  }, [task.status]);

  // Handle Start/Stop toggle
  const handleToggle = useCallback(async () => {
    if (isLoading) return;
    
    setIsLoading(true);
    try {
      if (isRunning) {
        await onStop(task.id);
        setIsRunning(false);
      } else {
        await onStart(task.id);
        setIsRunning(true);
      }
    } catch (error) {
      console.error('Failed to toggle task:', error);
    } finally {
      setIsLoading(false);
    }
  }, [isRunning, isLoading, task.id, onStart, onStop]);

  // Handle Restart
  const handleRestart = useCallback(async () => {
    if (isLoading) return;
    
    setIsLoading(true);
    try {
      await onRestart(task.id);
      setIsRunning(true);
    } catch (error) {
      console.error('Failed to restart task:', error);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, task.id, onRestart]);

  // Determine button states
  const canStart = task.status === 'pending' || task.status === 'stopped' || task.status === 'failed';
  const canStop = task.status === 'running';
  const canRestart = task.status === 'stopped' || task.status === 'failed' || task.status === 'completed';

  // Button is enabled if we can start or stop
  const isToggleEnabled = canStart || canStop;

  return (
    <div className="flex items-center gap-3 p-4 bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Start/Stop Toggle Button */}
      <button
        onClick={handleToggle}
        disabled={!isToggleEnabled || isLoading}
        className={`
          px-6 py-2.5 rounded-lg font-semibold text-sm
          transition-all duration-200 ease-in-out
          flex items-center gap-2
          ${isRunning
            ? 'bg-red-500 hover:bg-red-600 text-white shadow-red-200'
            : 'bg-emerald-500 hover:bg-emerald-600 text-white shadow-emerald-200'
          }
          ${!isToggleEnabled || isLoading
            ? 'opacity-50 cursor-not-allowed shadow-none'
            : 'shadow-lg hover:shadow-xl transform hover:-translate-y-0.5'
          }
        `}
      >
        {isLoading ? (
          <>
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span>Processing...</span>
          </>
        ) : isRunning ? (
          <>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <rect x="6" y="6" width="12" height="12" rx="2" strokeWidth="2" />
            </svg>
            <span>Stop</span>
          </>
        ) : (
          <>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <polygon points="5 3 19 12 5 21 5 3" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>Start</span>
          </>
        )}
      </button>

      {/* Restart Button */}
      <button
        onClick={handleRestart}
        disabled={!canRestart || isLoading}
        className={`
          px-6 py-2.5 rounded-lg font-semibold text-sm
          transition-all duration-200 ease-in-out
          flex items-center gap-2
          bg-amber-400 hover:bg-amber-500 text-amber-900
          ${!canRestart || isLoading
            ? 'opacity-50 cursor-not-allowed shadow-none'
            : 'shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 shadow-amber-200'
          }
        `}
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
        <span>Restart</span>
      </button>

      {/* Status Indicator */}
      <div className="ml-auto flex items-center gap-2">
        <span className="text-sm text-gray-500">Status:</span>
        <span
          className={`
            px-3 py-1 rounded-full text-xs font-medium
            ${task.status === 'running'
              ? 'bg-green-100 text-green-800'
              : task.status === 'pending'
              ? 'bg-gray-100 text-gray-800'
              : task.status === 'completed'
              ? 'bg-blue-100 text-blue-800'
              : task.status === 'failed'
              ? 'bg-red-100 text-red-800'
              : 'bg-yellow-100 text-yellow-800'
            }
          `}
        >
          {task.status.charAt(0).toUpperCase() + task.status.slice(1)}
        </span>
      </div>
    </div>
  );
};
