import React from 'react';
import { Navbar, Nav, NavItem } from 'react-bootstrap';
import { NavLink } from 'react-router-dom';
import { object } from 'prop-types';

import config, { SHIPIT_API_URL } from '../../config';
import ProductDisabler from '../../components/ProductDisabler';
import CredentialsMenu from '../../views/CredentialsMenu';

export default class Navigation extends React.Component {
  static contextTypes = {
    authController: object.isRequired,
  };

  constructor(...args) {
    super(...args);
    this.state = {
      loaded: false,
      disabledProducts: [],
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

  // TODO: this sin't working for maple because it's not in the hardcodes
  handleStateChange = async (productBranch) => {
    const url = productBranch.enabled
      ? `${SHIPIT_API_URL}/disabled-products?product=${productBranch.product}&branch=${productBranch.branch}`
      : `${SHIPIT_API_URL}/disabled-products`;
    const method = productBranch.enabled ? 'DELETE' : 'POST';
    const body = productBranch.enabled
      ? null
      : JSON.stringify({ product: productBranch.product, branch: productBranch.branch });

    if (!this.context.authController.userSession) {
      // TODO: replace with error message that ends up in ProductDisabler
      // this.setState({ errorMsg: 'Login required!' });
      return;
    }

    const { accessToken } = this.context.authController.getUserSession();
    const headers = {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    };
    try {
      const response = await fetch(url, { method, headers, body });
      if (!response.ok) {
        // TODO: replace with error message that ends up in ProductDisabler
        // this.setState({ errorMsg: 'Auth failure!' });
        return;
      }
      // TODO: replace this
      // this.setState({ submitted: true });
      window.location.reload();
    } catch (e) {
      // TODO: replace with error message that ends up in ProductDisabler
      // this.setState({ errorMsg: 'Server issues!' });
      throw e;
    }
  };

  render() {
    const { loaded, disabledProducts } = this.state;

    return (
      <div>
        <Navbar fluid inverse staticTop collapseOnSelect>
          <Navbar.Header>
            <Navbar.Brand>
              <NavLink to="/">Releases</NavLink>
            </Navbar.Brand>
            <Navbar.Brand>
              <NavLink to="/new">New Release</NavLink>
            </Navbar.Brand>
          </Navbar.Header>
          <Nav>
            <NavItem>
              <ProductDisabler
                productBranches={config.PRODUCTS.flatMap(product =>
                  product.branches.filter(branch => branch.disableable).map(pb => ({
                    product: product.product,
                    branch: pb.branch,
                    prettyProduct: product.prettyName,
                    prettyBranch: pb.prettyName,
                    enabled: product.product in disabledProducts
                      && disabledProducts[product.product].includes(pb.branch),
                  })))}
                onStateChange={this.handleStateChange}
                disabled={!this.context.authController.userSession}
                loading={!loaded}
              />
            </NavItem>
          </Nav>
          <Nav pullRight>
            <CredentialsMenu />
          </Nav>
        </Navbar>
      </div>
    );
  }
}
