import React from 'react';
import {
  ButtonToolbar, Button, FormGroup, FormControl, ControlLabel, InputGroup, DropdownButton,
  MenuItem, Collapse, Modal, Tooltip, OverlayTrigger,
} from 'react-bootstrap';
import { object } from 'prop-types';
import { NavLink } from 'react-router-dom';
import * as moment from 'moment';

import config, { SHIPIT_API_URL } from '../../config';
import { getApiHeaders, getBuildNumbers, getShippedReleases } from '../../components/api';
import { getPushes, getVersion, getLocales } from '../../components/vcs';
import maybeShorten from '../../components/text';

export default class NewRelease extends React.Component {
  static contextTypes = {
    authController: object.isRequired,
  };

  constructor(...args) {
    super(...args);
    this.state = Object.assign(this.defaultState());
  }

  set version(version) {
    this.setState({
      version,
    });
  }

  defaultState = () => ({
    selectedProduct: {},
    selectedBranch: {},
    suggestedRevisions: [],
    revision: '',
    version: '',
    buildNumber: 0,
    partialVersions: [],
    showModal: false,
    errorMsg: null,
    submitted: false,
    inProgress: false,
    releaseDate: '',
    releaseTime: '',
  });

  readyToSubmit = () => (
    this.state.version !== '' &&
    this.state.buildNumber > 0 &&
    (this.state.selectedProduct.enablePartials ?
      this.state.partialVersions.length > 0 : true)
  );

  open = () => {
    this.setState({ showModal: true });
  };

  close = () => {
    if (!this.state.errorMsg) {
      this.setState(Object.assign(this.defaultState()));
    }
  };

  handleBranch = async (branch) => {
    this.setState({
      selectedBranch: branch,
      revision: '',
      version: '',
      buildNumber: 0,
      partialVersions: [],
    });
    const { accessToken } = this.context.authController.getUserSession();
    const pushes = await getPushes(branch.repo, branch.branch, accessToken);
    const suggestedRevisions = pushes.filter(push => push.desc.indexOf('DONTBUILD') === -1);
    this.setState({ suggestedRevisions });
  };

  guessBuildId = async () => {
    const buildNumbers = await getBuildNumbers(
      this.state.selectedProduct.product,
      this.state.selectedBranch.branch,
      this.state.version,
    );
    const nextBuildNumber = buildNumbers.length !== 0 ? Math.max(...buildNumbers) + 1 : 1;
    this.setState({
      buildNumber: nextBuildNumber,
    });
  };

  // Poor man's RC detection. xx.0 is the only pattern that matches RC
  isRc = (version) => {
    const parts = version.split('.');
    if (parts.length !== 2) {
      return false;
    }
    if (parts[1] !== '0') {
      return false;
    }
    return true;
  };

  guessPartialVersions = async () => {
    const { product } = this.state.selectedProduct;
    const {
      branch, rcBranch, numberOfPartials, alternativeBranch,
    } = this.state.selectedBranch;
    const numberOfPartialsOrDefault = numberOfPartials || 3;

    const shippedReleases = await getShippedReleases(product, branch);
    const shippedBuilds = shippedReleases.map(r => `${r.version}build${r.build_number}`);
    // take first N releases
    const suggestedBuilds = shippedBuilds.slice(0, numberOfPartialsOrDefault);

    // alternativeBranch is used for find partials from a different branch, and
    // usually used for ESR releases
    let suggestedAlternativeBuilds = [];
    if (suggestedBuilds.length < numberOfPartialsOrDefault && alternativeBranch) {
      const alternativeReleases = await getShippedReleases(product, alternativeBranch);
      const shippedAlternativeBuilds = alternativeReleases.map(r => `${r.version}build${r.build_number}`);
      suggestedAlternativeBuilds = shippedAlternativeBuilds.slice(
        0,
        numberOfPartialsOrDefault - suggestedBuilds.length,
      );
    }
    // if RC, also add last shipped beta
    let suggestedRcBuilds = [];
    if (rcBranch && this.isRc(this.state.version)) {
      const rcShippedReleases = await getShippedReleases(product, rcBranch);
      const rcLastBuild = `${rcShippedReleases[0].version}build${rcShippedReleases[0].build_number}`;
      suggestedRcBuilds = [rcLastBuild];
    }

    this.setState({
      partialVersions: suggestedBuilds.concat(suggestedRcBuilds, suggestedAlternativeBuilds),
    });
  };

  handleSuggestedRev = async (rev) => {
    this.setState({
      revision: rev.node,
    });
    const { accessToken } = this.context.authController.getUserSession();
    this.version = await getVersion(
      this.state.selectedBranch.repo, rev.node,
      this.state.selectedProduct.appName,
      this.state.selectedBranch.versionFile,
      accessToken,
    );
    await this.guessBuildId();
    if (this.state.selectedProduct.enablePartials) {
      await this.guessPartialVersions();
    }
  };

