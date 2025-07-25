import { Auth0Context } from '@auth0/auth0-react';
import 'date-fns';
import React, { useState, useContext } from 'react';
import { useLocation, useHistory } from 'react-router-dom';
import TimeAgo from 'react-timeago';
import Box from '@material-ui/core/Box';
import Button from '@material-ui/core/Button';
import Collapse from '@material-ui/core/Collapse';
import TextField from '@material-ui/core/TextField';
import Autocomplete from '@material-ui/lab/Autocomplete';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';
import InputLabel from '@material-ui/core/InputLabel';
import MenuItem from '@material-ui/core/MenuItem';
import FormControl from '@material-ui/core/FormControl';
import Select from '@material-ui/core/Select';
import Grid from '@material-ui/core/Grid';
import { makeStyles } from '@material-ui/core/styles';
import DateFnsUtils from '@date-io/date-fns';
import { MuiPickersUtilsProvider, DateTimePicker } from '@material-ui/pickers';
import Spinner from '@mozilla-frontend-infra/components/Spinner';
import Typography from '@material-ui/core/Typography';
import Switch from '@material-ui/core/Switch';
import Dashboard from '../../components/Dashboard';
import config from '../../config';
import maybeShorten from '../../components/text';
import { getBranches, getPushes, getVersion } from '../../components/vcs';
import {
  guessBuildNumber,
  guessPartialVersions,
  submitRelease,
} from '../../components/api';
import useAction from '../../hooks/useAction';

