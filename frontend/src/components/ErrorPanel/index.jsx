import Alert from '@mui/material/Alert';
import { string } from 'prop-types';
import React, { useState } from 'react';

export default function ErrorPanel({ error = null }) {
  const [currentError, setCurrentError] = useState(null);
  const [previousError, setPreviousError] = useState(null);
  const handleErrorClose = () => {
    setCurrentError(null);
  };

  if (error !== previousError) {
    setCurrentError(error);
    setPreviousError(error);
  }

  return currentError ? (
    <Alert severity="error" variant="filled" onClose={handleErrorClose}>
      {currentError}
    </Alert>
  ) : null;
}

ErrorPanel.propTypes = {
  /** Error to display. */
  error: string,
};
