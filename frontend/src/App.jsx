import { Auth0Provider } from '@auth0/auth0-react';
import CssBaseline from '@mui/material/CssBaseline';
import { StyledEngineProvider, ThemeProvider } from '@mui/material/styles';
import React from 'react';
import { GlobalStyles } from 'tss-react';
import config from './config';
import Main from './Main';
import theme from './theme';

const App = () => {
  return (
    <StyledEngineProvider injectFirst>
      <ThemeProvider theme={theme}>
        <GlobalStyles
          styles={{
            'html, body': {
              height: '100%',
            },
            '#root': {
              height: '100%',
            },
          }}
        />
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
          sessionCheckExpiryDays={7}
        >
          <Main />
        </Auth0Provider>
      </ThemeProvider>
    </StyledEngineProvider>
  );
};

export default App;