  handleProduct = (product) => {
    this.setState({
      selectedProduct: product,
      selectedBranch: {},
      suggestedRevisions: [],
      revision: '',
      version: '',
      buildNumber: 0,
      partialVersions: [],
    });
  };

  handleRevisionChange = async (event) => {
    this.setState({
      revision: event.target.value,
    });
    this.version = await getVersion(
      this.state.selectedBranch.repo, event.target.value,
      this.state.selectedProduct.appName,
      this.state.selectedBranch.versionFile,
    );
    await this.guessBuildId();
    if (this.state.selectedProduct.enablePartials) {
      await this.guessPartialVersions();
    }
  };

  handlePartialsChange = async (event) => {
    this.setState({
      partialVersions: event.target.value.split(',').map(v => v.trim()),
    });
  };

  handleReleaseDateChange = (event) => {
    this.setState({
      releaseDate: event.target.value,
    });
  };

  handleReleaseTimeChange = (event) => {
    this.setState({
      releaseTime: event.target.value,
    });
  };


  generateReleaseEta = (date, time) => {
    if (date !== '' && time !== '') {
      return moment(`${date}T${time}Z`).toISOString();
    }
    return '';
  };


  submitRelease = async () => {
    this.setState({ inProgress: true });
    const { product } = this.state.selectedProduct;
    const {
      branch, repo, rcBranch, rcBranchVersionPattern, rcRepo, productKey,
      alternativeBranch, alternativeRepo,
    } = this.state.selectedBranch;
    const releaseObj = {
      branch,
      build_number: this.state.buildNumber,
      product,
      release_eta: this.generateReleaseEta(this.state.releaseDate, this.state.releaseTime),
      repo_url: repo,
      revision: this.state.revision,
      version: this.state.version,
    };

    if (this.state.selectedProduct.enablePartials) {
      const partialUpdates = await Promise.all(this.state.partialVersions.map(async (ver) => {
        const [version, buildNumber] = ver.split('build');
        let partialBranch = branch;
        let partialRepo = repo;
        // override the branch in case this is an RC and the version matches the (beta) pattern
        if (this.isRc(releaseObj.version) && rcBranch && rcBranchVersionPattern.test(version)) {
          partialBranch = rcBranch;
          partialRepo = rcRepo;
        }
        let shippedReleases = await getShippedReleases(
          product, partialBranch, version,
          buildNumber,
        );
        if (shippedReleases.length === 0 && alternativeBranch) {
          partialBranch = alternativeBranch;
          partialRepo = alternativeRepo;
          shippedReleases = await getShippedReleases(product, partialBranch, version, buildNumber);
        }
        if (shippedReleases.length !== 1) {
          this.setState({
            inProgress: false,
            errorMsg: `Cannot obtain proper information for ${product} ${partialBranch} ${version} build ${buildNumber}`,
          });
          return null;
        }
        const { revision } = shippedReleases[0];
        const locales = await getLocales(
          partialRepo, revision,
          this.state.selectedProduct.appName,
        );
        return [
          version, { buildNumber: parseInt(buildNumber, 10), locales },
        ];
      }));
      const partialUpdatesFlattened = {};
      partialUpdates.forEach(([v, e]) => {
        partialUpdatesFlattened[v] = e;
      });
      releaseObj.partial_updates = partialUpdatesFlattened;
    }
    if (productKey) {
      releaseObj.product_key = productKey;
    }

    await this.doEet(releaseObj);
    this.setState({ inProgress: false });
  };

  doEet = async (releaseObj) => {
    if (!this.context.authController.userSession) {
      this.setState({ errorMsg: 'Login required!' });
      return;
    }
    const url = `${SHIPIT_API_URL}/releases`;
    const { accessToken } = this.context.authController.getUserSession();
    const headers = getApiHeaders(accessToken);
    try {
      const body = JSON.stringify(releaseObj);
      const response = await fetch(url, { method: 'POST', headers, body });
      if (!response.ok) {
        const responseJson = await response.json();
        this.setState({ errorMsg: responseJson.detail ? `Error: ${responseJson.detail}` : 'Unknown server error' });
        return;
      }
      this.setState({ submitted: true });
    } catch (e) {
      this.setState({ errorMsg: 'Server issues!' });
      throw e;
    }
  };


