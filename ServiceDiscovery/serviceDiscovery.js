const express = require('express');
const axios = require('axios');
const dotenv = require('dotenv');
dotenv.config();

const checkServiceStatus = require('./circuitBreaker');
const app = express();
app.use(express.json());

const servicesRegistry = {}; // Holds registered services dynamically

/**
 * Discovers a service URL, either from the dynamic registry or the default list.
 * @param {string} serviceName The name of the service.
 * @returns {string} The service URL or error message.
 */
function discoverService(serviceName) {
    if (servicesRegistry[serviceName] && servicesRegistry[serviceName].length > 0) {
        const { serviceAddress, servicePort } = servicesRegistry[serviceName][0];
        return `http://${serviceAddress}:${servicePort}`;
    } else {
        throw new Error(`Service "${serviceName}" not found`);
    }
}

// API Endpoint for discovering a service
app.get('/discover-service', (req, res) => {
    const { name } = req.query;
    if (!name) {
        return res.status(400).send('Service name is required');
    }

    try {
        const serviceUrl = discoverService(name);
        res.status(200).json({ url: serviceUrl });
    } catch (error) {
        res.status(404).send(error.message);
    }
});

// HTTP Endpoints for managing services
app.post('/add-service', (req, res) => {
    const { name, address, port } = req.body;
    console.log('Current Registry:', JSON.stringify(servicesRegistry));
    if (!name || !address || !port) {
        return res.status(400).send('Service name, address, and port are required');
    }

    if (!servicesRegistry[name]) {
        servicesRegistry[name] = [];
        servicesRegistry[name].push({ serviceAddress: address, servicePort: port });
        res.status(201).send('Service added to the registry');
    } else {
        res.status(409).json(servicesRegistry);
    }
});

app.get('/get-service', (req, res) => {
    const { name } = req.query;
    if (!name) {
        return res.status(400).send('Service name is required');
    }

    // Find all services matching the given prefix (e.g., 'user' matches 'user-service-1', 'user-service-2')
    const matchingServices = Object.keys(servicesRegistry)
        .filter(serviceName => serviceName.startsWith(name))
        .flatMap(serviceName => servicesRegistry[serviceName]); // Flatten the result

    if (matchingServices.length > 0) {
        res.status(200).json(matchingServices);
    } else {
        res.status(404).send(`No services found matching the name: ${name}`);
    }
});


app.delete('/delete-service', (req, res) => {
    console.log(req.body);  // Debug the incoming body
    const { name, address, port } = req.body;
    console.log(servicesRegistry)
    if (servicesRegistry[name]) {
        const index = servicesRegistry[name].findIndex(
            service => service.serviceAddress === address && service.servicePort === port
        );

        if (index !== -1) {
            delete servicesRegistry[name];
            console.log('Service removed:', name, address, port); // Log success
            console.log('Registry after deletion:', JSON.parse(JSON.stringify(servicesRegistry)));
            return res.status(200).send('Service deleted successfully');
        }
    }

    console.log('Service not found:', name, address, port); // Log failure
    res.status(404).send('Service not found');
});


// Health monitoring: periodically checks service statuses
setInterval(async () => {
    for (const serviceName in servicesRegistry) {
        servicesRegistry[serviceName] = (
            await Promise.all(
                servicesRegistry[serviceName].map(async (service) => {
                    const { serviceAddress, servicePort } = service;
                    try {
                        const status = await checkServiceStatus(
                            serviceName, 
                            serviceAddress, 
                            servicePort, 
                            'status',
                            'GET'
                        );
                        return service;  // Keep the service if the status check is successful
                    } catch (error) {
                        console.error(`Service ${serviceName} at ${serviceAddress}:${servicePort} failed: ${error.message}`);
                        return null;  // Filter out this service on failure
                    }
                })
            )
        ).filter(Boolean);  // Remove any null values from the array
    }
}, 5000);  // Check every 5 seconds


// Service discovery status endpoint
app.get('/status', (req, res) => {
    res.status(200).json({ msg: 'Service discovery is running!' });
});

// Start the HTTP server
const PORT = process.env.SERVICE_DISCOVERY_PORT || 3000;
app.listen(PORT, () => {
    console.log(`Service Discovery HTTP Server running on port ${PORT}`);
});

module.exports = discoverService