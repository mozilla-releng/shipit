import { Auth0Provider } from '@auth0/auth0-react';
import CssBaseline from '@material-ui/core/CssBaseline';
import { ThemeProvider } from '@material-ui/styles';
import React, { Fragment } from 'react';
import config from './config';
import Main from './Main';
import theme from './theme';

const App = () => {
  return (
    <Fragment>
      <CssBaseline />
      <Auth0Provider
        domain={config.AUTH0.domain}
        clientId={config.AUTH0.clientID}
        redirectUri={config.AUTH0.redirectUri}
        audience={config.AUTH0.audience}
        scope={config.AUTH0.scope}
        authorizationParams={{
          audience: config.AUTH0.audience,
          scope: config.AUTH0.scope,
        }}
        leeway={30}
        cacheLocation="localstorage"
      >
        <ThemeProvider theme={theme}>
          <Main />
        </ThemeProvider>
      </Auth0Provider>
    </Fragment>
  );
};

export default App;
