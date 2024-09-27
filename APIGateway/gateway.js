const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const rateLimit = require('express-rate-limit');

const app = express();

// Set default timeout value (in milliseconds)
const TIMEOUT = 5000; // 5 seconds timeout

// Concurrent requests limit for Parking Lots Management Service
const parkingLimiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute window
    max: 10, // Limit each IP to 10 requests per minute
    message: 'Too many requests to the Parking Service, please try again later.',
});

// Concurrent requests limit for User Management Service
const userLimiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute window
    max: 15, // Limit each IP to 15 requests per minute
    message: 'Too many requests to the User Management Service, please try again later.',
});

// Middleware to handle request timeouts
app.use((req, res, next) => {
    res.setTimeout(TIMEOUT, () => {
        res.status(504).send('Request timed out');
    });
    next();
});

// Proxy setup for Parking Lots Management Service (Flask) with request limit
app.use('/parking', parkingLimiter, createProxyMiddleware({
    target: 'http://localhost:8000', // Parking Lots Management Service URL
    changeOrigin: true,
    pathRewrite: {
        '^/parking': '',
    },
    proxyTimeout: TIMEOUT, // Set proxy timeout
    onProxyReq: (proxyReq, req, res) => {
        req.setTimeout(TIMEOUT); // Set request timeout
    }
}));

// Proxy setup for User Management Service (Flask) with request limit
app.use('/user', userLimiter, createProxyMiddleware({
    target: 'http://localhost:8080', // User Management Service URL
    changeOrigin: true,
    pathRewrite: {
        '^/user': '',
    },
    proxyTimeout: TIMEOUT, // Set proxy timeout
    onProxyReq: (proxyReq, req, res) => {
        req.setTimeout(TIMEOUT); // Set request timeout
    }
}));

// Start the API Gateway on port 3000
app.listen(3000, () => {
    console.log('API Gateway running on port 3000 with timeouts and request limits');
});
