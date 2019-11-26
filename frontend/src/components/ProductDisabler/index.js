import React, { Fragment } from 'react';
import { Button, Glyphicon, Modal, Label } from 'react-bootstrap';

// TODO: dunno why putting this in styles.css isn't working
const pbLabelStyle = {
  paddingLeft: '5px',
  paddingRight: '5px',
  cursor: 'initial',
  color: '#9d9d9d',
};

const verticalDivider = {
  marginLeft: '5px',
  borderLeft: '1px solid #ddd',
  borderRight: '1px solid #ddd',
  height: '100%',
};

export default class ProductDisabler extends React.PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      showModal: false,
      modalContent: '',
    };
  }

  getIcon = (loading, enabled) => {
    if (loading) {
      return 'question-sign';
    }

    if (enabled) {
      return 'ok-sign';
    }

    return 'remove-sign';
  };

  getButtonStyle = (loading, enabled) => {
    if (loading) {
      return 'warning';
    }

    if (enabled) {
      return 'success';
    }

    return 'danger';
  };

  openModal = (pb) => {
    this.setState({ showModal: true, modalContent: this.renderModal(pb) });
  };

  closeModal = () => {
    this.setState({
      showModal: false,
    });
  };

  renderModal = (pb) => {
    // onStateChange will accept a single productBranch entry
    const { onStateChange, errorMsg } = this.props;

    return (
      <Fragment>
        <Modal.Header closeButton>
          <Modal.Title>
            {pb.enabled ? 'Disable' : 'Enable'} updates for&nbsp;
            {pb.prettyProduct} {pb.prettyBranch}?
          </Modal.Title>
        </Modal.Header>
        {errorMsg && (
          <Modal.Body>
            {errorMsg}
          </Modal.Body>
        )}
        <Modal.Footer>
          <Button
            onClick={() => onStateChange(pb)}
            bsStyle={pb.enabled ? 'danger' : 'success'}
          >
            {pb.enabled ? 'Disable releases' : 'Enable releases'}
          </Button>
          <Button onClick={this.closeModal} bsStyle="primary">Close</Button>
        </Modal.Footer>
      </Fragment>
    );
  }

  render() {
    /* productBranches looks like:

       [
         {
           "product": "firefox",
           "branch": "mozilla-beta",
           "prettyProduct": "Firefox Desktop",
           "prettyBranch": "Beta",
           "enabled": true,
         }
       ],
       ...
    */
    const { productBranches, disabled, loading } = this.props;

    return (
      <Fragment>
        <Label>Automated Release Status</Label>
        {productBranches.map(pb => (
          <Fragment key={`${pb.product}-${pb.branch}`}>
            <span style={verticalDivider} />
            <span style={pbLabelStyle}>{pb.prettyProduct} : {pb.prettyBranch}</span>
            <Button
              onClick={() => this.openModal(pb)}
              disabled={disabled}
              bsSize="xsmall"
              bsStyle={this.getButtonStyle(loading, pb.enabled)}
            >
              <Glyphicon glyph={this.getIcon(loading, pb.enabled)} />
            </Button>
          </Fragment>
        ))}
        <Modal show={this.state.showModal} onHide={this.closeModal}>
          {this.state.modalContent}
        </Modal>
      </Fragment>
    );
  }
}
