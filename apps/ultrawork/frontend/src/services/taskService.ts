import type { Task, TaskStatus } from '../types';

// Simulated API calls - replace with actual API endpoints
const API_BASE_URL = '/api/tasks';

export const taskService = {
  async getTasks(): Promise<Task[]> {
    // Simulated data - replace with actual API call
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([
          {
            id: '1',
            title: 'Design System Implementation',
            description: 'Create a comprehensive design system for the application',
            status: 'pending',
            createdAt: new Date('2026-01-15'),
            updatedAt: new Date('2026-01-15'),
            priority: 'high',
            tags: ['design', 'frontend'],
          },
          {
            id: '2',
            title: 'API Integration',
            description: 'Integrate with backend APIs',
            status: 'running',
            createdAt: new Date('2026-01-14'),
            updatedAt: new Date('2026-01-16'),
            startedAt: new Date('2026-01-16'),
            priority: 'high',
            tags: ['api', 'backend'],
          },
          {
            id: '3',
            title: 'Unit Tests',
            description: 'Write comprehensive unit tests',
            status: 'completed',
            createdAt: new Date('2026-01-10'),
            updatedAt: new Date('2026-01-13'),
            startedAt: new Date('2026-01-11'),
            completedAt: new Date('2026-01-13'),
            duration: 172800,
            priority: 'medium',
            tags: ['testing'],
          },
          {
            id: '4',
            title: 'Bug Fixes',
            description: 'Fix reported bugs from QA',
            status: 'failed',
            createdAt: new Date('2026-01-12'),
            updatedAt: new Date('2026-01-14'),
            startedAt: new Date('2026-01-13'),
            priority: 'high',
            tags: ['bugfix', 'qa'],
          },
          {
            id: '5',
            title: 'Documentation',
            description: 'Update project documentation',
            status: 'stopped',
            createdAt: new Date('2026-01-11'),
            updatedAt: new Date('2026-01-15'),
            startedAt: new Date('2026-01-12'),
            priority: 'low',
            tags: ['docs'],
          },
        ]);
      }, 500);
    });
  },

  async startTask(taskId: string): Promise<Task> {
    // Replace with actual API call
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          id: taskId,
          title: 'Task ' + taskId,
          description: 'Task description',
          status: 'running',
          createdAt: new Date(),
          updatedAt: new Date(),
          startedAt: new Date(),
          priority: 'medium',
          tags: [],
        });
      }, 300);
    });
  },

  async stopTask(taskId: string): Promise<Task> {
    // Replace with actual API call
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          id: taskId,
          title: 'Task ' + taskId,
          description: 'Task description',
          status: 'stopped',
          createdAt: new Date(),
          updatedAt: new Date(),
          startedAt: new Date(),
          priority: 'medium',
          tags: [],
        });
      }, 300);
    });
  },

  async restartTask(taskId: string): Promise<Task> {
    // Replace with actual API call
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          id: taskId,
          title: 'Task ' + taskId,
          description: 'Task description',
          status: 'running',
          createdAt: new Date(),
          updatedAt: new Date(),
          startedAt: new Date(),
          priority: 'medium',
          tags: [],
        });
      }, 300);
    });
  },

  canStartTask(status: TaskStatus): boolean {
    return status === 'pending' || status === 'stopped' || status === 'failed';
  },

  canStopTask(status: TaskStatus): boolean {
    return status === 'running';
  },

  canRestartTask(status: TaskStatus): boolean {
    return status === 'stopped' || status === 'failed' || status === 'completed';
  },
};
