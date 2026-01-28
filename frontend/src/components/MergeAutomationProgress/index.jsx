import CancelIcon from '@mui/icons-material/Block';
import LaunchIcon from '@mui/icons-material/Launch';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Divider from '@mui/material/Divider';
import Link from '@mui/material/Link';
import { styled } from '@mui/material/styles';
import Typography from '@mui/material/Typography';
import React, { useState } from 'react';
import { canCancel, isPending, shouldPoll } from '../../utils/statusUtils';

const StyledCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(2),
}));

const CommitBox = styled(Box)(({ theme }) => ({
  backgroundColor: theme.palette.grey[50],
  border: `1px solid ${theme.palette.grey[200]}`,
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(1.5),
  marginBottom: theme.spacing(2),
}));

const TaskStatusSection = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  padding: theme.spacing(1),
  backgroundColor: theme.palette.grey[50],
  borderRadius: theme.shape.borderRadius,
  border: `1px solid ${theme.palette.grey[200]}`,
}));

const StatusLink = styled(Link)(({ theme }) => ({
  color: theme.palette.primary.main,
  textDecoration: 'none',
  fontFamily: 'monospace',
  display: 'inline-flex',
  alignItems: 'center',
  gap: theme.spacing(0.5),
  '&:hover': {
    textDecoration: 'underline',
  },
}));

const SectionLink = styled(Link)(({ theme }) => ({
  fontSize: '0.75rem',
  fontWeight: 600,
  color: theme.palette.text.secondary,
  textTransform: 'uppercase',
  textDecoration: 'none',
  '&:hover': {
    textDecoration: 'underline',
  },
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(0.5),
}));

const SectionLabel = styled(Typography)(({ theme }) => ({
  fontSize: '0.75rem',
  fontWeight: 600,
  color: theme.palette.text.secondary,
  textTransform: 'uppercase',
}));

const StatusValue = styled(Typography)(({ theme, color }) => ({
  fontSize: '0.875rem',
  fontWeight: 500,
  color: theme.palette[color]?.dark,
}));

function getStatusColor(status) {
  const statusMap = {
    completed: 'success',
    running: 'info',
    failed: 'error',
    scheduled: 'warning',
    pending: 'default',
  };
  return statusMap[status?.toLowerCase()] || 'default';
}

