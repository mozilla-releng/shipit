import React from 'react';
import { ProgressBar, Button, Modal, Collapse, FormGroup, Radio, ControlLabel, Tabs, Tab } from 'react-bootstrap';
import { object } from 'prop-types';
import ReactInterval from 'react-interval';
import { Queue } from 'taskcluster-client-web';
import libUrls from 'taskcluster-lib-urls';
import config, { SHIPIT_API_URL, TASKCLUSTER_ROOT_URL } from '../../config';
import { getApiHeaders, getShippedReleases } from '../../components/api';

const statusStyles = {
  // TC statuses
  unscheduled: 'info',
  pending: 'info',
  running: 'info',
  completed: 'success',
  failed: 'danger',
  exception: 'warning',
  // Additional statuses
  ready: 'info',
  blocked: 'info',
  skipped: 'info',
};

const submittedTaskStatuses = ['unscheduled', 'pending', 'running'];

const taskStatus = async (taskId) => {
  const status = await (new Queue({ rootUrl: TASKCLUSTER_ROOT_URL })).status(taskId);
  return status;
};

export default class ListReleases extends React.Component {
  constructor(...args) {
    super(...args);
    this.state = {
      loaded: false,
      message: '',
      releases: [],
      shippedReleases: [],
      shippedReleasesMessage: '',
    };
  }

  async componentDidMount() {
    await this.getReleases();
  }

  getReleases = async () => {
    try {
      const req = await fetch(`${SHIPIT_API_URL}/releases`);
      const releases = await req.json();
      let message = '';
      if (releases.length === 0) {
        message = <h3>No pending releases!</h3>;
      }
      this.setState({
        releases,
        message,
        loaded: true,
      });
    } catch (e) {
      const message = <h3>Failed to fetch releases! (VPN required)</h3>;
      this.setState({
        loaded: true,
        message,
        releases: [],
      });
      throw e;
    }
  };

  getRecentReleases = async (product, branch) => {
    try {
      const shippedReleases = await getShippedReleases(product, branch);
      let shippedReleasesMessage = '';
      if (shippedReleases.length === 0) {
        shippedReleasesMessage = <h3>No recent releases!</h3>;
      }
      this.setState(state => ({
        shippedReleasesMessage,
        shippedReleases: state.shippedReleases.concat(shippedReleases.slice(0, 4)),
      }));
    } catch (e) {
      const shippedReleasesMessage = <h3>Failed to fetch releases! (VPN required)</h3>;
      this.setState({
        shippedReleasesMessage,
        shippedReleases: [],
      });
      throw e;
    }
  };

  handleTabSelect = (key) => {
    if (key === 'recentReleases') {
      // this is an expensive call, let's not repeat it
      if (this.state.shippedReleases.length > 0) {
        return;
      }
      config.PRODUCTS.forEach((product) => {
        product.branches.forEach((branch) => {
          this.getRecentReleases(product.product, branch.branch);
        });
      });
    }
  };

  renderRecentReleases = () => {
    const { shippedReleases, shippedReleasesMessage } = this.state;
    // Sort the releases by date, reversed
    const sortedShippedReleases = shippedReleases.sort((a, b) => a.created < b.created);
    return (
      <div className="container">
        <h3>Recent releases</h3>
        <div>
          {shippedReleasesMessage}
          {sortedShippedReleases.length > 0 && sortedShippedReleases.map(release => (
            <Release
              release={release}
              key={release.name}
              showCancel={false}
            />))}
        </div>
      </div>
    );
  };

  renderReleases = () => {
    const { releases, loaded, message } = this.state;
    return (
      <div className="container">
        <h3>Releases in progress</h3>
        <div>
          {loaded || <b>loading...</b>}
          {message}
          {releases.length > 0 && releases.map(release => (
            <Release
              release={release}
              key={release.name}
              showCancel
            />))}
          <ReactInterval
            enabled
            timeout={2 * 60 * 1000}
            callback={() => this.getReleases()}
          />
        </div>
      </div>
    );
  };

