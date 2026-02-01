import React from 'react';
import { TaskList } from './TaskList';
import { TaskSelectionPanel } from './TaskSelectionPanel';
import { TaskActions } from './TaskActions';
import { useTasks } from '../hooks/useTasks';

export const Layout: React.FC = () => {
  const {
    tasks,
    selectedTask,
    selectedTaskId,
    isLoading,
    error,
    filters,
    setSelectedTaskId,
    setFilters,
    startTask,
    stopTask,
    restartTask,
  } = useTasks();

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <svg
                  className="w-6 h-6 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Ultrawork</h1>
                <p className="text-sm text-gray-500">Task Management Dashboard</p>
              </div>
            </div>
            {isLoading && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
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
                <span>Loading...</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Error Message */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
            <svg className="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Task Selection Panel and Task List */}
          <div className="lg:col-span-2 space-y-6">
            {/* Task Selection Panel - Positioned at top with sticky for easy access */}
            <div className="sticky top-6 z-10">
              <TaskSelectionPanel
                tasks={tasks}
                selectedTaskId={selectedTaskId}
                onSelectTask={setSelectedTaskId}
                filters={filters}
                onFilterChange={setFilters}
              />
            </div>

            {/* Task List */}
            <TaskList
              tasks={tasks}
              selectedTaskId={selectedTaskId}
              onSelectTask={setSelectedTaskId}
            />
          </div>

          {/* Right Column - Task Actions */}
          <div className="lg:col-span-1">
            <div className="sticky top-6 space-y-6">
              {/* Selected Task Info */}
              {selectedTask ? (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {selectedTask.title}
                  </h3>
                  <p className="text-sm text-gray-600 mb-4">
                    {selectedTask.description}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span>ID: {selectedTask.id}</span>
                    <span>•</span>
                    <span>Priority: {selectedTask.priority}</span>
                  </div>
                </div>
              ) : (
                <div className="bg-gray-50 rounded-lg border border-gray-200 p-8 text-center">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-300 mb-3"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                    />
                  </svg>
                  <p className="text-sm text-gray-500">Select a task to view actions</p>
                </div>
              )}

              {/* Task Actions */}
              {selectedTask && (
                <TaskActions
                  task={selectedTask}
                  onStart={startTask}
                  onStop={stopTask}
                  onRestart={restartTask}
                />
              )}

              {/* Help Card */}
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-100 p-4">
                <h4 className="text-sm font-semibold text-blue-900 mb-2">
                  Quick Tips
                </h4>
                <ul className="text-xs text-blue-700 space-y-1">
                  <li>• Click a task to select it</li>
                  <li>• Use filters to find tasks quickly</li>
                  <li>• Start/Stop buttons control task execution</li>
                  <li>• Restart resets and starts a task</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
