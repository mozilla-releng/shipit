import React, { Fragment } from 'react';
import { string, node, bool } from 'prop-types';
import { Helmet } from 'react-helmet';
import { makeStyles, useTheme } from '@material-ui/styles';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import Breadcrumbs from '@material-ui/core/Breadcrumbs';
import Box from '@material-ui/core/Box';
import ExtensionIcon from '@material-ui/icons/Extension';
import UserMenu from './UserMenu';
import SettingsMenu from './SettingsMenu';
import ReleasesMenu from './ReleasesMenu';
import Footer from '../../views/Footer';
import { CONTENT_MAX_WIDTH, APP_BAR_HEIGHT } from '../../utils/constants';

const useStyles = makeStyles(theme => ({
  appbar: {
    height: APP_BAR_HEIGHT,
  },
  title: {
    color: '#fff',
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
  paper: {
    height: '100%',
    backgroundColor: 'transparent',
  },
  protocolLogo: {
    margin: '0px',
    marginRight: '.7%',
  },
  extensionIcon: {
    margin: '0px',
    marginRight: '.5%',
  },
}));

function Logo(props) {
  const { group } = props;
  const classes = useStyles();

  if (group && group.toLowerCase().includes('firefox')) {
    return (
      <Box
        component="div"
        className={`mzp-c-logo mzp-t-logo-sm mzp-t-product-firefox ${classes.protocolLogo}`}
      />
    );
  }

  if (group && group.toLowerCase().includes('extensions')) {
    return <ExtensionIcon className={classes.extensionIcon} />;
  }

  return (
    <Box
      component="div"
      className={`mzp-c-logo mzp-t-logo-sm mzp-t-product-mozilla ${classes.protocolLogo}`}
    />
  );
}

export default function Dashboard(props) {
  const classes = useStyles();
  const { title, children, disabled, group } = props;
  const theme = useTheme();
  const css = `
    #root {
      height: auto;
    }

    html body {
      background-color: ${theme.palette.background.default};
    }
  `;

  return (
    <Fragment>
      <Helmet>
        <title>
          Ship-It / {group ? `${group} / ` : ''}
          {title || ''}
        </title>
        <style>{css}</style>
      </Helmet>
      <AppBar className={classes.appbar} position="fixed">
        <Toolbar>
          <Logo group={group} />
          <Breadcrumbs aria-label="breadcrumb" className={classes.title}>
            {group && (
              <Typography color="inherit" variant="h6" noWrap>
                {group}
              </Typography>
            )}
            {title && (
              <Typography color="inherit" variant="h6" noWrap>
                {title}
              </Typography>
            )}
          </Breadcrumbs>
          <nav className={classes.nav}>
            <ReleasesMenu disabled={disabled} />
            <SettingsMenu disabled={disabled} />
            <UserMenu />
          </nav>
        </Toolbar>
      </AppBar>
      <Paper square elevation={0} className={classes.paper}>
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