  render() {
    return (
      <Tabs defaultActiveKey="releases" id="releases" onSelect={this.handleTabSelect}>
        <Tab eventKey="releases" title="In progress">
          {this.renderReleases()}
        </Tab>
        <Tab eventKey="recentReleases" title="Recent">
          {this.renderRecentReleases()}
        </Tab>
      </Tabs>
    );
  }
}

class Release extends React.Component {
  static contextTypes = {
    authController: object.isRequired,
  };
  constructor(props) {
    super(props);
    this.state = {
      showModal: false,
      submitted: props.submitted,
      errorMsg: null,
    };
  }

  open = () => {
    this.setState({ showModal: true });
  };

  close = () => {
    this.setState({
      showModal: false,
      errorMsg: null,
    });
  };

  abortRelease = async (release) => {
    const url = `${SHIPIT_API_URL}/releases/${release.name}`;
    if (!this.context.authController.userSession) {
      this.setState({ errorMsg: 'Login required!' });
      return;
    }
    const { accessToken } = this.context.authController.getUserSession();
    const headers = getApiHeaders(accessToken);
    try {
      const response = await fetch(url, { method: 'DELETE', headers });
      if (!response.ok) {
        this.setState({ errorMsg: 'Auth failure!' });
        return;
      }
      this.setState({ submitted: true });
      window.location.reload();
    } catch (e) {
      this.setState({ errorMsg: 'Server issues!' });
      throw e;
    }
  };

  renderBody = () => {
    const { submitted, errorMsg } = this.state;
    if (errorMsg) {
      return (
        <div>
          <p>{errorMsg}</p>
        </div>
      );
    }
    if (!submitted) {
      return (
        <div>
          <h4>Are you sure?</h4>
          <p>
            The release will be cancelled!
          </p>
        </div>
      );
    }
    return (
      <div>Done.</div>
    );
  };

  render() {
    const { release, showCancel } = this.props;
    return (
      <div className="row">
        <div className="col">
          <h3>
            <a href={`${config.TREEHERDER_URL}/#/jobs?repo=${release.project}&revision=${release.revision}`}>
              {release.product} <small>{release.version} build{release.build_number}</small>
            </a>
            {showCancel &&
              <Button
                onClick={this.open}
                bsStyle="danger"
                bsSize="xsmall"
                style={{ margin: '10px' }}
                disabled={!this.context.authController.userSession}
              >
                Cancel release
              </Button>
            }
          </h3>
        </div>
        <Modal show={this.state.showModal} onHide={this.close}>
          <Modal.Header closeButton>
            <Modal.Title>Cancel release</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {this.renderBody()}
          </Modal.Body>
          <Modal.Footer>
            <Button
              onClick={() => this.abortRelease(release)}
              bsStyle="danger"
              disabled={!this.context.authController.userSession}
            >
              Stop release
            </Button>
            <Button onClick={this.close} bsStyle="primary">Close</Button>
          </Modal.Footer>
        </Modal>
        <div className="col">
          <TaskProgress
            phases={release.phases}
            releaseName={release.name}
            allowPhaseSkipping={release.allow_phase_skipping}
          />
        </div>
      </div>
    );
  }
}

const phaseStatus = async (phase, idx, phases, allowPhaseSkipping) => {
  if (phase.skipped) {
    return 'skipped';
  }
  // Use TC status if task is submitted
  if (phase.submitted) {
    const status = await taskStatus(phase.actionTaskId);
    return status.status.state;
  }
  // First phase, ready any time
  if (idx === 0) {
    return 'ready';
  }
  // Phase is ready only when the previous one is submitted and the task is completed
  const previousPhase = phases[idx - 1];
  if (previousPhase.submitted) {
    // TODO: cache previous phase status
    const status = await taskStatus(previousPhase.actionTaskId);
    if (status.status.state === 'completed') {
      return 'ready';
    }
  }
  // Special case for Firefox RC.
  // push_firefox can be scheduled even if ship_firefox_rc (the previous phase)
  // is not ready. We still need to be sure that promote_firefox_rc is ready
  if (phase.name === 'push_firefox' && previousPhase.name === 'ship_firefox_rc') {
    const promoteFirefoxRCPhase = phases[0];
    if (promoteFirefoxRCPhase.submitted) {
      const status = await taskStatus(promoteFirefoxRCPhase.actionTaskId);
      if (status.status.state === 'completed') {
        return 'ready';
      }
    }
  }
  return allowPhaseSkipping ? 'ready' : 'blocked';
};

