import ExtensionIcon from '@mui/icons-material/Extension';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Breadcrumbs from '@mui/material/Breadcrumbs';
import Chip from '@mui/material/Chip';
import Paper from '@mui/material/Paper';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import { bool, node, string } from 'prop-types';
import React, { Fragment } from 'react';
import { makeStyles } from 'tss-react/mui';
import { DEPLOYMENT_BRANCH } from '../../config';
import { APP_BAR_HEIGHT, CONTENT_MAX_WIDTH } from '../../utils/constants';
import Footer from '../../views/Footer';
import ReleasesMenu from './ReleasesMenu';
import SettingsMenu from './SettingsMenu';
import UserMenu from './UserMenu';

const useStyles = makeStyles()((theme) => ({
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
    padding: `${theme.spacing(12)} ${APP_BAR_HEIGHT}px`,
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
    margin: '0px !important',
    marginRight: '.7% !important',
  },
  extensionIcon: {
    margin: '0px',
    marginRight: '.5%',
  },
  environmentChip: {
    marginLeft: theme.spacing(2),
    fontWeight: 'bold',
    textTransform: 'uppercase',
    '&.local': {
      backgroundColor: theme.palette.success.main,
      color: theme.palette.success.contrastText,
    },
    '&.dev': {
      backgroundColor: theme.palette.warning.main,
      color: theme.palette.warning.contrastText,
    },
  },
}));

function Logo(props) {
  const { group } = props;
  const { classes } = useStyles();

  if (group?.toLowerCase().includes('firefox')) {
    return (
      <Box
        component="div"
        className={`mzp-c-logo mzp-t-logo-sm mzp-t-product-firefox ${classes.protocolLogo}`}
      />
    );
  }

  if (group?.toLowerCase().includes('extensions')) {
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
  const { classes } = useStyles();
  const { title, children, disabled, group } = props;

  return (
    <Fragment>
      <title>{`Ship-It / ${group ? `${group} / ` : ''}${title ?? ''}`}</title>
      <AppBar className={classes.appbar} position="fixed">
        <Toolbar>
          <Logo group={group} />
          <Breadcrumbs aria-label="breadcrumb" className={classes.title}>
            {group && (
              <Typography variant="h6" noWrap>
                {group}
              </Typography>
            )}
            {title && (
              <Typography variant="h6" noWrap>
                {title}
              </Typography>
            )}
          </Breadcrumbs>
          {DEPLOYMENT_BRANCH !== 'production' && (
            <Chip
              label={DEPLOYMENT_BRANCH}
              size="small"
              className={`${classes.environmentChip} ${DEPLOYMENT_BRANCH}`}
            />
          )}
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
