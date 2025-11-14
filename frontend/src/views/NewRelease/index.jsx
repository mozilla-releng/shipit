import RefreshIcon from '@mui/icons-material/Refresh';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Collapse from '@mui/material/Collapse';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControl from '@mui/material/FormControl';
import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { DateTimePicker, LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { renderTimeViewClock } from '@mui/x-date-pickers/timeViewRenderers';
import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router';
import TimeAgo from 'react-timeago';
import { makeStyles } from 'tss-react/mui';
import {
  checkDecisionTaskStatus,
  guessBuildNumber,
  guessPartialVersions,
  submitRelease,
} from '../../components/api';
import Dashboard from '../../components/Dashboard';
import maybeShorten from '../../components/text';
import { getBranches, getPushes, getVersion } from '../../components/vcs';
import config from '../../config';
import useAction from '../../hooks/useAction';
import Link from '../../utils/Link';

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
  const [getBranchesState, getBranchesAction] = useAction(getBranches);
  const [getPushesState, getPushesAction] = useAction(getPushes);
  const [submitReleaseState, submitReleaseAction] = useAction(submitRelease);
  const [guessPartialVersionsState, guessPartialVersionsAction] =
    useAction(guessPartialVersions);
  const [getVersionState, getVersionAction] = useAction(getVersion);
  const [guessBuildNumberState, guessBuildNumberAction] =
    useAction(guessBuildNumber);
  const [checkDecisionTaskState, checkDecisionTaskAction] = useAction(
    checkDecisionTaskStatus,
  );
  const [decisionTaskStatus, setDecisionTaskStatus] = useState(null);
  const loading =
    getBranchesState.loading ||
    getPushesState.loading ||
    getVersionState.loading ||
    guessBuildNumberState.loading ||
    guessPartialVersionsState.loading;
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
    setSuggestedRevisions(null);
    setReleaseEta(null);
    setDecisionTaskStatus(null);
  };

  const handleProduct = (product) => {
    reset();
    setSelectedProduct(product);
  };

  const handleRepository = async (repository) => {
    reset();
    const repo = { ...repository };
    const branches = await getBranchesAction(repo.repo);

    repo.branches = branches.data;
    setSelectedRepository(repo);
  };

  const handleBranch = async (branch) => {
    reset();
    setSelectedBranch(branch);
    const pushes = await getPushesAction(branch.repo, branch.branch);

    setSuggestedRevisions(
      pushes.data.filter((push) => push.desc.indexOf('DONTBUILD') === -1),
    );
  };

  const handleCheckDecisionTask = async (rev) => {
    setDecisionTaskStatus(null);
    const status = await checkDecisionTaskAction(
      selectedProduct.product,
      selectedBranch.branch,
      rev,
      selectedBranch.repo,
    );
    setDecisionTaskStatus(status.data);
  };

  const handleRevisionInputChange = async (rev) => {
    setRevision(rev);

    if (!rev) {
      setVersion('');
      setBuildNumber('');
      setPartialVersions([]);
      setDecisionTaskStatus(null);

      return;
    }

    const ver = (
      await getVersionAction(
        selectedBranch.repo,
        rev,
        selectedProduct.appName,
        selectedBranch.versionFile,
      )
    ).data;
    const nextBuildNumber = (
      await guessBuildNumberAction(selectedProduct.product, ver)
    ).data;

    setVersion(ver);
    setBuildNumber(nextBuildNumber);

    handleCheckDecisionTask(rev);

    if (selectedProduct.enablePartials && partialFieldEnabled) {
      const parts = await guessPartialVersionsAction(
        selectedProduct,
        selectedBranch,
        ver,
      );

      setPartialVersions(parts.data);
    }
  };

  const handleRevisionChange = async (rev) => {
    // This will trigger value change and handleRevisionInputChange
    setRevision(rev);
  };

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
      submitReleaseState.data === null &&
      !submitReleaseState.error &&
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
      (getBranchesState.loading && <CircularProgress />) ||
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
          options={suggestedRevisions || []}
          getOptionLabel={(rev) => rev.node}
          onChange={(_event, value) =>
            value && handleRevisionChange(value.node)
          }
          onInputChange={(_event, value) => handleRevisionInputChange(value)}
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
    if (submitReleaseState.error) {
      return <p>{submitReleaseState.error.toString()}</p>;
    }

    if (submitReleaseState.data === null) {
      return (
        <p>A new release of {selectedProduct.prettyName} will be submitted.</p>
      );
    }

    return <p>{selectedProduct.prettyName} has been submitted.</p>;
  };

  const renderDialog = () => {
    return (
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>Create Release</DialogTitle>
        <DialogContent>{renderDialogText()}</DialogContent>
        <DialogActions>
          {submitReleaseState.loading && <CircularProgress />}
          <Button
            onClick={() => {
              setOpen(false);

              if (!readyToSubmit()) {
                navigate(`/?group=${group}`);
              }
            }}
            autoFocus
            variant="contained"
          >
            Close
          </Button>
          <Button
            onClick={() =>
              submitReleaseAction(
                selectedProduct,
                selectedBranch,
                revision,
                releaseEta,
                partialVersions,
                version,
                buildNumber,
              )
            }
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
    if (!decisionTaskStatus && !checkDecisionTaskState.loading) {
      return null;
    }

    const state = decisionTaskStatus?.state || 'checking...';
    const colorMap = {
      ready: 'success',
      missing: 'error',
    };
    const color = colorMap[state] || 'default';
    const taskUrl = decisionTaskStatus?.task_id
      ? `${config.TASKCLUSTER_ROOT_URL}/tasks/${decisionTaskStatus.task_id}`
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
            onClick={() => handleCheckDecisionTask(revision)}
            disabled={checkDecisionTaskState.loading}
            title="Refresh status"
          >
            {checkDecisionTaskState.loading ? (
              <CircularProgress size={16} />
            ) : (
              <RefreshIcon fontSize="small" />
            )}
          </IconButton>
        </Box>
      </Typography>
    );
  };

  const renderCreateReleaseButton = () => {
    return (
      <Grid container alignItems="center">
        <Button
          color="primary"
          variant="contained"
          disabled={!readyToSubmit()}
          onClick={() => setOpen(true)}
        >
          Create Release
        </Button>
        {loading && <CircularProgress />}
      </Grid>
    );
  };

  return (
    <Dashboard group={groupTitle} title="New Release">
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
          getBranchesState.loading ||
          (selectedRepository?.branches &&
            selectedRepository.branches.length > 0) ||
          (selectedProduct.branches && selectedProduct.branches.length > 0)
        }
      >
        {renderBranchesSelect()}
      </Collapse>
      <Collapse in={selectedBranch.repo && selectedBranch.repo.length > 0}>
        {renderRevisionInput()}
        {renderReleaseEta()}
        {selectedProduct.enablePartials && renderPartials()}
        <Collapse in={version !== '' && buildNumber !== 0}>
          {renderReleaseInfo()}
          {renderDecisionTaskStatus()}
        </Collapse>
        {renderCreateReleaseButton()}
      </Collapse>
      {renderDialog()}
    </Dashboard>
  );
}
