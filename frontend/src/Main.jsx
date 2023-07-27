import React, { useEffect } from 'react';
import { BrowserRouter, Switch } from 'react-router-dom';
import { makeStyles } from '@material-ui/styles';
import axios from 'axios';
import Spinner from '@mozilla-frontend-infra/components/Spinner';
import Dashboard from './components/Dashboard';
import ErrorPanel from './components/ErrorPanel';
import RouteWithProps from './components/RouteWithProps';
import routes from './routes';
import useAction from './hooks/useAction';

const useStyles = makeStyles({
  '@global': {
    'html, body': {
      height: '100%',
    },
    '#root': {
      height: '100%',
    },
  },
});

function Main() {
  useStyles();
  const [backendStatus, checkBackendStatus] = useAction(() =>
    axios.get('/__heartbeat__')
  );

  useEffect(() => {
    checkBackendStatus();
  }, []);

  if (backendStatus.loading) {
    return (
      <BrowserRouter>
        <Dashboard group="Loading..." disabled>
          <Spinner loading />
        </Dashboard>
      </BrowserRouter>
    );
  }

  if (backendStatus.error) {
    return (
      <BrowserRouter>
        <Dashboard title="Error" disabled>
          <ErrorPanel
            fixed
            error={`Error contacting Shipit backend: ${backendStatus.error.toString()}. Are you connected to the VPN?`}
          />
        </Dashboard>
      </BrowserRouter>
    );
  }

  return (
    <BrowserRouter>
      <Switch>
        {routes.map(({ path, ...rest }) => (
          <RouteWithProps key={path || 'not-found'} path={path} {...rest} />
        ))}
      </Switch>
    </BrowserRouter>
  );
}

export default Main;