export default function MergeAutomationProgress({
  automation,
  onCancel,
  onStart,
}) {
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  const taskStatus = automation.taskStatus;
  const taskStatusError = automation.taskStatusError;

  const handleCancel = async () => {
    setIsCancelling(true);
    try {
      if (onCancel) await onCancel(automation.id);
    } finally {
      setIsCancelling(false);
    }
    setShowCancelDialog(false);
  };

  const handleStart = async () => {
    setIsStarting(true);
    try {
      if (onStart) await onStart(automation.id);
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <>
      <StyledCard>
        <CardContent>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              mb: 2,
            }}
          >
            <Box sx={{ flex: 1 }}>
              <Box
                sx={{
                  fontWeight: 600,
                  fontSize: '1.125rem',
                  mb: 0.5,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                }}
              >
                <Box
                  sx={{
                    width: 2,
                    height: 20,
                    backgroundColor: (theme) => {
                      const color = getStatusColor(automation.status);
                      return (
                        theme.palette[color]?.dark || theme.palette.grey[500]
                      );
                    },
                  }}
                />
                {automation.dry_run && (
                  <Chip
                    label="Dry Run"
                    size="small"
                    sx={{ fontWeight: 600, fontSize: '0.8rem', height: 20 }}
                  />
                )}
                <Divider orientation="vertical" flexItem />
                <Typography
                  component="span"
                  sx={{ fontWeight: 600, fontSize: '1.125rem' }}
                >
                  {automation.pretty_name}
                </Typography>
              </Box>
              <Box
                sx={{
                  color: 'text.secondary',
                  fontSize: '0.875rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                }}
              >
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {automation.version}
                </Typography>
                <Divider orientation="vertical" flexItem />
                <Typography variant="body2">
                  Created{' '}
                  {new Date(automation.created).toLocaleDateString('en-US')}
                </Typography>
                <Divider orientation="vertical" flexItem />
                <StatusLink
                  href={`${automation.repo}/rev/${automation.revision}`}
                  target="_blank"
                >
                  {automation.revision.slice(0, 12)}
                  <LaunchIcon fontSize="inherit" />
                </StatusLink>
              </Box>
            </Box>
            <Chip
              label={automation.status}
              color={getStatusColor(automation.status)}
              size="small"
              sx={{ fontWeight: 600, fontSize: '0.8rem', height: 28 }}
            />
          </Box>

          <CommitBox>
            <Typography
              sx={{
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                lineHeight: 1.4,
                mb: 0.5,
              }}
            >
              {automation.commit_message}
            </Typography>
            <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>
              by {automation.commit_author}
            </Typography>
          </CommitBox>

          {shouldPoll(automation) && (
            <TaskStatusSection>
              <Typography
                variant="h6"
                sx={{ fontSize: '0.875rem', fontWeight: 600, mb: 1 }}
              >
                Taskcluster status
              </Typography>
              {taskStatusError ? (
                <Typography color="error" variant="body2">
                  Error loading task status: {taskStatusError}
                </Typography>
              ) : taskStatus ? (
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: 2,
                  }}
                >
                  <Box
                    sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}
                  >
                    <SectionLink
                      href={`https://firefox-ci-tc.services.mozilla.com/tasks/${automation.task_id}`}
                      target="_blank"
                    >
                      Decision Task
                      <LaunchIcon fontSize="inherit" />
                    </SectionLink>
                    <StatusValue
                      color={getStatusColor(taskStatus.decisionTask?.state)}
                    >
                      {taskStatus.decisionTask?.state || 'Loading...'}
                    </StatusValue>
                  </Box>
                  <Box
                    sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}
                  >
                    {taskStatus.taskGroup?.overallStatus &&
                    taskStatus.taskGroup.overallStatus !== 'pending' ? (
                      <SectionLink
                        href={`https://firefox-ci-tc.services.mozilla.com/tasks/groups/${automation.task_id}`}
                        target="_blank"
                      >
                        Task Group
                        <LaunchIcon fontSize="inherit" />
                      </SectionLink>
                    ) : (
                      <SectionLabel>Task Group</SectionLabel>
                    )}
                    <StatusValue
                      color={getStatusColor(
                        taskStatus.taskGroup?.overallStatus,
                      )}
                    >
                      {taskStatus.taskGroup?.overallStatus || 'Not created yet'}
                    </StatusValue>
                  </Box>
                </Box>
              ) : (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={16} />
                  <Typography variant="body2">
                    Loading task status...
                  </Typography>
                </Box>
              )}
            </TaskStatusSection>
          )}

          {automation.completed && (
            <Box sx={{ mb: 2 }}>
              <SectionLink
                href={`https://firefox-ci-tc.services.mozilla.com/tasks/groups/${automation.task_id}`}
                target="_blank"
              >
                Completed
                <LaunchIcon fontSize="inherit" />
              </SectionLink>
              <Typography sx={{ fontSize: '0.875rem' }}>
                {new Date(automation.completed).toLocaleString('en-US', {
                  timeZoneName: 'short',
                })}
              </Typography>
            </Box>
          )}

          <Box
            sx={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: 1,
              pt: 1,
              borderTop: 1,
              borderColor: 'grey.200',
            }}
          >
            {isPending(automation) && (
              <Button
                startIcon={<PlayArrowIcon />}
                color="primary"
                variant="contained"
                onClick={handleStart}
                disabled={isStarting}
              >
                {isStarting ? <CircularProgress size={16} /> : 'Start'}
              </Button>
            )}
            {canCancel(automation) && (
              <Button
                startIcon={<CancelIcon />}
                color="error"
                variant="outlined"
                onClick={() => setShowCancelDialog(true)}
                disabled={isCancelling}
              >
                {isCancelling ? <CircularProgress size={16} /> : 'Cancel'}
              </Button>
            )}
          </Box>
        </CardContent>
      </StyledCard>

      <Dialog
        open={showCancelDialog}
        onClose={() => setShowCancelDialog(false)}
      >
        <DialogTitle>Cancel Merge Automation</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to cancel the merge automation{' '}
            <strong>"{automation.pretty_name}"</strong> for revision{' '}
            <code>{automation.revision.slice(0, 12)}</code>?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCancelDialog(false)} variant="outlined">
            Close
          </Button>
          <Button
            onClick={handleCancel}
            color="error"
            variant="contained"
            autoFocus
          >
            Cancel
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
