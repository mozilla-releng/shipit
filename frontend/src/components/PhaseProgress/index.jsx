import React, { useState, useContext } from 'react';
import Button from '@material-ui/core/Button';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';
import Stepper from '@material-ui/core/Stepper';
import Step from '@material-ui/core/Step';
import StepButton from '@material-ui/core/StepButton';
import StepLabel from '@material-ui/core/StepLabel';
import Spinner from '@mozilla-frontend-infra/components/Spinner';
import libUrls from 'taskcluster-lib-urls';
import Typography from '@material-ui/core/Typography';
import Radio from '@material-ui/core/Radio';
import RadioGroup from '@material-ui/core/RadioGroup';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import FormControl from '@material-ui/core/FormControl';
import FormLabel from '@material-ui/core/FormLabel';
import Link from '@material-ui/core/Link';
import config from '../../config';
import { schedulePhase, phaseSignOff } from '../api';
import useAction from '../../hooks/useAction';
import ReleaseContext from '../../utils/ReleaseContext';

export default function PhaseProgress({ release, readOnly, xpi }) {
  const { fetchReleases } = useContext(ReleaseContext);
  const [open, setOpen] = useState(false);
  const [phase, setPhase] = useState({});
  const [selectedSignoffUID, setSelectedSignoffUID] = useState(null);
  const [schedulePhaseState, schedulePhaseAction] = useAction(schedulePhase);
  const [phaseSignOffState, phaseSignOffAction] = useAction(phaseSignOff);
  const taskGroupUrlPrefix = libUrls.ui(
    config.TASKCLUSTER_ROOT_URL,
    '/tasks/groups'
  );
  const loading = schedulePhaseState.loading || phaseSignOffState.loading;
  const handleClickOpen = phase => {
    setPhase(phase);
    setOpen(true);
  };

  const handleClose = async ({ refresh = false }) => {
    setOpen(false);

    if (refresh) {
      await fetchReleases();
    }
  };

  const scheduleOrSignoff = async () => {
    if (phase.signoffs && phase.signoffs.length > 0) {
      const result = await phaseSignOffAction(
        release.name,
        phase.name,
        selectedSignoffUID,
        xpi ? '/xpi/signoff' : '/signoff'
      );

      if (!result.error) {
        handleClose({ refresh: true });
      }
    } else {
      const result = await schedulePhaseAction(
        release.name,
        phase.name,
        xpi ? '/xpi/releases' : '/releases'
      );

      if (!result.error) {
        handleClose({ refresh: true });
      }
    }
  };

  const phasePrettyName = name => {
    if (name === 'promote_firefox_rc') {
      return 'Promote RC';
    }

    if (name === 'ship_firefox_rc') {
      return 'Ship RC';
    }

    if (name === 'ship_fennec_rc') {
      return 'Ship RC';
    }

    if (name === 'ship_fennec_release_rc') {
      return 'Ship Release to RC';
    }

    if (name === 'ship_fennec_release') {
      return 'Ship Fennec to Release';
    }

    const firstTerm = name.split('_')[0];

    return firstTerm.charAt(0).toUpperCase() + firstTerm.slice(1);
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
      const errorStatuses = ['failed', 'exception'];
      const inProgress = submittedTaskStatuses.includes(phase.tcStatus);
      const taskError = errorStatuses.includes(phase.tcStatus);

      return (
        <Step key={phase.name} completed={!inProgress}>
          <StepLabel
            error={taskError}
            StepIconProps={
              inProgress ? { icon: <Spinner loading size={30} /> } : undefined
            }>
            <Link href={`${taskGroupUrlPrefix}/${phase.actionTaskId}`}>
              {prettyName}
            </Link>
          </StepLabel>
        </Step>
      );
    }

    const canBeScheduled =
      !readOnly &&
      // don't schedule anything if something is still in progress
      !phases.map(p => p.tcStatus).find(st => st === 'running') &&
      (idx === 0 || // The first phase can be scheduled anytime
      allowPhaseSkipping || // Can schedule anything
      phases[idx - 1].tcStatus === 'completed' || // previsous phase is done
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

  const handleSignoffChange = event => {
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
          onChange={handleSignoffChange}>
          {phase.signoffs.map(signoff => (
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
      <Stepper alternativeLabel nonLinear={release.allow_phase_skipping}>
        {release.phases.map((phase, idx) =>
          renderPhase(phase, idx, release.phases, release.allow_phase_skipping)
        )}
      </Stepper>
      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>Schedule Phase</DialogTitle>
        <DialogContent>
          {phase.signoffs && phase.signoffs.length > 0
            ? renderSignoffs()
            : renderSchedulePhase()}
        </DialogContent>
        <DialogActions>
          {loading && <Spinner loading />}
          <Button onClick={handleClose} variant="contained" color="default">
            Close
          </Button>
          <Button
            onClick={() => scheduleOrSignoff(release.name, phase.name)}
            variant="contained"
            color="primary">
            {phase.signoffs && phase.signoffs.length > 0
              ? 'Sign Off'
              : 'Schedule'}
          </Button>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
}
