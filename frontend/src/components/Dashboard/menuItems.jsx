import React from 'react';
import AddBoxIcon from '@material-ui/icons/AddBox';
import AutorenewIcon from '@material-ui/icons/Autorenew';
import CheckCircleIcon from '@material-ui/icons/CheckCircle';

export default [
  {
    title: 'Firefox',
    items: [
      {
        title: 'New',
        to: '/new',
        Icon: <AddBoxIcon />,
      },
      {
        title: 'Pending',
        to: '/',
        Icon: <AutorenewIcon />,
      },
      {
        title: 'Recent',
        to: '/recent',
        Icon: <CheckCircleIcon />,
      },
    ],
  },
  {
    title: 'Security',
    items: [
      {
        title: 'New',
        to: '/new?group=security',
        Icon: <AddBoxIcon />,
      },
      {
        title: 'Pending',
        to: '/?group=security',
        Icon: <AutorenewIcon />,
      },
      {
        title: 'Recent',
        to: '/recent?group=security',
        Icon: <CheckCircleIcon />,
      },
    ],
  },
  {
    title: 'Extensions',
    items: [
      {
        title: 'New',
        to: '/newxpi',
        Icon: <AddBoxIcon />,
      },
      {
        title: 'Pending',
        to: '/xpi',
        Icon: <AutorenewIcon />,
      },
      {
        title: 'Recent',
        to: '/recentxpi',
        Icon: <CheckCircleIcon />,
      },
    ],
  },
];
