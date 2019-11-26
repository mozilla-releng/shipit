import React, { Fragment } from 'react';
import { Button, Modal } from 'react-bootstrap';

export default class ProductDisabler extends React.PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      showModal: false,
      modalContent: '',
      errorMsg: null,
    };
  }

  getIcon = (loading, enabled) => {
    if (loading) {
      return '❔';
    }

    if (enabled) {
      return '✅';
    }

    return '❌';
  };

  openModal = (pb) => {
    this.setState({ showModal: true, modalContent: this.renderModal(pb) });
  };

  closeModal = () => {
    this.setState({
      showModal: false,
      errorMsg: null,
    });
  };

  renderModal = (pb) => {
    // onStateChange will accept a single productBranch entry
    const { onStateChange } = this.props;

    return (
      <Fragment>
        <Modal.Header closeButton>
          <Modal.Title>
            {pb.enabled ? 'Disable' : 'Enable'} updates for&nbsp;
            {pb.prettyProduct} {pb.prettyBranch}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          I have got a lovely bunch of coconuts
        </Modal.Body>
        <Modal.Footer>
          <Button
            onClick={() => onStateChange(pb)}
            bsStyle="danger"
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
        <h3>Product Status</h3>
        {productBranches.map(pb => (
          <Button
            key={`${pb.product}-${pb.branch}`}
            onClick={() => this.openModal(pb)}
            disabled={disabled}
          >
            {pb.prettyProduct} : {pb.prettyBranch}
            {this.getIcon(loading, pb.enabled)}
          </Button>
        ))}
        <Modal show={this.state.showModal} onHide={this.closeModal}>
          {this.state.errorMsg
            ? (
              <div>
                <p>{this.state.errorMsg}</p>
              </div>
            ) : (
              this.state.modalContent
            )
          }
        </Modal>
      </Fragment>
    );
  }
}
