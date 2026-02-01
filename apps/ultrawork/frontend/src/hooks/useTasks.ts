import { useState, useEffect, useCallback, useMemo } from 'react';
import type { Task, TaskFilter, TaskStatus } from '../types';
import { taskService } from '../services/taskService';

interface UseTasksReturn {
  tasks: Task[];
  selectedTask: Task | null;
  selectedTaskId: string | null;
  isLoading: boolean;
  error: string | null;
  filters: TaskFilter;
  canStart: boolean;
  canStop: boolean;
  canRestart: boolean;
  setSelectedTaskId: (taskId: string | null) => void;
  setFilters: (filters: TaskFilter) => void;
  startTask: (taskId: string) => Promise<void>;
  stopTask: (taskId: string) => Promise<void>;
  restartTask: (taskId: string) => Promise<void>;
  refreshTasks: () => Promise<void>;
}

export function useTasks(): UseTasksReturn {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<TaskFilter>({});

  // Fetch tasks on mount
  useEffect(() => {
    refreshTasks();
  }, []);

  const refreshTasks = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const fetchedTasks = await taskService.getTasks();
      setTasks(fetchedTasks);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tasks');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Get selected task
  const selectedTask = useMemo(() => {
    return tasks.find((task) => task.id === selectedTaskId) || null;
  }, [tasks, selectedTaskId]);

  // Compute canStart flag - enabled when task is pending
  const canStart = useMemo(() => {
    if (!selectedTask) return false;
    return taskService.canStartTask(selectedTask.status);
  }, [selectedTask]);

  // Compute canStop flag - enabled when task is running
  const canStop = useMemo(() => {
    if (!selectedTask) return false;
    return taskService.canStopTask(selectedTask.status);
  }, [selectedTask]);

  // Compute canRestart flag
  const canRestart = useMemo(() => {
    if (!selectedTask) return false;
    return taskService.canRestartTask(selectedTask.status);
  }, [selectedTask]);

  // Start task operation
  const startTask = useCallback(async (taskId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const updatedTask = await taskService.startTask(taskId);
      setTasks((prevTasks) =>
        prevTasks.map((task) =>
          task.id === taskId ? updatedTask : task
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start task');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Stop task operation
  const stopTask = useCallback(async (taskId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const updatedTask = await taskService.stopTask(taskId);
      setTasks((prevTasks) =>
        prevTasks.map((task) =>
          task.id === taskId ? updatedTask : task
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop task');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Restart task operation
  const restartTask = useCallback(async (taskId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const updatedTask = await taskService.restartTask(taskId);
      setTasks((prevTasks) =>
        prevTasks.map((task) =>
          task.id === taskId ? updatedTask : task
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to restart task');
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    tasks,
    selectedTask,
    selectedTaskId,
    isLoading,
    error,
    filters,
    canStart,
    canStop,
    canRestart,
    setSelectedTaskId,
    setFilters,
    startTask,
    stopTask,
    restartTask,
    refreshTasks,
  };
}
