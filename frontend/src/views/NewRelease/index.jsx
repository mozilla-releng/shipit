import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Collapse from '@mui/material/Collapse';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControl from '@mui/material/FormControl';
import Grid from '@mui/material/Grid';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { DateTimePicker, LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { renderTimeViewClock } from '@mui/x-date-pickers/timeViewRenderers';
import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router';
import TimeAgo from 'react-timeago';
import { makeStyles } from 'tss-react/mui';
import {
  guessBuildNumber,
  guessPartialVersions,
  submitRelease,
} from '../../components/api';
import Dashboard from '../../components/Dashboard';
import DecisionTaskStatus from '../../components/DecisionTaskStatus';
import ErrorPanel from '../../components/ErrorPanel';
import maybeShorten from '../../components/text';
import {
  getBranches,
  getPushes,
  getVersion,
  isGitHubRepo,
} from '../../components/vcs';
import config from '../../config';
import useAction from '../../hooks/useAction';

const useStyles = makeStyles()((theme) => ({
  formControl: {
    margin: theme.spacing(1),
    minWidth: 500,
  },
  lessImportantData: {
    color: theme.palette.grey[500],
  },
}));

export default function NewRelease() {
  const location = useLocation();
  const navigate = useNavigate();
  const group = new URLSearchParams(location.search).get('group') || 'firefox';
  const groupTitle = group.charAt(0).toUpperCase() + group.slice(1);
  const { classes } = useStyles();
  const [selectedProduct, setSelectedProduct] = useState('');
  const [selectedRepository, setSelectedRepository] = useState('');
  const [selectedBranch, setSelectedBranch] = useState('');
  const [revision, setRevision] = useState('');
  const [version, setVersion] = useState('');
  const [buildNumber, setBuildNumber] = useState(0);
  const [partialFieldEnabled, setPartialFieldEnabled] = useState(true);
  const [partialVersions, setPartialVersions] = useState([]);
  const [suggestedRevisions, setSuggestedRevisions] = useState(null);
  const [releaseEta, setReleaseEta] = useState(null);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState(null);
  const [branchesLoading, setBranchesLoading] = useState(false);
  const [pushesLoading, setPushesLoading] = useState(false);
  const [revisionInfoLoading, setRevisionInfoLoading] = useState(false);
  const [submitReleaseState, submitReleaseAction] = useAction(submitRelease);
  const [decisionTaskStatus, setDecisionTaskStatus] = useState(null);
  const loading = branchesLoading || pushesLoading || revisionInfoLoading;
  const revisionPretty = (rev) => {
    return `${rev.date.toDateString()} - ${rev.node.substring(0, 8)} - ${
      rev.author
    } - ${maybeShorten(rev.desc)}`;
  };
  const reset = () => {
    setSelectedBranch('');
    setSuggestedRevisions(null);
    setRevision('');
    setVersion('');
    setBuildNumber(0);
    setPartialVersions([]);
    setReleaseEta(null);
    setDecisionTaskStatus(null);
  };

  const handleProduct = (product) => {
    reset();
    setSelectedProduct(product);
  };

  const handleRepository = (repository) => {
    reset();
    setSelectedRepository(repository);
  };

  useEffect(() => {
    if (!selectedRepository?.repo) {
      return;
    }

    const abortController = new AbortController();

    async function fetchBranches() {
      try {
        setBranchesLoading(true);
        const data = await getBranches(
          selectedRepository.repo,
          abortController.signal,
        );
        setSelectedRepository((prev) => ({ ...prev, branches: data }));
      } catch (e) {
        if (abortController.signal.aborted) return;
        setError(
          `Failed to fetch branches for ${selectedRepository.repo}: ${e.toString()}`,
        );
      } finally {
        if (!abortController.signal.aborted) {
          setBranchesLoading(false);
        }
      }
    }

    setError(null);
    fetchBranches();
    return () => abortController.abort();
  }, [selectedRepository?.repo]);

  const handleBranch = (branch) => {
    reset();
    setSelectedBranch(branch);
  };

  useEffect(() => {
    if (!selectedBranch.repo) {
      return;
    }

    const abortController = new AbortController();

    async function fetchPushes() {
      try {
        setPushesLoading(true);
        const pushes = await getPushes(
          selectedBranch.repo,
          isGitHubRepo(selectedBranch.repo) ? selectedBranch.branch : null,
          abortController.signal,
        );
        setSuggestedRevisions(
          pushes.filter((push) => push.desc.indexOf('DONTBUILD') === -1),
        );
      } catch (e) {
        if (abortController.signal.aborted) return;
        setError(
          `Failed to fetch pushes for ${selectedBranch.branch}: ${e.toString()}`,
        );
      } finally {
        if (!abortController.signal.aborted) {
          setPushesLoading(false);
        }
      }
    }

    setSuggestedRevisions(null);
    setError(null);
    fetchPushes();
    return () => abortController.abort();
  }, [selectedBranch.repo, selectedBranch.branch]);

  useEffect(() => {
    if (revision === '' || !selectedBranch?.repo || !selectedProduct) {
      setVersion('');
      setBuildNumber(0);
      return;
    }

    const abortController = new AbortController();
    const { signal } = abortController;

    async function fetchRevisionInfo() {
      try {
        setRevisionInfoLoading(true);

        const ver = await getVersion(
          selectedBranch.repo,
          revision,
          selectedProduct.appName,
          selectedBranch.versionFile,
          signal,
        );
        if (signal.aborted) return;

        const nextBuildNumber = await guessBuildNumber(
          selectedProduct.product,
          ver,
          signal,
        );
        if (signal.aborted) return;

        setVersion(ver);
        setBuildNumber(nextBuildNumber);
      } catch (e) {
        if (signal.aborted) return;
        setError(
          `Failed to fetch revision info for ${revision}: ${e.toString()}`,
        );
      } finally {
        if (!signal.aborted) {
          setRevisionInfoLoading(false);
        }
      }
    }

    setVersion('');
    setBuildNumber(0);
    setDecisionTaskStatus(null);
    setError(null);
    const timeout = setTimeout(fetchRevisionInfo, 500);
    return () => {
      clearTimeout(timeout);
      abortController.abort();
    };
  }, [
    revision,
    selectedBranch?.repo,
    selectedBranch?.branch,
    selectedBranch?.versionFile,
    selectedProduct?.product,
    selectedProduct?.appName,
  ]);

  useEffect(() => {
    if (!version || !selectedProduct?.enablePartials || !partialFieldEnabled) {
      setPartialVersions([]);
      return;
    }

    const abortController = new AbortController();
    const { signal } = abortController;

    async function fetchPartials() {
      try {
        const parts = await guessPartialVersions(
          selectedProduct,
          selectedBranch,
          version,
          signal,
        );
        if (signal.aborted) return;
        setPartialVersions(parts);
      } catch {
        if (signal.aborted) return;
      }
    }

    setError(null);
    fetchPartials();
    return () => abortController.abort();
  }, [
    version,
    selectedProduct?.enablePartials,
    selectedProduct?.product,
    selectedBranch?.branch,
    selectedBranch?.numberOfPartials,
    selectedBranch?.rcBranch,
    selectedBranch?.alternativeBranch,
    partialFieldEnabled,
  ]);

  const handleReleaseEta = (date) => {
    setReleaseEta(date);
  };

  const handlePartials = (partials) => {
    setPartialVersions(
      typeof partials === 'string'
        ? partials.split(',').map((x) => x.trim())
        : partials,
    );
  };

  const readyToSubmit = () => {
    return (
      version !== '' &&
      buildNumber > 0 &&
      (selectedProduct.enablePartials && partialFieldEnabled
        ? partialVersions.filter((x) => x).length > 0
        : true) &&
      !loading &&
      !submitReleaseState.loading &&
      decisionTaskStatus?.state === 'ready'
    );
  };

  const renderProductsSelect = () => {
    return (
      <FormControl variant="standard" className={classes.formControl}>
        <InputLabel>Product</InputLabel>
        <Select
          variant="standard"
          value={selectedProduct}
          onChange={(event) => handleProduct(event.target.value)}
        >
          {config.PRODUCTS[group].map((product) => (
            <MenuItem value={product} key={product.product}>
              {product.prettyName}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    );
  };

  const renderRepositoriesSelect = () => {
    return (
      selectedProduct.repositories && (
        <FormControl variant="standard" className={classes.formControl}>
          <InputLabel>Repository</InputLabel>
          <Select
            variant="standard"
            value={selectedRepository}
            renderValue={() => selectedRepository.prettyName}
            onChange={(event) => handleRepository(event.target.value)}
          >
            {selectedProduct.repositories.map((repository) => (
              <MenuItem value={repository} key={repository.repo}>
                {repository.prettyName}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )
    );
  };

  const getBranchLabel = (branch) => {
    const label = [branch.prettyName];

    if (branch.date) {
      label.push(
        <Box
          component="span"
          m={1}
          className={classes.lessImportantData}
          key={branch.branch}
        >
          updated <TimeAgo date={branch.date} />
        </Box>,
      );
    }

    return label;
  };

  const renderBranchesSelect = () => {
    let branches;

    if (selectedRepository.branches && selectedRepository.branches.length > 0) {
      branches = selectedRepository.branches;
    } else if (selectedProduct.branches?.some((b) => !!b.branch)) {
      branches = selectedProduct.branches;
    }

    return (
      (branchesLoading && <CircularProgress />) ||
      (branches && (
        <FormControl variant="standard" className={classes.formControl}>
          <InputLabel>Branch</InputLabel>
          <Select
            variant="standard"
            value={selectedBranch}
            onChange={(event) => handleBranch(event.target.value)}
          >
            {branches.map((branch) => (
              <MenuItem value={branch} key={branch.branch}>
                {getBranchLabel(branch)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      ))
    );
  };

  const renderRevisionInput = () => {
    return (
      <Grid container alignItems="center">
        <Autocomplete
          className={classes.formControl}
          freeSolo
          forcePopupIcon
          loading={suggestedRevisions === null}
          options={suggestedRevisions || []}
          getOptionLabel={(rev) => rev.node}
          onChange={(_event, value) => value && setRevision(value.node)}
          onInputChange={(_event, value) => setRevision(value)}
          renderOption={(props, option, _state) => (
            <div {...props}> {revisionPretty(option)} </div>
          )}
          renderInput={(params) => (
            <TextField
              {...params}
              inputProps={{ ...params.inputProps, value: revision }}
              label="Revision"
              variant="outlined"
            />
          )}
        />
        {pushesLoading && <CircularProgress size={24} />}
        {revision !== '' && selectedRepository.enableTreeherder !== false && (
          <a
            href={`${config.TREEHERDER_URL}/jobs?repo=${selectedBranch.project}&revision=${revision}`}
          >
            Treeherder
          </a>
        )}
      </Grid>
    );
  };

  const renderReleaseEta = () => {
    return (
      selectedBranch.enableReleaseEta && (
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <DateTimePicker
            referenceDate={new Date()}
            className={classes.formControl}
            viewRenderers={{
              hours: renderTimeViewClock,
              minutes: renderTimeViewClock,
              seconds: renderTimeViewClock,
            }}
            margin="normal"
            inputVariant="outlined"
            ampm={false}
            label="Release ETA (Local time)"
            disablePast
            slotProps={{
              actionBar: {
                actions: ['clear', 'cancel', 'accept'],
              },
            }}
            value={releaseEta}
            onChange={handleReleaseEta}
            minutesStep={15}
            format="yyyy/MM/dd, HH:mm"
          />
        </LocalizationProvider>
      )
    );
  };

  const renderPartials = () => {
    if (selectedProduct) {
      return (
        <Grid container alignItems="center">
          <TextField
            label="Partial updates"
            disabled={!partialFieldEnabled}
            variant="outlined"
            value={partialVersions}
            onChange={(event) => handlePartials(event.target.value)}
            className={classes.formControl}
            helperText="Comma-separated list of versions with build number, e.g. 59.0b8build7."
          />
          {selectedProduct.canTogglePartials && (
            <Switch
              color="secondary"
              checked={partialFieldEnabled}
              onChange={() => {
                setPartialFieldEnabled(!partialFieldEnabled);
                handlePartials('');
              }}
            />
          )}
        </Grid>
      );
    }
  };

  const renderDialogText = () => {
    return (
      <p>A new release of {selectedProduct.prettyName} will be submitted.</p>
    );
  };

  const renderDialog = () => {
    return (
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>Create Release</DialogTitle>
        <DialogContent>{renderDialogText()}</DialogContent>
        <DialogActions>
          {submitReleaseState.loading && <CircularProgress />}
          <Button onClick={() => setOpen(false)} autoFocus variant="contained">
            Close
          </Button>
          <Button
            onClick={async () => {
              const result = await submitReleaseAction(
                selectedProduct,
                selectedBranch,
                revision,
                releaseEta,
                partialFieldEnabled ? partialVersions : [],
                version,
                buildNumber,
              );

              setOpen(false);
              if (result.error !== null) {
                setError(
                  `Could not submit release: ${result.error.toString()}`,
                );
              } else {
                await navigate(`/?group=${group}`, {
                  state: {
                    successMessage: `Successfully created ${selectedProduct.prettyName} ${version}-build${buildNumber} release`,
                  },
                });
              }
            }}
            color="primary"
            disabled={!readyToSubmit()}
            variant="contained"
          >
            Submit
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  const renderReleaseInfo = () => {
    return (
      <React.Fragment>
        <Typography component="h3" variant="h6">
          Version: {version}
        </Typography>
        <Typography component="h3" variant="h6">
          Build #: {buildNumber}
        </Typography>
      </React.Fragment>
    );
  };

  const renderDecisionTaskStatus = () => {
    if (!revision || !selectedProduct || !selectedBranch) {
      return null;
    }

    return (
      <DecisionTaskStatus
        product={selectedProduct.product}
        branch={selectedBranch.branch}
        revision={revision}
        repoUrl={selectedBranch.repo}
        onStatusChange={setDecisionTaskStatus}
      />
    );
  };

  const renderCreateReleaseButton = () => {
    return (
      <Box sx={{ mt: 3 }}>
        <Button
          color="primary"
          variant="contained"
          disabled={!readyToSubmit()}
          onClick={() => setOpen(true)}
        >
          Create Release
        </Button>
      </Box>
    );
  };

  return (
    <Dashboard group={groupTitle} title="New Release">
      <ErrorPanel error={error} />
      {renderProductsSelect()}
      <Collapse
        in={
          selectedProduct.repositories &&
          selectedProduct.repositories.length > 0
        }
      >
        {renderRepositoriesSelect()}
      </Collapse>
      <Collapse
        in={
          branchesLoading ||
          (selectedRepository?.branches &&
            selectedRepository.branches.length > 0) ||
          (selectedProduct.branches && selectedProduct.branches.length > 0)
        }
      >
        {renderBranchesSelect()}
      </Collapse>
      <Collapse in={selectedBranch.repo && selectedBranch.repo.length > 0}>
        <Box>
          {renderRevisionInput()}
          {revision !== '' && (
            <React.Fragment>
              {renderReleaseEta()}
              {selectedProduct.enablePartials && renderPartials()}
              {version !== '' && buildNumber !== 0 ? (
                <Box sx={{ mt: 2 }}>
                  {renderReleaseInfo()}
                  {renderDecisionTaskStatus()}
                  {renderCreateReleaseButton()}
                </Box>
              ) : (
                error === null && (
                  <CircularProgress sx={{ display: 'block', margin: 'auto' }} />
                )
              )}
            </React.Fragment>
          )}
        </Box>
      </Collapse>
      {renderDialog()}
    </Dashboard>
  );
}
