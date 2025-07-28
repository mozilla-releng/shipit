import { useAuth0 } from '@auth0/auth0-react';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import axios from 'axios';
import React, { useEffect, useState } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router';
import Dashboard from './components/Dashboard';
import ErrorPanel from './components/ErrorPanel';
import { SHIPIT_API_URL, SHIPIT_PUBLIC_API_URL } from './config';
import useAction from './hooks/useAction';
import routes from './routes';

function setupAxiosInterceptors(getAccessTokenSilently, getIdTokenClaims) {
  axios.interceptors.request.use(async (config) => {
    const result = config;

    if (!config.url.startsWith('http')) {
      // No need to use tokens etc when the public API is used
      if (config.usePublicApi) {
        result.baseURL = SHIPIT_PUBLIC_API_URL;

        return result;
      }

      result.baseURL = SHIPIT_API_URL;

      if (config.authRequired) {
        const claims = getIdTokenClaims();

        if (claims) {
          const accessToken = await getAccessTokenSilently();

          result.headers.Authorization = `Bearer ${accessToken}`;
        }
      }
    }

    return result;
  });

  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      const errorMsg = error.response
        ? error.response.data.exception || error.response.data.detail || null
        : error.message;

      // If we found a more detailed error message
      // raise an Error with that instead.
      if (errorMsg !== null) {
        throw new Error(errorMsg);
      }

      throw error;
    },
  );
}

function Main() {
  const { isLoading, getAccessTokenSilently, getIdTokenClaims, user } =
    useAuth0();
  const [isReady, setReady] = useState(false);

  useEffect(() => {
    setupAxiosInterceptors(getAccessTokenSilently, getIdTokenClaims);
  }, [getAccessTokenSilently, isLoading]);

  useEffect(() => {
    if (!isReady && !isLoading) {
      setReady(true);
    }
  }, [isLoading]);

  const [backendStatus, checkBackendStatus] = useAction(() =>
    axios.get('/__heartbeat__'),
  );

  useEffect(() => {
    checkBackendStatus();
  }, []);

  if (!isReady || backendStatus.loading) {
    return (
      <BrowserRouter>
        <Dashboard disabled>
          <Box style={{ textAlign: 'center' }}>
            <CircularProgress />
          </Box>
        </Dashboard>
      </BrowserRouter>
    );
  }

  if (backendStatus.error) {
    return (
      <BrowserRouter>
        <Dashboard disabled>
          <ErrorPanel
            error={`Error contacting Shipit backend: ${backendStatus.error.toString()}. Are you connected to the VPN?`}
          />
        </Dashboard>
      </BrowserRouter>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        {routes.map(({ path, component, requiresAuth, exact, ...rest }) => (
          <Route
            key={path || 'not-found'}
            path={path}
            exact={exact}
            Component={component}
            render={() => (
              <Suspense fallback={null}>
                {requiresAuth && !user ? (
                  <Redirect to="/" />
                ) : (
                  <component {...renderProps} {...rest} />
                )}
              </Suspense>
            )}
          />
        ))}
      </Routes>
    </BrowserRouter>
  );
}

export default Main;
