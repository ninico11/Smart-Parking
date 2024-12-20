const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const rateLimit = require('express-rate-limit');
const axios = require('axios'); // Use Axios for HTTP requests

const SERVICE_DISCOVERY = process.env.SERVICE_DISCOVERY_HOST;

const app = express();
const TIMEOUT = 5000; // 5 seconds timeout

// Round-robin index tracker for each service group
const roundRobinIndex = {};

// Rate limiter settings (can be adjusted dynamically)
const rateLimiterConfig = {
    'parking': { max: 1, windowMs: 60 * 1000 }, // 10 requests per minute
    'user': { max: 15, windowMs: 60 * 1000 }     // 15 requests per minute
};

// Create rate limiters once and store them in a map
const rateLimiters = {};
for (const [serviceName, config] of Object.entries(rateLimiterConfig)) {
    rateLimiters[serviceName] = rateLimit({
        windowMs: config.windowMs,
        max: config.max,
        message: `Too many requests to the ${serviceName} service. Please try again later.`,
    });
}

// Middleware to handle request timeouts
app.use((req, res, next) => {
    res.setTimeout(TIMEOUT, () => {
        res.status(504).send('Request timed out');
    });
    next();
});

// Status endpoint for the gateway
app.get('/status', (req, res) => {
    res.json({ status: 'API Gateway is running', timestamp: new Date().toISOString() });
});

// Discover service replicas dynamically from the Service Discovery API
async function discoverService(servicePrefix) {
    try {
        const response = await axios.get(`http://${SERVICE_DISCOVERY}/get-service?name=${servicePrefix}`);
        if (response.data && response.data.length > 0) {
            return response.data;
        } else {
            throw new Error(`No replicas found for ${servicePrefix}`);
        }
    } catch (error) {
        console.error(`Error discovering ${servicePrefix}: ${error.message}: http://${SERVICE_DISCOVERY}/get-service?name=${servicePrefix}`);
        return [];
    }
}

// Select the next replica in a round-robin manner
function getNextReplica(servicePrefix, replicas) {
    if (!roundRobinIndex[servicePrefix]) {
        roundRobinIndex[servicePrefix] = 0; // Initialize the index
    }

    const nextIndex = roundRobinIndex[servicePrefix] % replicas.length;
    roundRobinIndex[servicePrefix]++; // Increment the index for the next use

    const { serviceAddress, servicePort } = replicas[nextIndex];
    const address = serviceAddress.startsWith('http')
        ? serviceAddress
        : `http://${serviceAddress}`;
    return `${address}:${servicePort}`;
}

// Middleware for dynamic proxying with load balancing across replicas
function createDynamicProxyMiddleware(servicePrefix) {
    const limiter = rateLimiters[servicePrefix]; // Use pre-created rate limiter

    return async (req, res, next) => {
        try {
            const replicas = await discoverService(servicePrefix);
            if (replicas.length === 0) {
                return res.status(503).send(`Service ${servicePrefix} is unavailable`);
            }

            const targetUrl = getNextReplica(servicePrefix, replicas);
            console.log(`Proxying ${servicePrefix} request to: ${targetUrl}: http://${SERVICE_DISCOVERY}/get-service?name=${servicePrefix}`);

            createProxyMiddleware({
                target: targetUrl,
                changeOrigin: true,
                pathRewrite: { [`^/${servicePrefix}`]: '' }, // e.g., /user -> /
                proxyTimeout: TIMEOUT,
                onProxyReq: (proxyReq, req, res) => {
                    req.setTimeout(TIMEOUT);           
                }
            })(req, res, next);
        } catch (error) {
            console.error(`Error in proxy middleware for ${servicePrefix}: ${error.message}`);
            res.status(500).send('Internal Server Error');
        }
    };
}

// Saga orchestrator for updating user profile
// app.put('/user/api/users/profile/update', async (req, res) => {
//     try {
//         const authorizationHeader = req.headers['authorization'];

//         // Discover user service replicas
//         const replicas = await discoverService('user');
//         if (replicas.length === 0) {
//             return res.status(503).send('User Service is unavailable');
//         }

//         // Select a replica
//         const targetUrl = getNextReplica('user', replicas);

//         // Step 1: Get current user profile data
//         const currentProfileResponse = await axios.get(`${targetUrl}/api/users/profile`, {
//             headers: {
//                 Authorization: authorizationHeader
//             },
//             timeout: TIMEOUT
//         });

//         const currentProfileData = currentProfileResponse.data;

//         // Step 2: Update user profile
//         const updateResponse = await axios.put(`${targetUrl}/api/users/profile/update`, req.body, {
//             headers: {
//                 Authorization: authorizationHeader
//             },
//             timeout: TIMEOUT
//         });

//         // If all steps are successful, commit the Saga
//         res.status(200).json({ message: 'Profile updated successfully' });

//     } catch (error) {
//         // If any step fails, perform compensating transactions
//         console.error('Error during profile update Saga:', error);

//         // Discover user service replicas
//         const replicas = await discoverService('user');
//         if (replicas.length === 0) {
//             console.error('User Service is unavailable for compensating transaction');
//         } else {
//             const targetUrl = getNextReplica('user', replicas);

//             // Compensating Step: Restore the user profile to its previous state
//             try {
//                 await axios.put(`${targetUrl}/api/users/profile/update`, currentProfileData, {
//                     headers: {
//                         Authorization: authorizationHeader
//                     },
//                     timeout: TIMEOUT
//                 });
//             } catch (compensateError) {
//                 // Log or handle the error
//                 console.error('Error during compensating transaction:', compensateError);
//             }
//         }

//         res.status(500).json({ error: 'Failed to update profile' });
//     }
// });

// Setup dynamic proxies for known service prefixes
const servicePrefixes = ['user', 'parking']; // Add more prefixes as needed

servicePrefixes.forEach((prefix) => {
    // Apply the rate limiter before the proxy middleware
    app.use(`/${prefix}`, rateLimiters[prefix], createDynamicProxyMiddleware(prefix));
});

// Start the API Gateway
const PORT = process.env.API_GATEWAY_PORT || 5000;
app.listen(PORT, () => {
    console.log(`API Gateway running on port ${PORT} with dynamic load balancing`);
});