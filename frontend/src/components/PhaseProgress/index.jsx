import Box from '@material-ui/core/Box';
import Button from '@material-ui/core/Button';
import CircularProgress from '@material-ui/core/CircularProgress';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';
import FormControl from '@material-ui/core/FormControl';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import FormLabel from '@material-ui/core/FormLabel';
import Link from '@material-ui/core/Link';
import Radio from '@material-ui/core/Radio';
import RadioGroup from '@material-ui/core/RadioGroup';
import Step from '@material-ui/core/Step';
import StepButton from '@material-ui/core/StepButton';
import StepLabel from '@material-ui/core/StepLabel';
import Stepper from '@material-ui/core/Stepper';
import { makeStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import InfoOutlinedIcon from '@material-ui/icons/InfoOutlined';
import LinkOutlinedIcon from '@material-ui/icons/LinkOutlined';
import AndroidIcon from 'mdi-react/AndroidIcon';
import React, { useContext, useState } from 'react';
import libUrls from 'taskcluster-lib-urls';
import config from '../../config';
import useAction from '../../hooks/useAction';
import ReleaseContext from '../../utils/ReleaseContext';
import { phaseSignOff, schedulePhase } from '../api';
import MouseOverPopover from '../Shared/MouseOverPopover';
import { phasePrettyName } from '../text';

const useStyles = makeStyles((theme) => ({
  label: {
    lineHeight: '0.5',
  },
  stepper: {
    backgroundColor: theme.palette.background.paper,
    paddingTop: '40px',
  },
  completed: {
    fill: theme.palette.success.dark,
  },
}));

export default function PhaseProgress({ release, readOnly, xpi }) {
  const classes = useStyles();
  const { fetchReleases, productBranches } = useContext(ReleaseContext);
  const [disableScheduleOrSignoff, setDisableScheduleOrSignoff] =
    useState(false);
  const [open, setOpen] = useState(false);
  const [phase, setPhase] = useState({});
  const [selectedSignoffUID, setSelectedSignoffUID] = useState(null);
  const [schedulePhaseState, schedulePhaseAction] = useAction(schedulePhase);
  const [phaseSignOffState, phaseSignOffAction] = useAction(phaseSignOff);
  const taskGroupUrlPrefix = libUrls.ui(
    config.TASKCLUSTER_ROOT_URL,
    '/tasks/groups',
  );
  const loading = schedulePhaseState.loading || phaseSignOffState.loading;
  const handleClickOpen = (phase) => {
    setPhase(phase);
    setOpen(true);
  };

  const handleClose = async ({ refresh = false }) => {
    setOpen(false);

    if (refresh) {
      await fetchReleases(productBranches);
    }
  };

  const scheduleOrSignoff = async () => {
    setDisableScheduleOrSignoff(true);

    if (phase.signoffs && phase.signoffs.length > 0) {
      const result = await phaseSignOffAction(
        release.name,
        phase.name,
        selectedSignoffUID,
        xpi ? '/xpi/signoff' : '/signoff',
      );

      setDisableScheduleOrSignoff(false);

      if (!result.error) {
        handleClose({ refresh: true });
      }
    } else {
      const result = await schedulePhaseAction(
        release.name,
        phase.name,
        xpi ? '/xpi/releases' : '/releases',
      );

      setDisableScheduleOrSignoff(false);

      if (!result.error) {
        handleClose({ refresh: true });
      }
    }
  };

  const renderPhase = (phase, idx, phases, allowPhaseSkipping) => {
    const prettyName = phasePrettyName(phase.name);

    if (phase.skipped) {
      return (
        <Step key={phase.name} disabled active={false}>
          <StepLabel>{prettyName} (skipped)</StepLabel>
        </Step>
      );
    }

    if (phase.submitted) {
      const submittedTaskStatuses = ['unscheduled', 'pending', 'running'];
      const errorStatuses = ['failed', 'exception', 'warning'];
      const inProgress = submittedTaskStatuses.includes(phase.tcStatus);
      const taskError = errorStatuses.includes(phase.tcStatus);

      return (
        <Step key={phase.name} completed={!inProgress}>
          <StepLabel
            classes={{ label: classes.label }}
            error={taskError}
            StepIconProps={
              inProgress
                ? { icon: <CircularProgress loading size={30} /> }
                : { classes: { completed: classes.completed } }
            }
          >
            <Link href={`${taskGroupUrlPrefix}/${phase.actionTaskId}`}>
              {prettyName} task
            </Link>
            {phase.signoffs && phase.signoffs.length > 0 && (
              <MouseOverPopover
                text={
                  <React.Fragment>
                    Approved
                    <InfoOutlinedIcon
                      fontSize="small"
                      viewBox="-5 0 30 30"
                      style={{
                        position: 'relative',
                        top: '.35em',
                      }}
                    />
                  </React.Fragment>
                }
                fontSize=".80rem"
                fontWeight={500}
                position="absolute"
                marginTop=".15rem"
                popoverContent={
                  <React.Fragment>
                    {phase.signoffs.map((signoff) => (
                      <Typography
                        key={signoff.name}
                        variant="caption"
                        display="block"
                      >
                        {`${signoff.completed_by}, ${signoff.name}`}
                      </Typography>
                    ))}
                  </React.Fragment>
                }
              />
            )}
            {!inProgress && phase.xpiUrl && (
              <Box
                fontSize=".80rem"
                fontWeight={500}
                marginTop="1.6rem"
                position="absolute"
              >
                <Link href={phase.xpiUrl}>
                  xpi package
                  <LinkOutlinedIcon
                    fontSize="small"
                    viewBox="-5 0 30 30"
                    style={{
                      position: 'relative',
                      top: '.4em',
                    }}
                  />
                </Link>
              </Box>
            )}
          </StepLabel>
        </Step>
      );
    }

    const canBeScheduled =
      !readOnly &&
      // don't schedule anything if something is still in progress
      !phases.map((p) => p.tcStatus).find((st) => st === 'running') &&
      (idx === 0 || // The first phase can be scheduled anytime
        allowPhaseSkipping || // Can schedule anything
        phases[idx - 1].tcStatus === 'completed' || // previous phase is done
        // Special case for Firefox RC.
        // push_firefox can be scheduled even if ship_firefox_rc (the previous
        // phase) is not ready. We still need to be sure that
        // promote_firefox_rc is ready
        (phase.name === 'push_firefox' &&
          phases[idx - 1].name === 'ship_firefox_rc' &&
          phases[0].tcStatus === 'completed'));

    if (canBeScheduled) {
      return (
        <Step key={phase.name} disabled={false}>
          <StepButton onClick={() => handleClickOpen(phase)} completed={false}>
            {prettyName}
          </StepButton>
        </Step>
      );
    }

    return (
      <Step key={phase.name} disabled>
        <StepLabel>{prettyName} blocked</StepLabel>
      </Step>
    );
  };

  const handleSignoffChange = (event) => {
    setSelectedSignoffUID(event.target.value);
  };

  const renderSignoffs = () => {
    if (phaseSignOffState.error) {
      return <p>{phaseSignOffState.error.toString()}</p>;
    }

    return (
      <FormControl component="fieldset">
        <FormLabel component="legend">Sign Off As</FormLabel>
        <RadioGroup
          name="currentSignoff"
          value={selectedSignoffUID}
          onChange={handleSignoffChange}
        >
          {phase.signoffs.map((signoff) => (
            <FormControlLabel
              key={signoff.uid}
              value={signoff.uid}
              control={<Radio />}
              label={signoff.name}
              disabled={signoff.signed}
            />
          ))}
        </RadioGroup>
      </FormControl>
    );
  };

  const renderSchedulePhase = () => {
    if (schedulePhaseState.error) {
      return <p>{schedulePhaseState.error.toString()}</p>;
    }

    return (
      <Typography variant="subtitle1">
        Schedule {phase.name} of {release.name}?
      </Typography>
    );
  };

  return (
    <React.Fragment>
      <Stepper
        nonLinear={release.allow_phase_skipping}
        className={classes.stepper}
      >
        {release.phases.map((phase, idx) =>
          renderPhase(phase, idx, release.phases, release.allow_phase_skipping),
        )}
      </Stepper>
      <Dialog open={open} onClose={handleClose}>
        <div style={{ position: 'relative' }}>
          <div style={{ width: '50%', position: 'absolute' }}>
            {release.name.toLowerCase().includes('android') && (
              <AndroidIcon
                style={{
                  color: '#20ac5f',
                  height: '3em',
                  width: '3em',
                  marginTop: '2em',
                  marginLeft: '28.75em',
                }}
              />
            )}
          </div>
        </div>
        <DialogTitle>Schedule Phase</DialogTitle>
        <DialogContent>
          {phase.signoffs && phase.signoffs.length > 0
            ? renderSignoffs()
            : renderSchedulePhase()}
        </DialogContent>
        <DialogActions>
          {loading && <CircularProgress loading />}
          <Button onClick={handleClose} variant="contained" color="default">
            Close
          </Button>
          <Button
            disabled={disableScheduleOrSignoff}
            onClick={() => scheduleOrSignoff(release.name, phase.name)}
            variant="contained"
            color="primary"
          >
            {phase.signoffs && phase.signoffs.length > 0
              ? 'Sign Off'
              : 'Schedule'}
          </Button>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
}
