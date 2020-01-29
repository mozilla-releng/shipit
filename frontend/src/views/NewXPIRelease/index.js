import React from 'react';
import {
  ButtonToolbar, Button, FormGroup, FormControl, ControlLabel, InputGroup, DropdownButton,
  MenuItem, Collapse, Modal,
} from 'react-bootstrap';
import { object } from 'prop-types';
import { NavLink } from 'react-router-dom';

import config, { SHIPIT_API_URL } from '../../config';
import { getApiHeaders, getXPIBuildNumbers } from '../../components/api';
import { getGithubCommits } from '../../components/vcs';
import maybeShorten from '../../components/text';

export default class NewXPIelease extends React.Component {
  static contextTypes = {
    authController: object.isRequired,
  };

  constructor(...args) {
    super(...args);
    this.state = Object.assign(this.defaultState());
  }

  getManifestCommits = async (owner, repo, branch) => {
    try {
      const { accessToken } = this.context.authController.getUserSession();
      return await getGithubCommits(owner, repo, branch, accessToken);
    } catch (e) {
      this.setState({ errorMsg: e.message });
      return null;
    }
  };

  getXPIRevisions = async (owner, repo, branch) => {
    const revisions = await this.getManifestCommits(owner, repo, branch);
    return revisions;
  };

  getXPIVersion = async (owner, repo, revision) => {
    const url = `${SHIPIT_API_URL}/github/package_json/${owner}/${repo}/${revision}`;
    try {
      const packageJson = await this.queryApi(url);
      return packageJson.version;
    } catch (e) {
      this.setState({ errorMsg: e.message });
      return null;
    }
  };

  getXPIs = async (owner, repo, revision) => {
    const url = `${SHIPIT_API_URL}/github/xpis/${owner}/${repo}/${revision}`;
    try {
      const xpis = await this.queryApi(url);
      return xpis.xpis;
    } catch (e) {
      this.setState({ errorMsg: e.message });
      return null;
    }
  };

