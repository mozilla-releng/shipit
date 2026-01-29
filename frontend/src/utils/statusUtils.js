export const getAutomationStatus = (automation) =>
  automation.status.toLowerCase();

export const hasAnyStatus = (automation, statuses) =>
  statuses.includes(getAutomationStatus(automation));

export const canCancel = (automation) =>
  hasAnyStatus(automation, ['scheduled', 'running', 'pending', 'failed']);

export const shouldPoll = (automation) =>
  hasAnyStatus(automation, ['running', 'failed']) && automation.task_id;

export const isPending = (automation) =>
  getAutomationStatus(automation) === 'pending';
