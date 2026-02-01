import React from 'react';
import type { TaskSelectionPanelProps } from '../types';

export const TaskSelectionPanel: React.FC<TaskSelectionPanelProps> = ({
  tasks,
  selectedTaskId,
  onSelectTask,
  filters,
  onFilterChange,
}) => {
  const statusOptions = ['pending', 'running', 'completed', 'failed', 'stopped'];
  const priorityOptions = ['low', 'medium', 'high'];

  // Get unique tags from all tasks
  const allTags = React.useMemo(() => {
    const tags = new Set<string>();
    tasks.forEach((task) => task.tags.forEach((tag) => tags.add(tag)));
    return Array.from(tags).sort();
  }, [tasks]);

  // Filtered tasks
  const filteredTasks = React.useMemo(() => {
    return tasks.filter((task) => {
      if (filters.status && task.status !== filters.status) return false;
      if (filters.priority && task.priority !== filters.priority) return false;
      if (filters.tags && filters.tags.length > 0) {
        const hasMatchingTag = filters.tags.some((tag) => task.tags.includes(tag));
        if (!hasMatchingTag) return false;
      }
      return true;
    });
  }, [tasks, filters]);

  const handleStatusFilter = (status: string | null) => {
    onFilterChange({ ...filters, status: status as any });
  };

  const handlePriorityFilter = (priority: string | null) => {
    onFilterChange({ ...filters, priority: priority as any });
  };

  const handleTagFilter = (tag: string) => {
    const currentTags = filters.tags || [];
    const newTags = currentTags.includes(tag)
      ? currentTags.filter((t) => t !== tag)
      : [...currentTags, tag];
    onFilterChange({ ...filters, tags: newTags.length > 0 ? newTags : undefined });
  };

  const clearFilters = () => {
    onFilterChange({});
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-800">Task Selection</h2>
        <p className="text-sm text-gray-500 mt-1">
          {filteredTasks.length} of {tasks.length} tasks
        </p>
      </div>

      <div className="p-4 space-y-4">
        {/* Status Filter */}
        <div>
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Status
          </label>
          <div className="mt-2 flex flex-wrap gap-2">
            <button
              onClick={() => handleStatusFilter(null)}
              className={`
                px-3 py-1.5 rounded-full text-xs font-medium transition-colors
                ${!filters.status
                  ? 'bg-gray-800 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }
              `}
            >
              All
            </button>
            {statusOptions.map((status) => (
              <button
                key={status}
                onClick={() => handleStatusFilter(status)}
                className={`
                  px-3 py-1.5 rounded-full text-xs font-medium transition-colors capitalize
                  ${filters.status === status
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }
                `}
              >
                {status}
              </button>
            ))}
          </div>
        </div>

        {/* Priority Filter */}
        <div>
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Priority
          </label>
          <div className="mt-2 flex flex-wrap gap-2">
            <button
              onClick={() => handlePriorityFilter(null)}
              className={`
                px-3 py-1.5 rounded-full text-xs font-medium transition-colors
                ${!filters.priority
                  ? 'bg-gray-800 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }
              `}
            >
              All
            </button>
            {priorityOptions.map((priority) => (
              <button
                key={priority}
                onClick={() => handlePriorityFilter(priority)}
                className={`
                  px-3 py-1.5 rounded-full text-xs font-medium transition-colors capitalize
                  ${filters.priority === priority
                    ? priority === 'high'
                      ? 'bg-red-600 text-white'
                      : priority === 'medium'
                      ? 'bg-amber-500 text-white'
                      : 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }
                `}
              >
                {priority}
              </button>
            ))}
          </div>
        </div>

        {/* Tags Filter */}
        {allTags.length > 0 && (
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Tags
            </label>
            <div className="mt-2 flex flex-wrap gap-2">
              {allTags.map((tag) => (
                <button
                  key={tag}
                  onClick={() => handleTagFilter(tag)}
                  className={`
                    px-3 py-1.5 rounded-full text-xs font-medium transition-colors
                    ${filters.tags?.includes(tag)
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }
                  `}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Clear Filters */}
        {(filters.status || filters.priority || (filters.tags && filters.tags.length > 0)) && (
          <button
            onClick={clearFilters}
            className="w-full py-2 text-sm text-gray-600 hover:text-gray-800 
                       border border-gray-300 rounded-lg hover:bg-gray-50
                       transition-colors"
          >
            Clear Filters
          </button>
        )}

        {/* Quick Select */}
        <div className="pt-4 border-t border-gray-200">
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Quick Select
          </label>
          <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
            {filteredTasks.map((task) => (
              <button
                key={task.id}
                onClick={() => onSelectTask(task.id)}
                className={`
                  w-full text-left px-3 py-2 rounded-lg text-sm
                  transition-colors
                  ${selectedTaskId === task.id
                    ? 'bg-blue-100 text-blue-800 border border-blue-300'
                    : 'hover:bg-gray-100 text-gray-700'
                  }
                `}
              >
                <div className="flex items-center gap-2">
                  <div
                    className={`
                      w-2 h-2 rounded-full
                      ${task.status === 'running'
                        ? 'bg-green-500'
                        : task.status === 'pending'
                        ? 'bg-gray-400'
                        : task.status === 'completed'
                        ? 'bg-blue-500'
                        : task.status === 'failed'
                        ? 'bg-red-500'
                        : 'bg-yellow-500'
                      }
                    `}
                  />
                  <span className="truncate">{task.title}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
