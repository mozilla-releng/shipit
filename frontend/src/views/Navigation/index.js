import React from 'react';
import { Navbar, Nav } from 'react-bootstrap';
import { NavLink } from 'react-router-dom';

import CredentialsMenu from '../../views/CredentialsMenu';
import { RELEASE_CHANNEL } from '../../config';

export default function Navigation() {
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
          {RELEASE_CHANNEL !== 'production' &&
            <Navbar.Brand>
              <NavLink to="/xpi">XPI Releases</NavLink>
            </Navbar.Brand>
          }
          {RELEASE_CHANNEL !== 'production' &&
            <Navbar.Brand>
              <NavLink to="/newxpi">New XPI Release</NavLink>
            </Navbar.Brand>
          }
        </Navbar.Header>
        <Nav pullRight>
          <CredentialsMenu />
        </Nav>
      </Navbar>
    </div>
  );
}
