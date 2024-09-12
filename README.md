# Smart-Parking
## Application Suitability
1. Why is this application relevant?
- Universities often face challenges with limited parking spaces. A smart system can optimize parking allocation, reducing time spent by students and faculty searching for spaces.
- Automating the process of finding, reserving, and monitoring parking slots can improve traffic management and user convenience. It offers real-time updates and predictive analytics for space availability.
- Such systems can scale to accommodate more users or integrate with other smart campus systems like security or transport services.
2. Why does this application require a microservice architecture?
- A Smart Parking System may have numerous separate components (for example, parking spot identification, user notifications, payments, and reservations). Using microservices enables modular development, with each service being developed, deployed, and scaled independently.
- In a microservice architecture, the failure of one service (for example, payment processing) does not bring down the entire system. Other services, such as space detection and notifications, can continue to run.
## Service Boundaries
![Architecture](./Check_PAD.png)
- User managment service will handle everything about user like authentication and notification.
- Parking lots managment service will handle reservation and parking lots tracking system
## Technology Stack and Communication Patterns
- Parking lots managment service
  - Python (RESTful API with Flask)
  - MongoDB
- User managment service
  - Python (RESTful API with Flask)
  - PostgreSQL
  - Redis
  - Websocket (websockets library)
-Add for gateway
## Data Managment
* Parking lots managment service:
```
  /api/parking/lots - Retrieves the list of available parking lots along with their status (available, reserved, occupied).
  /api/parking/lots/<lot_id> - Retrieves detailed information about a specific parking lot.
  /api/parking/reservations - Makes a parking reservation for the user, specifying the parking lot and time.
  /api/parking/reservations/cancel - Cancels an existing parking reservation.
  /api/parking/lots/update - Updates the status of a parking lot based on sensor data or manual entry.
```
1. Endpoint: `/api/parking/lots`
   - **Method**: GET
   - **Received Data**: None
   - **Responses**:
     - **200**: 
       ```json
       {
           "lots": [
               {
                   "lot_id": "string",
                   "status": "available | reserved | occupied",
                   "location": "string",
                   "capacity": "int"
               }
           ]
       }
       ```
     - **500**: 
       ```json
       {
           "msg": "Internal server error"
       }
       ```

---

2. Endpoint: `/api/parking/lots/<lot_id>`
   - **Method**: GET
   - **Received Data**: None
   - **Responses**:
     - **200**:
       ```json
       {
           "lot_id": "string",
           "status": "available | reserved | occupied",
           "location": "string",
           "capacity": "int",
           "current_occupancy": "int"
       }
       ```
     - **404**: 
       ```json
       {
           "msg": "Parking lot not found"
       }
       ```

---

3. Endpoint: `/api/parking/reservations`
   - **Method**: POST
   - **Received Data**: 
     ```json
     {
         "user_id": "string",
         "lot_id": "string",
         "reservation_time": "datetime"
     }
     ```
   - **Responses**:
     - **201**:
       ```json
       {
           "msg": "Reservation successful",
           "reservation_id": "string"
       }
       ```
     - **400**:
       ```json
       {
           "msg": "Invalid parking lot or time"
       }
       ```
     - **409**:
       ```json
       {
           "msg": "Parking lot already reserved"
       }
       ```

---

4. Endpoint: `/api/parking/reservations/cancel`
   - **Method**: POST
   - **Received Data**:
     ```json
     {
         "reservation_id": "string"
     }
     ```
   - **Responses**:
     - **200**:
       ```json
       {
           "msg": "Reservation canceled"
       }
       ```
     - **404**:
       ```json
       {
           "msg": "Reservation not found"
       }
       ```

---

5. Endpoint: `/api/parking/lots/update`
   - **Method**: PUT
   - **Received Data**: 
     ```json
     {
         "lot_id": "string",
         "status": "available | reserved | occupied"
     }
     ```
   - **Responses**:
     - **200**:
       ```json
       {
           "msg": "Parking lot status updated"
       }
       ```
     - **400**:
       ```json
       {
           "msg": "Invalid status update"
       }
       ```
     - **404**:
       ```json
       {
           "msg": "Parking lot not found"
       }
       ```
