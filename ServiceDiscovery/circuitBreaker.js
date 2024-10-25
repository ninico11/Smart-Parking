const axios = require('axios');


async function checkServiceStatus(
    serviceName, serviceAddress, servicePort, api, method, data = null, retries = 3, delay = 3000 / 3
) {
    const url = `${serviceAddress}:${servicePort}/${api}`;

    for (let attempt = 0; attempt < retries; attempt++) {
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
                return error.response; // Return the response for <500 status codes
            } else {
                console.log(`Attempt ${attempt + 1} failed with status ${error.response ? error.response.status : 'unknown'}. Retrying... URL: ${url}`);
                await new Promise((resolve) => setTimeout(resolve, delay));
            }
        }
    }

    console.log("Circuit breaker triggered!");
    await deleteServiceViaApi(serviceName, serviceAddress, servicePort);
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