const phaseSignOffs = async (releaseName, phaseName) => {
  const url = `${SHIPIT_API_URL}/signoff/${releaseName}/${phaseName}`;
  const response = await fetch(url);
  if (!response.ok) {
    return [];
  }
  const signoffs = await response.json();
  return signoffs;
};

class TaskProgress extends React.Component {
  constructor(...args) {
    super(...args);
    this.state = {
      phasesWithStatus: [],
      tasksInProgress: false,
    };
  }

  async componentDidMount() {
    await this.syncPhases();
  }

  syncPhases = async () => {
    const { releaseName, phases, allowPhaseSkipping } = this.props;
    const phasesWithStatus = await Promise.all(phases.map(async (phase, idx, arr) => {
      const status = await phaseStatus(phase, idx, arr, allowPhaseSkipping);
      const signoffs = await phaseSignOffs(releaseName, phase.name);
      return { ...phase, status, signoffs };
    }));
    const tasksInProgress = phasesWithStatus.some(phase =>
      submittedTaskStatuses.includes(phase.status));
    this.setState({ phasesWithStatus, tasksInProgress });
  };

  render() {
    const { phasesWithStatus, tasksInProgress } = this.state;
    const { releaseName } = this.props;
    const width = 100 / phasesWithStatus.length;
    const taskGroupUrlPrefix = libUrls.ui(TASKCLUSTER_ROOT_URL, '/tasks/groups');

    return (
      <ProgressBar style={{ height: '40px', padding: '3px' }}>
        {phasesWithStatus.map(({
          name, submitted, actionTaskId, status, signoffs,
        }) => (
          <ProgressBar
            key={name}
            bsStyle={statusStyles[status] || 'info'}
            now={width}
            active={submitted && submittedTaskStatuses.includes(status)}
            label={<TaskLabel
              key={actionTaskId}
              name={name}
              submitted={submitted}
              status={status}
              tasksInProgress={tasksInProgress}
              signoffs={signoffs}
              releaseName={releaseName}
              taskGroupUrl={`${taskGroupUrlPrefix}/${actionTaskId}`}
            />}
          />
        ))}
      </ProgressBar>
    );
  }
}

class TaskLabel extends React.PureComponent {
  static contextTypes = {
    authController: object.isRequired,
  };

  constructor(props) {
    super(props);
    this.state = {
      showModal: false,
      submitted: props.submitted,
      errorMsg: null,
      selectedSignoff: null,
      inProgress: false,
    };
  }

  open = () => {
    this.setState({ showModal: true });
  };

  close = () => {
    this.setState({
      showModal: false,
      errorMsg: null,
      selectedSignoff: null,
    });
  };

  signOff = async () => {
    this.setState({ inProgress: true });
    const { accessToken } = this.context.authController.getUserSession();
    const { releaseName, name } = this.props;
    const { selectedSignoff } = this.state;
    const url = `${SHIPIT_API_URL}/signoff/${releaseName}/${name}`;
    const headers = getApiHeaders(accessToken);
    const body = JSON.stringify(selectedSignoff);
    try {
      const response = await fetch(url, { method: 'PUT', headers, body });
      if (!response.ok) {
        const err = await response.json();
        this.setState({ errorMsg: `Error: ${err.detail}` });
        return;
      }
      this.setState({ submitted: true });
    } catch (e) {
      this.setState({ errorMsg: 'Server issues!' });
      throw e;
    } finally {
      this.setState({ inProgress: false });
    }
  };

