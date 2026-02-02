import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Switch from '@mui/material/Switch';
import { styled } from '@mui/material/styles';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router';
import Dashboard from '../../components/Dashboard';
import ErrorPanel from '../../components/ErrorPanel';
import {
  getMergeBehaviors,
  getMergeInfo,
  getMergeRevisions,
  prettyProductName,
  submitMergeAutomation,
} from '../../components/merge_automation';
import maybeShorten from '../../components/text';
import useAction from '../../hooks/useAction';

const StyledFormControl = styled(FormControl)(({ theme }) => ({
  margin: theme.spacing(1),
  width: '100%',
}));

const CommitInfoBox = styled(Box)(({ theme }) => ({
  marginTop: theme.spacing(1),
  borderLeft: `3px solid ${theme.palette.grey[400]}`,
  paddingLeft: theme.spacing(3),
}));

export default function NewMergeAutomation() {
  const location = useLocation();
  const navigate = useNavigate();
  const product =
    new URLSearchParams(location.search).get('product') || 'firefox';

  const [mergeBehaviors, setMergeBehaviors] = useState(null);
  const [mergeRevisions, setMergeRevisions] = useState({});
  const [selectedRevision, setSelectedRevision] = useState('');
  const [selectedBehavior, setSelectedBehavior] = useState('');
  const [dryRun, setDryRun] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [error, setError] = useState(null);
  const [revisionInfo, setRevisionInfo] = useState(null);

  const [submitMergeAutomationState, submitMergeAutomationAction] = useAction(
    submitMergeAutomation,
  );

  useEffect(() => {
    async function updateMergeBehaviors() {
      try {
        const behaviors = await getMergeBehaviors(product);
        setMergeBehaviors(behaviors);
      } catch (e) {
        setError(
          `Failed to fetch merge behaviors for product ${product}: ${e.toString()}`,
        );
      }
    }
    setError(null);
    setMergeBehaviors(null);
    setMergeRevisions({});
    setSelectedBehavior('');
    setSelectedRevision('');
    setDryRun(true);
    setDialogOpen(false);

    updateMergeBehaviors();
  }, [product]);

  useEffect(() => {
    if (selectedBehavior === '' || !mergeBehaviors) {
      return;
    }

    const abortController = new AbortController();

    async function updateMergeRevisions() {
      try {
        const behaviorConfig = mergeBehaviors[selectedBehavior];
        const newMergeRevisions = await getMergeRevisions(
          behaviorConfig,
          abortController.signal,
        );
        setMergeRevisions(newMergeRevisions);

        if (Object.keys(newMergeRevisions).length === 1) {
          setSelectedRevision(Object.keys(newMergeRevisions)[0]);
        }
      } catch (e) {
        if (e.message === 'canceled') {
          return;
        }
        setError(
          `Failed to fetch merge commits for product ${product} and behavior ${selectedBehavior}: ${e.toString()}`,
        );
      }
    }

    setMergeRevisions({});
    setSelectedRevision('');
    setDialogOpen(false);
    setRevisionInfo(null);
    setError(null);
    updateMergeRevisions();

    return () => {
      abortController.abort();
    };
  }, [selectedBehavior, mergeBehaviors]);

  useEffect(() => {
    if (selectedRevision === '' || !mergeBehaviors || !selectedBehavior) {
      setRevisionInfo(null);
      return;
    }

    const abortController = new AbortController();

    async function updateRevisionInfo() {
      try {
        const behaviorConfig = mergeBehaviors[selectedBehavior];
        const info = await getMergeInfo(
          behaviorConfig,
          selectedRevision,
          abortController.signal,
        );
        setRevisionInfo(info);
      } catch (e) {
        if (e.message === 'canceled') {
          return;
        }
        setError(
          `Failed to fetch revision info for ${selectedRevision}: ${e.toString()}`,
        );
      }
    }

    setRevisionInfo(null);
    setError(null);
    updateRevisionInfo();

    return () => {
      abortController.abort();
    };
  }, [selectedRevision, selectedBehavior, mergeBehaviors]);

  function renderMergeBehaviors() {
    if (mergeBehaviors === null) {
      if (error !== null) {
        return null;
      }

      return <CircularProgress sx={{ margin: 'auto' }} />;
    }

    return (
      <Box display="flex" gap={2}>
        <InputLabel>Behavior</InputLabel>
        <Select
          sx={{ flexGrow: 1 }}
          variant="standard"
          value={selectedBehavior}
          onChange={(event) => setSelectedBehavior(event.target.value)}
        >
          {Object.entries(mergeBehaviors).map(([name, behavior]) => (
            <MenuItem value={name} key={name}>
              {behavior.pretty_name}
            </MenuItem>
          ))}
        </Select>
        <FormControlLabel
          control={
            <Switch
              checked={dryRun}
              onChange={(e) => setDryRun(e.target.checked)}
              disabled={selectedBehavior === ''}
              color="secondary"
            />
          }
          label={
            <Box>
              <Typography variant="body1">Dry Run</Typography>
            </Box>
          }
        />
      </Box>
    );
  }

  function renderMergeRevisions() {
    if (Object.keys(mergeRevisions).length === 0) {
      if (error !== null) {
        return null;
      }
      return <CircularProgress sx={{ display: 'block', margin: 'auto' }} />;
    }

    const uniqueRevision = Object.keys(mergeRevisions).length === 1;
    const revisionPretty = (rev, sha) => {
      return `${rev.date.toDateString()} - ${sha.substring(0, 8)} - ${
        rev.author
      } - ${maybeShorten(rev.desc)}`;
    };

    return (
      <Autocomplete
        disabled={uniqueRevision}
        freeSolo
        forcePopupIcon
        options={Object.keys(mergeRevisions)}
        value={selectedRevision}
        renderInput={(params) => (
          <TextField {...params} label="Revision" variant="outlined" />
        )}
        onInputChange={(_event, value) => setSelectedRevision(value)}
        renderOption={(props, option, _state) => (
          <div {...props}>
            {' '}
            {revisionPretty(mergeRevisions[option], option)}{' '}
          </div>
        )}
      />
    );
  }

  function renderRevisionInfo() {
    if (revisionInfo === null) {
      if (error !== null) {
        return null;
      }
      return <CircularProgress sx={{ display: 'block', margin: 'auto' }} />;
    }

    return (
      <Box>
        <Box>
          <Typography component="h3" variant="h6">
            Current version: {revisionInfo.version}
          </Typography>
        </Box>
        <CommitInfoBox>
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {revisionInfo.commit_message}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {revisionInfo.commit_author}
          </Typography>
        </CommitInfoBox>
      </Box>
    );
  }

  function okToSubmit() {
    return product && selectedBehavior && selectedRevision && revisionInfo;
  }

  const renderDialog = () => {
    return (
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogTitle>
          Create Merge Automation {dryRun ? '(Dry run)' : null}
        </DialogTitle>
        <DialogContent>
          Submitting will create a{' '}
          <Typography variant="inlineCode">{selectedBehavior}</Typography> merge
          automation for revision{' '}
          <Typography variant="inlineCode">{selectedRevision}</Typography>.
        </DialogContent>
        <DialogActions>
          {submitMergeAutomationState.loading && <CircularProgress />}
          <Button
            onClick={() => {
              setDialogOpen(false);
            }}
            autoFocus
            variant="contained"
          >
            Close
          </Button>
          <Button
            onClick={async () => {
              const result = await submitMergeAutomationAction(
                product,
                selectedBehavior,
                selectedRevision,
                dryRun,
                revisionInfo.version,
                revisionInfo.commit_message,
                revisionInfo.commit_author,
              );

              setDialogOpen(false);
              if (result.error !== null) {
                setError(
                  `Could not submit merge automation: ${result.error.toString()}`,
                );
              } else {
                await navigate('/merge-automation', {
                  state: {
                    successMessage: `Successfully created merge automation ${selectedBehavior} for ${product}`,
                  },
                });
              }
            }}
            // A user should not be be able to get the dialog open if this isn't true, but I'd better be safe than sorry.
            disabled={!okToSubmit()}
            color="primary"
            variant="contained"
          >
            Submit
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  return (
    <Dashboard
      group="Merge automation"
      title={`New (${prettyProductName(product)})`}
    >
      <ErrorPanel error={error} />
      <StyledFormControl variant="standard">
        {renderMergeBehaviors()}
        {selectedBehavior !== '' && (
          <Box sx={{ mt: 2 }}>{renderMergeRevisions()}</Box>
        )}
        {selectedRevision !== '' && (
          <Box sx={{ mt: 2 }}>{renderRevisionInfo()}</Box>
        )}

        <Box sx={{ mt: 3 }}>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={!okToSubmit()}
            onClick={() => {
              setDialogOpen(true);
            }}
            fullWidth
          >
            Submit
          </Button>
        </Box>
      </StyledFormControl>
      {renderDialog()}
    </Dashboard>
  );
}
