export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'stopped';

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  createdAt: Date;
  updatedAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  duration?: number; // in seconds
  priority: 'low' | 'medium' | 'high';
  tags: string[];
}

export interface TaskFilter {
  status?: TaskStatus;
  priority?: 'low' | 'medium' | 'high';
  tags?: string[];
}

export interface TaskActionsProps {
  task: Task;
  onStart: (taskId: string) => void;
  onStop: (taskId: string) => void;
  onRestart: (taskId: string) => void;
}

export interface TaskListProps {
  tasks: Task[];
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
}

export interface TaskSelectionPanelProps {
  tasks: Task[];
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
  filters: TaskFilter;
  onFilterChange: (filters: TaskFilter) => void;
}