* User managment service:
```
    /api/users/auth/signup - Creates a new user account with required details
    /api/users/auth/signin - Authenticates a user and generates a session token.
    /api/users/auth/signout - Invalidates a user session and logs out the user.
    /api/users/profile - Fetches the authenticated user's profile details.
    /api/users/profile/update - Updates user profile information
    /api/users/notifications - Retrieves the list of notifications for the user.
    /api/users/notifications/mark-as-read - Marks specific notifications as read for the user.
    /api/users/notifications/ws - WebSocket endpoint for real-time notifications
    /api/users/reservations - Retrieves the user's past parking reservations.
```
1. Endpoint: `/api/users/auth/signup`
   - **Method**: POST
   - **Received Data**: 
     ```json
     {
         "name": "string",
         "email": "string",
         "password": "string"
     }
     ```
   - **Responses**:
     - **201**:
       ```json
       {
           "msg": "User successfully created"
       }
       ```
     - **400**:
       ```json
       {
           "msg": "Invalid input"
       }
       ```
     - **409**:
       ```json
       {
           "msg": "User already exists"
       }
       ```

---

2. Endpoint: `/api/users/auth/signin`
   - **Method**: POST
   - **Received Data**: 
     ```json
     {
         "email": "string",
         "password": "string"
     }
     ```
   - **Responses**:
     - **200**:
       ```json
       {
           "token": "string",
           "msg": "Login successful"
       }
       ```
     - **401**:
       ```json
       {
           "msg": "Invalid credentials"
       }
       ```

---

3. Endpoint: `/api/users/auth/signout`
   - **Method**: POST
   - **Received Data**: None
   - **Responses**:
     - **200**:
       ```json
       {
           "msg": "Logged out successfully"
       }
       ```
     - **401**:
       ```json
       {
           "msg": "User not authenticated"
       }
       ```

---

4. Endpoint: `/api/users/profile`
   - **Method**: GET
   - **Received Data**: None
   - **Responses**:
     - **200**:
       ```json
       {
           "name": "string",
           "email": "string",
           "created_at": "datetime"
       }
       ```
     - **401**:
       ```json
       {
           "msg": "User not authenticated"
       }
       ```

---

5. Endpoint: `/api/users/profile/update`
   - **Method**: PUT
   - **Received Data**:
     ```json
     {
         "name": "string",
         "email": "string"
     }
     ```
   - **Responses**:
     - **200**:
       ```json
       {
           "msg": "Profile updated successfully"
       }
       ```
     - **400**:
       ```json
       {
           "msg": "Invalid input data"
       }
       ```
     - **401**:
       ```json
       {
           "msg": "User not authenticated"
       }
       ```

---

6. Endpoint: `/api/users/notifications`
   - **Method**: GET
   - **Received Data**: None
   - **Responses**:
     - **200**:
       ```json
       {
           "notifications": [
               {
                   "notification_id": "string",
                   "content": "string",
                   "read": "boolean",
                   "created_at": "datetime"
               }
           ]
       }
       ```
     - **401**:
       ```json
       {
           "msg": "User not authenticated"
       }
       ```

---

7. Endpoint: `/api/users/notifications/mark-as-read` Can be done via ws
   - **Method**: POST
   - **Received Data**:
     ```json
     {
         "notification_ids": ["string"]
     }
     ```
   - **Responses**:
     - **200**:
       ```json
       {
           "msg": "Notifications marked as read"
       }
       ```
     - **400**:
       ```json
       {
           "msg": "Invalid notification IDs"
       }
       ```
     - **401**:
       ```json
       {
           "msg": "User not authenticated"
       }
       ```

---

8. Endpoint: `/api/users/notifications/{region}`
   - **Method**: WebSocket
   - **Received Data**: The data will be used in endpoint link
   - **Responses**: Real-time notifications sent to the client via WebSocket

---

9. Endpoint: `/api/users/reservations`
   - **Method**: GET
   - **Received Data**: None
   - **Responses**:
     - **200**:
       ```json
       {
           "reservations": [
               {
                   "reservation_id": "string",
                   "lot_id": "string",
                   "reserved_at": "datetime",
                   "status": "string"
               }
           ]
       }
       ```
     - **401**:
       ```json
       {
           "msg": "User not authenticated"
       }
       ```
## Deployment and Scaling
Docker containers will be created for deployment, and Docker compose will be used for scalability and administration.
  
