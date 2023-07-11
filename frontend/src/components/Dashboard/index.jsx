import React, { Fragment, useState } from 'react';
import { string, node, bool } from 'prop-types';
import { Helmet } from 'react-helmet';
import { makeStyles } from '@material-ui/styles';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import menuItems from './menuItems';
import Link from '../../utils/Link';
import UserMenu from './UserMenu';
import SettingsMenu from './SettingsMenu';
import ReleasesMenu from './ReleasesMenu';
import Button from '../Button';
import Footer from '../../views/Footer';
import { CONTENT_MAX_WIDTH, APP_BAR_HEIGHT } from '../../utils/constants';
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import Collapse from "@material-ui/core/Collapse";
import ExpandLessIcon from "@material-ui/icons/ExpandLess";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";


const useStyles = makeStyles(theme => ({
  appbar: {
    height: APP_BAR_HEIGHT,
  },
  title: {
    textDecoration: 'none',
  },
  main: {
    maxWidth: CONTENT_MAX_WIDTH,
    height: '100%',
    margin: '0 auto',
    padding: `${theme.spacing(12)}px ${APP_BAR_HEIGHT}px`,
  },
  nav: {
    display: 'flex',
    flex: 1,
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  link: {
    textDecoration: 'none',
    color: 'inherit',
  },
  disabledLink: {
    textDecoration: 'none',
    color: theme.palette.grey[500],
    pointerEvents: 'none',
  },
  buttonWithIcon: {
    paddingLeft: theme.spacing(2),
  },
}));

export default function Dashboard(props) {
  const classes = useStyles();
  const { title, children, disabled } = props;

  return (
    <Fragment>
      <Helmet>
        <title>{title} - Ship-It!</title>
      </Helmet>
      <AppBar className={classes.appbar} position="fixed">
        <Toolbar>
          <Typography
            className={classes.title}
            color="inherit"
            variant="h6"
            noWrap
            component={Link}
            to="/">
            Ship-It Admin ┃ {title}
          </Typography>
          <nav className={classes.nav}>
            {/* {menuItems.main.map(menuItem => (
              <Link
                key={menuItem.value}
                className={disabled ? classes.disabledLink : classes.link}
                nav
                to={menuItem.path}>
                <Button color="inherit">{menuItem.value}</Button>
              </Link>
            ))} */}
            <ReleasesMenu />
            <SettingsMenu disabled={disabled} />
            <UserMenu />
          </nav>
        </Toolbar>
      </AppBar>
      <Paper square elevation={0}>
        <main className={classes.main}>{children}</main>
      </Paper>
      {!disabled && <Footer />}
    </Fragment>
  );
}

Dashboard.prototype = {
  children: node.isRequired,
  // A title for the view.
  title: string.isRequired,
  disabled: bool,
};
