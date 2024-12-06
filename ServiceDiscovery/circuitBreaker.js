const axios = require('axios');

async function checkServiceStatus(
    serviceName, initialAddress, initialPort, api, method, servicesRegistry, data = null, retries = 3, delay = 2000
) {
    let instances = servicesRegistry[serviceName] || [];
    let attemptedInstances = new Set();

    // Loop through each instance and attempt to reach it up to `retries` times
    while (attemptedInstances.size < instances.length) {
        const serviceInstance = instances.find(instance =>
            !attemptedInstances.has(`${instance.serviceAddress}:${instance.servicePort}`)
        );

        if (!serviceInstance) break; // If no unattempted instance, exit loop

        const { serviceAddress, servicePort } = serviceInstance;
        const url = `${serviceAddress}:${servicePort}/${api}`;
        attemptedInstances.add(`${serviceAddress}:${servicePort}`);
        let instanceAttempts = 0;

        while (instanceAttempts < retries) {
            try {
                const response = await axios({
                    method: method,
                    url: url,
                    data: data,
                    timeout: 5000
                });
                return response; // Return the response if the call is successful
            } catch (error) {
                if (error.response && error.response.status < 500) {
                    return error.response; // Return for <500 status codes
                } else {
                    console.log(`Attempt ${instanceAttempts + 1} failed for ${url}. Retrying...`);
                    await new Promise((resolve) => setTimeout(resolve, delay));
                    instanceAttempts++;
                }
            }
        }

        console.log(`All attempts failed for instance ${url}. Moving to next instance...`);
    }

    console.log("Circuit breaker triggered!");
    await deleteServiceViaApi(serviceName, initialAddress, initialPort);
    throw new Error('Circuit breaker triggered!');
}

async function deleteServiceViaApi(serviceName, serviceAddress, servicePort) {
    try {
        const response = await axios.delete('http://localhost:3000/delete-service', {
            data: { name: serviceName, address: serviceAddress, port: servicePort }
        });

        console.log(response.data);
    } catch (error) {
        console.error('Failed to delete service:', error.message);
    }
}

module.exports = checkServiceStatus;
