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
      modalItem: null,
    };
  }

  getIcon = (loading, disabled) => {
    if (loading) {
      return 'question-sign';
    }

    if (disabled) {
      return 'remove-sign';
    }

    return 'ok-sign';
  };

  getButtonStyle = (loading, disabled) => {
    if (loading) {
      return 'warning';
    }

    if (disabled) {
      return 'danger';
    }

    return 'success';
  };

  openModal = (pb) => {
    this.setState({ showModal: true, modalItem: pb });
  };

  closeModal = () => {
    this.setState({
      showModal: false,
      modalItem: null,
    });
  };

  render() {
    /* productBranches looks like:

       [
         {
           "product": "firefox",
           "branch": "mozilla-beta",
           "prettyProduct": "Firefox Desktop",
           "prettyBranch": "Beta",
           "disabled": true,
         }
       ],
       ...
    */
    const {
      productBranches, disabled, loading, onStateChange, errorMsg,
    } = this.props;
    const { modalItem } = this.state;

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
              bsStyle={this.getButtonStyle(loading, pb.disabled)}
            >
              <Glyphicon glyph={this.getIcon(loading, pb.disabled)} />
            </Button>
          </Fragment>
        ))}
        <Modal show={this.state.showModal} onHide={this.closeModal}>
          {modalItem && (
            <Fragment>
              <Modal.Header closeButton>
                <Modal.Title>
                  {modalItem.disabled ? 'Disable' : 'Enable'} updates for&nbsp;
                  {modalItem.prettyProduct} {modalItem.prettyBranch}?
                </Modal.Title>
              </Modal.Header>
              {errorMsg && (
                <Modal.Body>
                  {errorMsg}
                </Modal.Body>
              )}
              <Modal.Footer>
                <Button
                  onClick={() => onStateChange(modalItem)}
                  bsStyle={modalItem.disabled ? 'danger' : 'success'}
                >
                  {modalItem.disabled ? 'Disable releases' : 'Enable releases'}
                </Button>
                <Button onClick={this.closeModal} bsStyle="primary">Close</Button>
              </Modal.Footer>
            </Fragment>
          )}
        </Modal>
      </Fragment>
    );
  }
}
