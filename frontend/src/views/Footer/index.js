import React from 'react';
import { Navbar, Nav, NavItem } from 'react-bootstrap';
import { object } from 'prop-types';

import config, { SHIPIT_API_URL } from '../../config';
import ProductDisabler from '../../components/ProductDisabler';
import { getApiHeaders } from '../../components/api';

export default class Navigation extends React.Component {
  static contextTypes = {
    authController: object.isRequired,
  };

  constructor(...args) {
    super(...args);
    this.state = {
      loaded: false,
      disabledProducts: [],
      errorMsg: null,
    };
  }

  async componentDidMount() {
    await this.getDisabledProducts();
  }

  getDisabledProducts = async () => {
    try {
      const req = await fetch(`${SHIPIT_API_URL}/disabled-products`);
      const disabledProducts = await req.json();
      this.setState({
        loaded: true,
        disabledProducts,
      });
    } catch (e) {
      this.setState({
        loaded: true,
        disabledProducts: [],
      });
      throw e;
    }
  };

  handleStateChange = async (productBranch) => {
    const url = productBranch.disabled
      ? `${SHIPIT_API_URL}/disabled-products?product=${productBranch.product}&branch=${productBranch.branch}`
      : `${SHIPIT_API_URL}/disabled-products`;
    const method = productBranch.disabled ? 'DELETE' : 'POST';
    const body = productBranch.enabled
      ? null
      : JSON.stringify({ product: productBranch.product, branch: productBranch.branch });

    if (!this.context.authController.userSession) {
      this.setState({ errorMsg: 'Login required!' });
      return;
    }

    const { accessToken } = this.context.authController.getUserSession();
    const headers = getApiHeaders(accessToken);
    try {
      const response = await fetch(url, { method, headers, body });
      if (!response.ok) {
        this.setState({ errorMsg: 'Auth failure!' });
        return;
      }
      window.location.reload();
    } catch (e) {
      this.setState({ errorMsg: 'Server issues!' });
      throw e;
    }
  };

  render() {
    const { loaded, disabledProducts, errorMsg } = this.state;

    return (
      <div>
        <Navbar fluid inverse fixedBottom collapseOnSelect>
          <Nav>
            <NavItem>
              <ProductDisabler
                productBranches={config.PRODUCTS.flatMap(product =>
                  product.branches.filter(branch => branch.disableable).map(pb => ({
                    product: product.product,
                    branch: pb.branch,
                    prettyProduct: product.prettyName,
                    prettyBranch: pb.prettyName,
                    disabled: product.product in disabledProducts
                      && disabledProducts[product.product].includes(pb.branch),
                  })))}
                onStateChange={this.handleStateChange}
                disabled={!this.context.authController.userSession}
                loading={!loaded}
                errorMsg={errorMsg}
              />
            </NavItem>
          </Nav>
        </Navbar>
      </div>
    );
  }
}
