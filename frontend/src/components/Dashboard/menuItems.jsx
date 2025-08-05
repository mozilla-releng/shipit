import AddBoxIcon from '@mui/icons-material/AddBox';
import AutorenewIcon from '@mui/icons-material/Autorenew';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import React from 'react';

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
    title: 'Thunderbird',
    items: [
      {
        title: 'New',
        to: '/new?group=thunderbird',
        Icon: <AddBoxIcon />,
      },
      {
        title: 'Pending',
        to: '/?group=thunderbird',
        Icon: <AutorenewIcon />,
      },
      {
        title: 'Recent',
        to: '/recent?group=thunderbird',
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
