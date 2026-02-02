import RefreshIcon from '@mui/icons-material/Refresh';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import React, { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router';
import Dashboard from '../../components/Dashboard';
import ErrorPanel from '../../components/ErrorPanel';
import MergeAutomationProgress from '../../components/MergeAutomationProgress';
import {
  cancelMergeAutomation,
  getMergeAutomations,
  getMergeAutomationTaskStatus,
  prettyProductName,
  startMergeAutomation,
} from '../../components/merge_automation';
import useAction from '../../hooks/useAction';
import { shouldPoll } from '../../utils/statusUtils';

export default function ListMergeAutomation() {
  const location = useLocation();
  const product =
    new URLSearchParams(location.search).get('product') || 'firefox';
  const [error, setError] = useState(null);

  const [automations, fetchAutomations] = useAction(getMergeAutomations);
  const [automationsList, setAutomationsList] = useState(null);

  const runningAutomations = useMemo(
    () => automationsList?.filter(shouldPoll) || [],
    [automationsList],
  );

  useEffect(() => {
    fetchAutomations(product);
  }, [product]);

  useEffect(() => {
    if (automations.data) {
      setAutomationsList(automations.data);
    }
  }, [automations.data]);

  useEffect(() => {
    if (!automationsList) return;

    if (runningAutomations.length === 0) return;

    const pollTaskStatuses = async () => {
      for (const automation of runningAutomations) {
        try {
          const response = await getMergeAutomationTaskStatus(automation.id);

          setAutomationsList((prev) =>
            prev.map((a) =>
              a.id === automation.id
                ? {
                    ...a,
                    ...(response.automation || {}),
                    taskStatus: response,
                  }
                : a,
            ),
          );
        } catch (error) {
          // If 404, the automation was deleted. Remove it from the list so we don't poll it forever
          if (error.status === 404) {
            setAutomationsList((prev) =>
              prev.filter((a) => a.id !== automation.id),
            );
          } else {
            setAutomationsList((prev) =>
              prev.map((a) =>
                a.id === automation.id
                  ? { ...a, taskStatusError: error.message }
                  : a,
              ),
            );
          }
        }
      }
    };

    pollTaskStatuses();

    const interval = setInterval(pollTaskStatuses, 30000);
    return () => clearInterval(interval);
  }, [runningAutomations.length]);

  const handleRefresh = () => {
    fetchAutomations(product);
  };

  const handleCancel = async (automationId) => {
    try {
      await cancelMergeAutomation(automationId);
      // Refresh the list to remove the deleted automation
      fetchAutomations(product);
    } catch (error) {
      setError(`Failed to cancel automation: ${error.message || error}`);
    }
  };

  const handleStart = async (automationId) => {
    try {
      await startMergeAutomation(automationId);
      handleAutomationChange(automationId);
    } catch (error) {
      setError(`Failed to start automation: ${error.message || error}`);
    }
  };

  const handleAutomationChange = async (automationId) => {
    try {
      const response = await getMergeAutomationTaskStatus(automationId);
      setAutomationsList((prev) =>
        prev.map((a) =>
          a.id === automationId
            ? {
                ...a,
                ...(response.automation || {}),
                taskStatus: response,
              }
            : a,
        ),
      );
    } catch (error) {
      // If 404, the automation was deleted. Remove it from the list so we don't poll it forever
      if (error.status === 404) {
        setAutomationsList((prev) => prev.filter((a) => a.id !== automationId));
      } else {
        fetchAutomations(product);
      }
    }
  };

  return (
    <Dashboard group="Merge Automation" title={prettyProductName(product)}>
      <ErrorPanel error={error} />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
          mb: 2,
          mr: 1,
        }}
      >
        <Button startIcon={<RefreshIcon />} onClick={handleRefresh}>
          Refresh
        </Button>
      </Box>

      {automations.loading && (
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress />
        </Box>
      )}

      {automations.error && (
        <ErrorPanel
          error={automations.error.message || 'Failed to fetch automations'}
        />
      )}

      {automationsList && automationsList.length < 1 && (
        <h2>No merge automations found for {product}</h2>
      )}

      {automationsList?.map((automation) => (
        <MergeAutomationProgress
          key={automation.id}
          automation={automation}
          onCancel={handleCancel}
          onStart={handleStart}
        />
      ))}
    </Dashboard>
  );
}