  schedulePhase = async () => {
    this.setState({ inProgress: true });
    const { accessToken } = this.context.authController.getUserSession();
    const { releaseName, name } = this.props;
    const headers = getApiHeaders(accessToken);
    const url = `${SHIPIT_API_URL}/releases/${releaseName}/${name}`;
    try {
      const response = await fetch(url, { method: 'PUT', headers });
      if (!response.ok) {
        const err = await response.json();
        this.setState({ errorMsg: `Error: ${err.detail}` });
        return;
      }
      this.setState({ submitted: true });
    } catch (e) {
      this.setState({ errorMsg: 'Server issues!' });
      throw e;
    } finally {
      this.setState({ inProgress: false });
    }
  };

  doEet = async () => {
    if (!this.context.authController.userSession) {
      this.setState({ errorMsg: 'Login required!' });
      return;
    }
    const { selectedSignoff } = this.state;
    if (selectedSignoff) {
      await this.signOff();
    } else {
      await this.schedulePhase();
    }
  };

  renderSignoffs = signoffs => (
    <div>
      <ControlLabel>Sign off as</ControlLabel>
      <FormGroup>
        {signoffs.map(s => (
          <Radio
            key={s.uid}
            name="signoff"
            disabled={s.signed}
            onClick={() => this.setState({ selectedSignoff: s.uid })}
          >
            {s.name} - {s.description}
            {s.signed && <small> (completed by: {s.completed_by})</small>}
          </Radio>
        ))}
      </FormGroup>
    </div>
  );

  renderBody = () => {
    const { inProgress, submitted, errorMsg } = this.state;
    const { signoffs } = this.props.signoffs;
    const signoffRequired = signoffs && signoffs.length > 0;

    if (errorMsg) {
      return (
        <div>
          <h4>{errorMsg}</h4>
        </div>
      );
    }

    if (inProgress) {
      return (
        <div>
          <h4>Working...</h4>
        </div>
      );
    }

    if (!submitted) {
      if (signoffRequired) {
        return (
          <div>
            <h4>Phase will be signed off</h4>
            {this.renderSignoffs(signoffs)}
          </div>
        );
      }

      return (
        <div>
          <h4>Phase will be scheduled</h4>
        </div>
      );
    }

    if (signoffRequired) {
      return <h4>Phase signed off</h4>;
    }

    return <h4>Phase submitted</h4>;
  };

  render() {
    const {
      status, name, taskGroupUrl, tasksInProgress,
    } = this.props;
    if (status === 'blocked' || status === 'skipped') {
      return (
        <div>
          <Button disabled={tasksInProgress} bsStyle={statusStyles[status]}>{name}</Button>
          {status === 'skipped' && <small>skipped</small>}
        </div>
      );
    }
    if (status === 'ready') {
      return (
        <div>
          <Button bsStyle="primary" disabled={tasksInProgress} onClick={this.open}>{name}</Button>
          <Modal show={this.state.showModal} onHide={this.close}>
            <Modal.Header closeButton>
              <Modal.Title>Schedule Phase</Modal.Title>
            </Modal.Header>
            <Modal.Body>
              {this.renderBody()}
            </Modal.Body>
            <Modal.Footer>
              <Collapse in={!this.state.submitted}>
                <div>
                  <Button
                    onClick={this.doEet}
                    bsStyle="danger"
                    disabled={!this.context.authController.userSession || this.state.inProgress}
                  >
                    Schedule Phase
                  </Button>
                  <Button onClick={this.close} bsStyle="primary">Close</Button>
                </div>
              </Collapse>
            </Modal.Footer>
          </Modal>
        </div>
      );
    }
    return (
      <div>
        <Button bsStyle={statusStyles[status]} href={taskGroupUrl}>{name}</Button>
      </div>
    );
  }
}