  releaseEtaValidationState = () => {
    const { releaseDate, releaseTime } = this.state;
    if (releaseDate === '' && releaseTime === '') {
      return null;
    } else if (releaseDate !== '' && releaseTime !== '') {
      return 'success';
    }
    return 'error';
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
      const url = `${config.TREEHERDER_URL}/#/jobs?repo=${this.state.selectedBranch.project}&revision=${this.state.revision}`;
      const buildName =
        `${this.state.selectedProduct.product}-${this.state.version}-build${this.state.buildNumber}`;
      return (
        <div>
          <h4>The following release will be submitted:</h4>
          <div>
            <a href={url}>{buildName}</a>
          </div>
        </div>
      );
    }
    return (
      <div>
        Done. Start the release from <NavLink to="/">the list of releases</NavLink>
      </div>
    );
  };


  renderPartials = () => {
    const { selectedProduct, partialVersions } = this.state;
    if (selectedProduct && selectedProduct.enablePartials) {
      return (
        <FormGroup>
          <InputGroup>
            <InputGroup.Addon>Partial versions</InputGroup.Addon>
            <FormControl
              type="text"
              value={partialVersions.join(',')}
              onChange={this.handlePartialsChange}
            />
          </InputGroup>
          <small>
            Coma-separated list of versions with build number, e.g. 59.0b8build7.
            UX will be improved!
          </small>
        </FormGroup>
      );
    }
    return '';
  };


  renderReleaseEta = () => {
    if (this.state.selectedBranch.enableReleaseEta) {
      const tooltip = (
        <Tooltip id="releaseEtaHelp">
          Date and time at which the release is planned to be public. This date
          is used by Balrog to automatically activate the new rule. One extra
          condition: The new rule should be signed off by a set of human before
          going live. In the case the date expires, the rule will go live
          immediately after every signoff is made.
        </Tooltip>
      );
      return (
        <FormGroup validationState={this.releaseEtaValidationState()}>
          <InputGroup>
            <OverlayTrigger placement="right" overlay={tooltip}>
              <InputGroup.Addon>Release ETA (UTC)</InputGroup.Addon>
            </OverlayTrigger>
            <FormControl
              type="date"
              value={this.state.releaseDate}
              onChange={this.handleReleaseDateChange}
              style={{ width: '200px' }}
              min={moment().format('YYYY-MM-DD')}
            />
            <FormControl
              type="time"
              value={this.state.releaseTime}
              onChange={this.handleReleaseTimeChange}
              style={{ width: '150px' }}
            />
            <FormControl.Feedback />
          </InputGroup>
        </FormGroup>
      );
    }
    return '';
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
        <h3>Start a new release</h3>
        <div>
          <ButtonToolbar>
            {config.PRODUCTS.map(product => (
              <Button
                key={product.product}
                bsStyle={this.state.selectedProduct === product ? 'primary' : 'default'}
                bsSize="large"
                onClick={() => this.handleProduct(product)}
              >
                {product.prettyName}
              </Button>
            ))}
          </ButtonToolbar>
        </div>
        <Collapse in={this.state.selectedProduct.branches
                && this.state.selectedProduct.branches.length > 0}
        >
          <div style={{ paddingTop: '10px', paddingBottom: '10px' }}>
            <ButtonToolbar>
              {this.state.selectedProduct.branches &&
               this.state.selectedProduct.branches.map(branch => (
                 <Button
                   key={`${this.state.selectedProduct.product}-${branch.prettyName}`}
                   bsStyle={this.state.selectedBranch === branch ? 'primary' : 'default'}
                   bsSize="large"
                   onClick={() => this.handleBranch(branch)}
                 >
                   {branch.prettyName}
                 </Button>
              ))}
            </ButtonToolbar>
          </div>
        </Collapse>
        <Collapse in={this.state.selectedBranch.repo && this.state.selectedBranch.repo.length > 0}>
          <div>
            <FormGroup>
              <ControlLabel>Revision</ControlLabel>
              <InputGroup>
                <DropdownButton
                  componentClass={InputGroup.Button}
                  id="input-dropdown-addon"
                  title="Suggested revisions"
                >
                  {this.state.suggestedRevisions && this.state.suggestedRevisions.map(rev => (
                    <MenuItem
                      onClick={() => this.handleSuggestedRev(rev)}
                      key={rev.node}
                      title={
                        `${rev.date.toString()} - ${rev.node} - ${rev.desc}`
                      }
                    >
                      {rev.date.toDateString()}
                      {' '} - {' '}
                      {rev.node.substring(0, 8)}
                      {' '} - {' '}
                      {maybeShorten(rev.desc)}
                    </MenuItem>
                  ))}
                </DropdownButton>
                <FormControl type="text" value={this.state.revision} onChange={this.handleRevisionChange} />
              </InputGroup>
            </FormGroup>
            {this.renderReleaseEta()}
            {this.renderPartials()}
            <div className="text-muted">Version: {this.state.version || ''}</div>
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
                        Do eeet!
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
