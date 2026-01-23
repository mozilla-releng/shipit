import { useAuth0 } from '@auth0/auth0-react';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import axios from 'axios';
import React, { Suspense, useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router';
import Dashboard from './components/Dashboard';
import ErrorPanel from './components/ErrorPanel';
import { SHIPIT_API_URL, SHIPIT_PUBLIC_API_URL } from './config';
import useAction from './hooks/useAction';
import routes from './routes';

function setupAxiosInterceptors(getAccessTokenSilently, getIdTokenClaims) {
  const requestInterceptor = axios.interceptors.request.use(async (config) => {
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

  const responseInterceptor = axios.interceptors.response.use(
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

  return {
    request: requestInterceptor,
    response: responseInterceptor,
  };
}

function Main() {
  const { isLoading, getAccessTokenSilently, getIdTokenClaims, user } =
    useAuth0();
  const [isReady, setReady] = useState(false);

  useEffect(() => {
    const interceptors = setupAxiosInterceptors(
      getAccessTokenSilently,
      getIdTokenClaims,
    );

    return () => {
      axios.interceptors.request.eject(interceptors.request);
      axios.interceptors.response.eject(interceptors.response);
    };
  }, [getAccessTokenSilently, isLoading]);

  useEffect(() => {
    const validateTokenOnFirstLoad = async () => {
      if (user && !isLoading) {
        await getAccessTokenSilently();
      }
    };

    if (!isReady && !isLoading) {
      validateTokenOnFirstLoad()
        .catch(() => {})
        .finally(() => setReady(true));
    }
  }, [isLoading, user, getAccessTokenSilently, isReady]);

  const [backendStatus, checkBackendStatus] = useAction(() =>
    axios.get('/__heartbeat__'),
  );

  useEffect(() => {
    if (isReady) {
      checkBackendStatus();
    }
  }, [isReady]);

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
      <Suspense
        fallback={
          <Dashboard disabled>
            <Box style={{ textAlign: 'center' }}>
              <CircularProgress />
            </Box>
          </Dashboard>
        }
      >
        <Routes>
          {routes.map(
            ({ path, component: Component, requiresAuth, exact, ...rest }) => (
              <Route
                key={path || 'not-found'}
                path={path}
                exact={exact}
                element={
                  requiresAuth && !user ? (
                    <Navigate to="/" replace />
                  ) : (
                    <Component {...rest} />
                  )
                }
              />
            ),
          )}
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default Main;
