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
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { makeStyles } from 'tss-react/mui';
import { getXPIBuildNumbers, submitXPIRelease } from '../../components/api';
import Dashboard from '../../components/Dashboard';
import DecisionTaskStatus from '../../components/DecisionTaskStatus';
import maybeShorten from '../../components/text';
import {
  getGithubCommits,
  getLatestGithubCommit,
  getXPIVersion,
  getXpis,
} from '../../components/vcs';
import config from '../../config';
import useAction from '../../hooks/useAction';

const useStyles = makeStyles()((theme) => ({
  formControl: {
    margin: theme.spacing(1),
    minWidth: 500,
  },
}));

export default function NewXPIRelease() {
  const { classes } = useStyles();
  const [manifestCommit, fetchManifestCommit] = useAction(
    getLatestGithubCommit,
  );
  const navigate = useNavigate();
  const [xpis, fetchXpis] = useAction(getXpis);
  const [xpiCommits, fetchXpiCommits] = useAction(getGithubCommits);
  const [xpiVersion, fetchXpiVersion] = useAction(getXPIVersion);
  const [buildNumbers, fetchBuildNumbers] = useAction(getXPIBuildNumbers);
  const [submitReleaseState, submitReleaseAction] = useAction(submitXPIRelease);
  const [selectedManifestCommit, setSelectedManifestCommit] = useState('');
  const [selectedXpi, setSelectedXpi] = useState('');
  const [selectedXpiRevision, setSelectedXpiRevision] = useState('');
  const [buildNumber, setBuildNumber] = useState(0);
  const [decisionTaskStatus, setDecisionTaskStatus] = useState(null);
  const [open, setOpen] = useState(false);
  const loading =
    xpis.loading ||
    xpiCommits.loading ||
    xpiVersion.loading ||
    buildNumbers.loading ||
    manifestCommit.loading;
  const revisionPretty = (commit) =>
    `${maybeShorten(commit.revision, 8, '')} - ${maybeShorten(
      commit.message,
      45,
    )}`;
  const init = async () => {
    const { owner, project, branch } = config.XPI_MANIFEST;
    const manifestCommit = await fetchManifestCommit(owner, project, branch);
    const { revision } = manifestCommit.data;

    setSelectedManifestCommit(revision);
    setSelectedXpi('');
    setSelectedXpiRevision('');
    setBuildNumber(0);
    await fetchXpis(owner, project, revision);
  };

  useEffect(() => {
    init();
  }, []);

  const handleXpiSelect = async (xpi) => {
    setSelectedXpiRevision('');
    setSelectedXpi(xpi);
    setBuildNumber(0);
    await fetchXpiCommits(xpi.owner, xpi.repo, xpi.branch);
  };

  const renderXpiSelect = () => {
    if (xpis.loading) {
      return (
        <Box style={{ textAlign: 'center' }}>
          <CircularProgress />
        </Box>
      );
    }

    if (xpis.error) {
      return (
        <Typography variant="h6" component="h3">
          {xpis.error.toString()}
        </Typography>
      );
    }

    if (xpis.data) {
      return (
        <FormControl variant="standard" className={classes.formControl}>
          <InputLabel className={classes.formControl}>Extension</InputLabel>
          <Select
            variant="standard"
            className={classes.formControl}
            value={selectedXpi}
            onChange={(event) => handleXpiSelect(event.target.value)}
          >
            {xpis.data.xpis.map((xpi) => (
              <MenuItem value={xpi} key={xpi.xpi_name}>
                {xpi.xpi_name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      );
    }
  };

  const guessBuildNumber = async (xpiName, version) => {
    const buildNumbers = await fetchBuildNumbers(xpiName, version);
    const nextBuildNumber =
      buildNumbers.data.length !== 0 ? Math.max(...buildNumbers.data) + 1 : 1;

    return nextBuildNumber;
  };

  const handleXpiRevisionChange = async (revision) => {
    // This will trigger handleXpiRevisionInputChange
    setSelectedXpiRevision(revision);
  };

  const handleXpiRevisionInputChange = async (revision) => {
    setSelectedXpiRevision(revision);

    const version = (
      await fetchXpiVersion(
        selectedXpi.owner,
        selectedXpi.repo,
        selectedXpi.revision,
        selectedXpi.install_type,
        selectedXpi.directory,
      )
    ).data;
    const buildNumber = await guessBuildNumber(selectedXpi.xpi_name, version);

    setBuildNumber(buildNumber);
  };

  const renderXpiRevisionSelect = () => {
    if (xpiCommits.loading) {
      return <CircularProgress />;
    }

    if (xpiCommits.error) {
      return (
        <Typography variant="h6" component="h3">
          {xpiCommits.error.toString()}
        </Typography>
      );
    }

    if (xpiCommits.data) {
      return (
        <FormControl variant="standard" className={classes.formControl}>
          <Autocomplete
            className={classes.formControl}
            freeSolo
            forcePopupIcon
            options={xpiCommits.data || []}
            getOptionLabel={(commit) => commit.revision}
            onChange={(_event, value) =>
              value && handleXpiRevisionChange(value.revision)
            }
            onInputChange={(_event, value) =>
              handleXpiRevisionInputChange(value)
            }
            renderOption={(props, option, _state) => (
              <div {...props}> {revisionPretty(option)} </div>
            )}
            renderInput={(params) => (
              <TextField
                {...params}
                inputProps={{
                  ...params.inputProps,
                  value: selectedXpiRevision,
                }}
                label="Revision"
                variant="outlined"
              />
            )}
          />
        </FormControl>
      );
    }
  };

  const renderReleaseInfo = () => {
    const loading = buildNumbers.loading || xpiVersion.loading;

    if (loading) {
      return <CircularProgress />;
    }

    return (
      <React.Fragment>
        <Typography component="h3" variant="h6">
          Version: {xpiVersion.data}
        </Typography>
        <Typography component="h3" variant="h6">
          Build #: {buildNumber}
        </Typography>
        <Typography component="h3" variant="h6">
          Manifest revision: {selectedManifestCommit}
        </Typography>
      </React.Fragment>
    );
  };

  const readyToSubmit = () => {
    return (
      !loading &&
      xpiVersion.data !== null &&
      buildNumber !== 0 &&
      submitReleaseState.data === null &&
      !submitReleaseState.error &&
      decisionTaskStatus?.state === 'ready'
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
      </Grid>
    );
  };

  const renderDialogText = () => {
    if (submitReleaseState.error) {
      return <p>{submitReleaseState.error.toString()}</p>;
    }

    if (submitReleaseState.data === null) {
      return (
        <p>
          A new release of {`${selectedXpi.xpi_name}-${xpiVersion.data}`} will
          be submitted.
        </p>
      );
    }

    return (
      <p>
        {`${selectedXpi.xpi_name}-${xpiVersion.data} build ${buildNumber}`} has
        been submitted.
      </p>
    );
  };

  const renderDialog = () => {
    return (
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>Create XPI Release</DialogTitle>
        <DialogContent>{renderDialogText()}</DialogContent>
        <DialogActions>
          {submitReleaseState.loading && <CircularProgress />}
          <Button
            onClick={() => {
              setOpen(false);

              if (!readyToSubmit()) {
                navigate('/xpi');
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
                selectedManifestCommit,
                selectedXpiRevision,
                selectedXpi.xpi_name,
                xpiVersion.data,
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

  return (
    <Dashboard group="Extensions" title="New Release">
      <Collapse in={selectedManifestCommit !== ''}>
        {renderXpiSelect()}
      </Collapse>
      <Collapse in={selectedXpi !== ''}>{renderXpiRevisionSelect()}</Collapse>
      <Collapse in={selectedXpiRevision !== ''}>
        {renderReleaseInfo()}
        {selectedXpiRevision && (
          <DecisionTaskStatus
            product="xpi"
            branch={config.XPI_MANIFEST.project}
            revision={selectedManifestCommit}
            repoUrl={config.XPI_MANIFEST.repo}
            onStatusChange={setDecisionTaskStatus}
          />
        )}
        {renderCreateReleaseButton()}
        {renderDialog()}
      </Collapse>
    </Dashboard>
  );
}
