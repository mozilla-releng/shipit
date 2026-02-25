import RefreshIcon from '@mui/icons-material/Refresh';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import React, { useEffect, useState } from 'react';
import config from '../../config';
import useAction from '../../hooks/useAction';
import Link from '../../utils/Link';
import { checkDecisionTaskStatus } from '../api';

export default function DecisionTaskStatus({
  product,
  branch,
  revision,
  repoUrl,
  onStatusChange,
}) {
  const [checkState, checkAction] = useAction(checkDecisionTaskStatus);
  const [status, setStatus] = useState(null);

  async function check() {
    setStatus(null);
    const result = await checkAction(product, branch, revision, repoUrl);
    setStatus(result.data);
  }

  useEffect(() => {
    if (!revision) {
      setStatus(null);
      return;
    }
    check();
  }, [product, branch, revision, repoUrl]);

  useEffect(() => {
    if (onStatusChange) {
      onStatusChange(status);
    }
  }, [status]);

  if (!status && !checkState.loading) {
    return null;
  }

  const state = status?.state || 'checking...';
  const colorMap = { ready: 'success', missing: 'error' };
  const color = colorMap[state] || 'default';
  const taskUrl = status?.task_id
    ? `${config.TASKCLUSTER_ROOT_URL}/tasks/${status.task_id}`
    : null;

  return (
    <Typography component="h3" variant="h6">
      Decision task:
      <Box sx={{ ml: 1, display: 'inline' }}>
        {taskUrl ? (
          <Link to={taskUrl} nav={true}>
            <Chip label={state} color={color} size="small" />
          </Link>
        ) : (
          <Chip label={state} color={color} size="small" />
        )}
        <IconButton
          size="small"
          onClick={check}
          disabled={checkState.loading}
          title="Refresh status"
        >
          {checkState.loading ? (
            <CircularProgress size={16} />
          ) : (
            <RefreshIcon fontSize="small" />
          )}
        </IconButton>
      </Box>
    </Typography>
  );
}