const useStyles = makeStyles(theme => ({
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
  const history = useHistory();
  const group = new URLSearchParams(location.search).get('group') || 'firefox';
  const groupTitle = group.charAt(0).toUpperCase() + group.slice(1);
  const classes = useStyles();
  const authContext = useContext(Auth0Context);
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
  const [guessPartialVersionsState, guessPartialVersionsAction] = useAction(
    guessPartialVersions
  );
  const [getVersionState, getVersionAction] = useAction(getVersion);
  const [guessBuildNumberState, guessBuildNumberAction] = useAction(
    guessBuildNumber
  );
  const loading =
    getBranchesState.loading ||
    getPushesState.loading ||
    getVersionState.loading ||
    guessBuildNumberState.loading ||
    guessPartialVersionsState.loading;
  const revisionPretty = rev =>
    `${rev.date.toDateString()} - ${rev.node.substring(0, 8)} - ${
      rev.author
    } - ${maybeShorten(rev.desc)}`;
  const reset = () => {
    setSelectedBranch('');
    setSuggestedRevisions(null);
    setRevision('');
    setVersion('');
    setBuildNumber(0);
    setPartialVersions([]);
    setSuggestedRevisions(null);
    setReleaseEta(null);
  };

  const handleProduct = product => {
    reset();
    setSelectedProduct(product);
  };

  const handleRepository = async repository => {
    reset();
    const repo = { ...repository };
    const branches = await getBranchesAction(repo.repo);

    repo.branches = branches.data;
    setSelectedRepository(repo);
  };

  const handleBranch = async branch => {
    reset();
    setSelectedBranch(branch);
    const pushes = await getPushesAction(branch.repo, branch.branch);

    setSuggestedRevisions(
      pushes.data.filter(push => push.desc.indexOf('DONTBUILD') === -1)
    );
  };

  const handleRevisionInputChange = async rev => {
    setRevision(rev);

    if (!rev) {
      setVersion('');
      setBuildNumber('');
      setPartialVersions([]);

      return;
    }

    const ver = (
      await getVersionAction(
        selectedBranch.repo,
        rev,
        selectedProduct.appName,
        selectedBranch.versionFile
      )
    ).data;
    const nextBuildNumber = (
      await guessBuildNumberAction(selectedProduct.product, ver)
    ).data;

    setVersion(ver);
    setBuildNumber(nextBuildNumber);

    if (selectedProduct.enablePartials && partialFieldEnabled) {
      const parts = await guessPartialVersionsAction(
        selectedProduct,
        selectedBranch,
        ver
      );

      setPartialVersions(parts.data);
    }
  };

  const handleRevisionChange = async rev => {
    // This will trigger value change and handleRevisionInputChange
    setRevision(rev);
  };

  const handleReleaseEta = date => {
    setReleaseEta(date);
  };

  const handlePartials = partials => {
    setPartialVersions(
      typeof partials === 'string'
        ? partials.split(',').map(x => x.trim())
        : partials
    );
  };

  const readyToSubmit = () => {
    return (
      version !== '' &&
      buildNumber > 0 &&
      (selectedProduct.enablePartials && partialFieldEnabled
        ? partialVersions.filter(x => x).length > 0
        : true) &&
      !loading &&
      submitReleaseState.data === null &&
      !submitReleaseState.error
    );
  };

  const renderProductsSelect = () => {
    return (
      <FormControl className={classes.formControl}>
        <InputLabel>Product</InputLabel>
        <Select
          value={selectedProduct}
          onChange={event => handleProduct(event.target.value)}>
          {config.PRODUCTS[group].map(product => (
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
        <FormControl className={classes.formControl}>
          <InputLabel>Repository</InputLabel>
          <Select
            value={selectedRepository}
            renderValue={() => selectedRepository.prettyName}
            onChange={event => handleRepository(event.target.value)}>
            {selectedProduct.repositories.map(repository => (
              <MenuItem value={repository} key={repository.repo}>
                {repository.prettyName}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )
    );
  };

  const getBranchLabel = branch => {
    const label = [branch.prettyName];

    if (branch.date) {
      label.push(
        <Box
          component="span"
          m={1}
          className={classes.lessImportantData}
          key={branch.branch}>
          updated <TimeAgo date={branch.date} />
        </Box>
      );
    }

    return label;
  };

  const renderBranchesSelect = () => {
    let branches;

    if (selectedRepository.branches && selectedRepository.branches.length > 0) {
      branches = selectedRepository.branches;
    } else if (
      selectedProduct.branches &&
      selectedProduct.branches.some(b => !!b.branch)
    ) {
      branches = selectedProduct.branches;
    }

    return (
      (getBranchesState.loading && <Spinner loading />) ||
      (branches && (
        <FormControl className={classes.formControl}>
          <InputLabel>Branch</InputLabel>
          <Select
            value={selectedBranch}
            onChange={event => handleBranch(event.target.value)}>
            {branches.map(branch => (
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
          getOptionLabel={rev => rev.node}
          onChange={(_event, value) =>
            value && handleRevisionChange(value.node)
          }
          onInputChange={(_event, value) => handleRevisionInputChange(value)}
          renderOption={option => revisionPretty(option)}
          renderInput={params => (
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
            href={`${config.TREEHERDER_URL}/jobs?repo=${selectedBranch.project}&revision=${revision}`}>
            Treeherder
          </a>
        )}
      </Grid>
    );
  };

  const renderReleaseEta = () => {
    return (
      selectedBranch.enableReleaseEta && (
        <MuiPickersUtilsProvider utils={DateFnsUtils}>
          <DateTimePicker
            className={classes.formControl}
            margin="normal"
            inputVariant="outlined"
            ampm={false}
            label="Release ETA (Local time)"
            disablePast
            clearable
            value={releaseEta}
            onChange={handleReleaseEta}
            minutesStep={15}
            format="yyyy/MM/dd, HH:mm (O)"
          />
        </MuiPickersUtilsProvider>
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
            onChange={event => handlePartials(event.target.value)}
            className={classes.formControl}
            helperText="Comma-separated list of versions with build number, e.g. 59.0b8build7."
          />
          {selectedProduct.canTogglePartials && (
            <Switch
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
          {submitReleaseState.loading && <Spinner loading />}
          <Button
            onClick={() => {
              setOpen(false);

              if (!readyToSubmit()) {
                history.push(`/?group=${group}`);
              }
            }}
            color="default"
            autoFocus
            variant="contained">
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
                buildNumber
              )
            }
            color="primary"
            disabled={!readyToSubmit()}
            variant="contained">
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

  const renderCreateReleaseButton = () => {
    return (
      <Grid container alignItems="center">
        <Button
          color="primary"
          variant="contained"
          disabled={!readyToSubmit()}
          onClick={() => setOpen(true)}>
          Create Release
        </Button>
        {loading && <Spinner loading />}
      </Grid>
    );
  };

  if (!authContext.user) {
    return (
      <Dashboard group={groupTitle} title="New Release">
        <Typography variant="h6" component="h2">
          Auth required
        </Typography>
      </Dashboard>
    );
  }

  return (
    <Dashboard group={groupTitle} title="New Release">
      {renderProductsSelect()}
      <Collapse
        in={
          selectedProduct.repositories &&
          selectedProduct.repositories.length > 0
        }>
        {renderRepositoriesSelect()}
      </Collapse>
      <Collapse
        in={
          getBranchesState.loading ||
          (selectedRepository &&
            selectedRepository.branches &&
            selectedRepository.branches.length > 0) ||
          (selectedProduct.branches && selectedProduct.branches.length > 0)
        }>
        {renderBranchesSelect()}
      </Collapse>
      <Collapse in={selectedBranch.repo && selectedBranch.repo.length > 0}>
        {renderRevisionInput()}
        {renderReleaseEta()}
        {selectedProduct.enablePartials && renderPartials()}
        <Collapse in={version !== '' && buildNumber !== 0}>
          {renderReleaseInfo()}
        </Collapse>
        {renderCreateReleaseButton()}
      </Collapse>
      {renderDialog()}
    </Dashboard>
  );
}