  queryApi = async (url) => {
    const { accessToken } = this.context.authController.getUserSession();
    const headers = getApiHeaders(accessToken);
    const response = await fetch(url, { headers });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(`API returned HTTP ${error.title}`);
    }
    const obj = await response.json();
    return obj;
  };

  refreshManifest = async (product) => {
    // keep previously assigned state
    this.setState({ ...this.defaultState(), product });
    const commits = await this.getManifestCommits(product.owner, product.repo, product.branch);
    this.setState({ commits });
  };

  handleXPIPick = async (manifestRevision, xpiName, xpiOwner, xpiRepo, branch) => {
    const xpiRevisions = await this.getXPIRevisions(xpiOwner, xpiRepo, branch);
    // keep previously assigned state
    const {
      product, commits, revision, xpis,
    } = this.state;
    this.setState({
      ...this.defaultState(),
      product,
      commits,
      revision,
      xpis,
      xpiRevisions,
      xpiName,
      xpiOwner,
      xpiRepo,
    });
  };

  handleXPIRevision = async (revision) => {
    this.setState({ xpiRevision: revision.revision });
    this.guessBuildId();
    const xpiVersion = await this.getXPIVersion(
      this.state.xpiOwner,
      this.state.xpiRepo,
      revision.revision,
    );
    this.setState({ xpiVersion });
  };

  defaultState = () => ({
    product: {},
    commits: [],
    revision: '',
    version: '',
    buildNumber: 0,
    showModal: false,
    errorMsg: null,
    submitted: false,
    inProgress: false,
    xpis: [],
    xpiRevisions: [],
    xpiName: '',
    xpiRevision: '',
    xpiOwner: '',
    xpiRepo: '',
    xpiVersion: '',
  });

  handlePickCommit = async (revision) => {
    const { product, commits } = this.state;
    this.setState({
      ...this.defaultState(), product, commits, revision,
    });
    const { owner, repo } = this.state.product;
    const xpis = await this.getXPIs(owner, repo, revision);
    this.setState({ xpis });
  };

  guessBuildId = async () => {
    const buildNumbers = await getXPIBuildNumbers(
      this.state.xpiName,
      this.state.xpiRevision,
    );
    const nextBuildNumber = buildNumbers.length !== 0 ? Math.max(...buildNumbers) + 1 : 1;
    this.setState({
      buildNumber: nextBuildNumber,
    });
  };

  close = () => {
    this.setState(Object.assign(this.defaultState()));
  };

  open = () => {
    this.setState({ showModal: true });
  };

  readyToSubmit = () => this.state.xpiVersion !== '' && this.state.buildNumber > 0;

  handleRevisionChange = async (event) => {
    const { product, commits } = this.state;
    this.setState({
      ...this.defaultState(), product, commits, revision: event.target.value,
    });
    const { owner, repo } = this.state.product;
    const xpis = await this.getXPIs(owner, repo, event.target.value);
    this.setState({ xpis });
  };

  submitRelease = async () => {
    this.setState({ inProgress: true });
    const releaseObj = {
      revision: this.state.revision,
      xpi_revision: this.state.xpiRevision,
      xpi_name: this.state.xpiName,
      xpi_version: this.state.xpiVersion,
      build_number: parseInt(this.state.buildNumber, 10),
    };
    await this.doEet(releaseObj);
    this.setState({ inProgress: false });
  };

  doEet = async (releaseObj) => {
    if (!this.context.authController.userSession) {
      this.setState({ errorMsg: 'Login required!' });
      return;
    }
    const url = `${SHIPIT_API_URL}/xpi/releases`;
    const { accessToken } = this.context.authController.getUserSession();
    const headers = getApiHeaders(accessToken);
    try {
      const body = JSON.stringify(releaseObj);
      const response = await fetch(url, { method: 'POST', headers, body });
      if (!response.ok) {
        this.setState({ errorMsg: 'Auth failure!' });
        return;
      }
      this.setState({ submitted: true });
    } catch (e) {
      this.setState({ errorMsg: 'Server issues!' });
      throw e;
    }
  };

  renderBody = () => {
    const { inProgress, submitted, errorMsg } = this.state;
    if (errorMsg) {
      return (
        <div>
          <p>{errorMsg}</p>
        </div>
      );
    }
    if (inProgress) {
      return (
        <div>
          <h4>Working....</h4>
        </div>
      );
    }
    if (!submitted) {
      const buildName =
        `${this.state.xpiName}-${this.state.xpiVersion}-build${this.state.buildNumber}`;
      return (
        <div>
          <h4>The following release will be submitted:</h4>
          <div>{buildName}</div>
        </div>
      );
    }
    return (
      <div>
        Done. Start the release from <NavLink to="/xpi">the list of releases</NavLink>
      </div>
    );
  };

  render() {
    if (!this.context.authController.userSession) {
      return (
        <div className="container">
          <h1>Auth required</h1>
        </div>
      );
    }
    return (
      <div className="container">
        {this.state.errorMsg && <h3>{this.state.errorMsg}</h3>}
        <h3>Start a new release</h3>
        <div>
          <ButtonToolbar>
            {config.XPI_PRODUCTS.map(product => (
              <Button
                key={product.product}
                bsStyle={this.state.product === product ? 'primary' : 'default'}
                bsSize="large"
                onClick={() => this.refreshManifest(product)}
              >
                {product.prettyName}
              </Button>
            ))}
          </ButtonToolbar>
        </div>
        <Collapse in={this.state.product.branch && this.state.product.branch !== ''}>
          <div style={{ paddingTop: '10px', paddingBottom: '10px' }}>
            <FormGroup>
              <ControlLabel>Manifest Revision</ControlLabel>
              <InputGroup>
                <DropdownButton
                  componentClass={InputGroup.Button}
                  id="input-dropdown-addon"
                  title="Suggested revisions"
                >
                  {this.state.commits && this.state.commits.map(commit => (
                    <MenuItem
                      onClick={() => this.handlePickCommit(commit.revision)}
                      key={commit.revision}
                      title={
                        `${commit.revision} - ${commit.message}`
                      }
                    >
                      {commit.revision}
                      {' '} - {' '}
                      {maybeShorten(commit.message)}
                    </MenuItem>
                  ))}
                </DropdownButton>
                <FormControl type="text" value={this.state.revision} onChange={this.handleRevisionChange} />
              </InputGroup>
            </FormGroup>
          </div>
        </Collapse>
        <Collapse in={this.state.xpis && this.state.xpis.length > 0} >
          <div style={{ paddingTop: '10px', paddingBottom: '10px' }}>
            <FormGroup>
              <ControlLabel>Available XPIs</ControlLabel>
              <InputGroup>
                <DropdownButton
                  componentClass={InputGroup.Button}
                  id="input-dropdown-addon"
                  title="XPIs"
                >
                  {this.state.xpis && this.state.xpis.map(xpi => (
                    <MenuItem
                      onClick={() => this.handleXPIPick(
                        xpi.manifest_revision,
                        xpi.xpi_name,
                        xpi.owner,
                        xpi.repo,
                        this.state.product.branch,
                      )}
                      key={xpi.xpi_name}
                      title={xpi.xpi_name}
                    >
                      {xpi.xpi_name}
                    </MenuItem>
                  ))}
                </DropdownButton>
                <FormControl type="text" value={this.state.xpiName} readOnly />
              </InputGroup>
            </FormGroup>
          </div>
        </Collapse>
        <Collapse in={this.state.xpiName !== ''} >
          <div style={{ paddingTop: '10px', paddingBottom: '10px' }}>
            <FormGroup>
              <ControlLabel>Available revisions</ControlLabel>
              <InputGroup>
                <DropdownButton
                  componentClass={InputGroup.Button}
                  id="input-dropdown-addon"
                  title="XPI revisions"
                >
                  {this.state.xpiRevisions.map(commit => (
                    <MenuItem
                      onClick={() => this.handleXPIRevision(commit)}
                      key={commit.revision}
                      title={
                        `${commit.revision} - ${commit.message}`
                      }
                    >
                      {commit.revision}
                      {' '} - {' '}
                      {maybeShorten(commit.message)}
                    </MenuItem>
                  ))}
                </DropdownButton>
                <FormControl type="text" value={this.state.xpiRevision} onChange={this.handleXPIRevision} />
              </InputGroup>
            </FormGroup>
          </div>
        </Collapse>
        <Collapse in={this.state.xpiRevision !== ''}>
          <div>
            <div className="text-muted">Version: {this.state.xpiVersion || ''}</div>
            <div className="text-muted">Build number: {this.state.buildNumber || ''}</div>
            <div style={{ paddingTop: '10px', paddingBottom: '10px' }}>
              <Button type="submit" bsStyle="primary" onClick={this.open} disabled={!this.readyToSubmit()}>Start tracking it!</Button>
              <Modal show={this.state.showModal} onHide={this.close}>
                <Modal.Header closeButton>
                  <Modal.Title>Start release</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                  {this.renderBody()}
                </Modal.Body>
                <Modal.Footer>
                  <Collapse in={!this.state.submitted}>
                    <div>
                      <Button
                        onClick={this.submitRelease}
                        bsStyle="danger"
                        disabled={!this.context.authController.userSession || this.state.inProgress}
                      >
                        Do eet!
                      </Button>
                      <Button onClick={this.close} bsStyle="primary">Close</Button>
                    </div>
                  </Collapse>
                </Modal.Footer>
              </Modal>
            </div>
          </div>
        </Collapse>
      </div>
    );
  }
}
