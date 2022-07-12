# Demo Flask API

This project demonstrates a RESTful Flask API that utilizes Google Cloud Build and Datastore and OAuth using Auth0.

# Datastore Data Model

The app stores three kinds of entities in Datastore: Users, Boats and Loads. If the required field is marked "n/a", then the attribute is automatically added by the API.

## Users

| **Property** | **Data Type** | **Required?** | **Valid Examples** |
| --- | --- | --- | --- |
| id | Integer | n/a | 5748403989258 |
| name | String | Yes | "Big Ship Shipping" |

## Boats

| **Property** | **Data Type** | **Required?** | **Valid Examples** |
| --- | --- | --- | --- |
| id | Integer | n/a | 5839203948572 |
| name | String | Yes | "Evergreen" |
| length | Integer | Yes | 150 |
| date\_built | String | Yes | "10-09-2022" |
| owner | Integer | Yes | 5748403989258 |
| loads | List of ID Integers | Yes | [4602261653159936, 9385930294956] |
| self | String | n/a | https://myapiurl.com/5839203948572 |

## Loads

| **Property** | **Data Type** | **Required?** | **Valid Examples** |
| --- | --- | --- | --- |
| id | Integer | n/a | 4859203957185 |
| volume | Integer | Yes | 500 |
| carrier | Integer ID or null | Yes | 5839203948572 or Null |
| item | String | Yes | "Shoes" |
| creation\_date | String | Yes | "10-09-2022" |
| self | String | n/a | https://myapiurl.com/4859203957185 |

## Relationship Between Non-User Entities

The non-user entities are Boats and Loads. A Boat entity has a "loads" attribute which holds a list of load IDs that it is currently carrying. A Load entity has a "carrier" attribute which holds the ID of the Boat carrying the Load, or Null if it is not being carried.

## How the User Entity is Modelled

The User entity represents companies or owners of the Boats. A User entity has a "Boats" attribute which contains a list of all the Boat IDs which a User owns. The unique identifier for a User that is stored in Google Datastore is the JWT "sub" attribute. This makes it easy to check if an incoming request is authorized to access a particular resource. Every request to a protected resource must supply the "id\_token" of a JWT.

# API Endpoints

## POST /boats (protected)

Allows you to create a new boat.

## Request

### Path Parameters

None

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |
| Authorization | Bearer <id\_token> | Yes |

### Request Body

Required

### Request Body Format

JSON

### Request JSON Attributes

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| name | The name of the boat. | Yes |
| date\_built | The date that the boat was constructed. | Yes |
| length | Length of the boat in feet. | Yes |

### Request Body Example

```json
{
    "name": "Sea Witch", 
    "date_built": "10-09-2022", 
    "length": 28
}
```

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 201 Created |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

- Status: 201 Created
```json
{
    "date_built": "10-09-2022",
    "loads": [
        {
            "id": 5224275996835840,
            "item": "LEGO Blocks",
            "self": "https://myapiurl.com/loads/5224275996835840"
        }
    ],
    "length": 28,
    "name": "Sea Witch",
    "owner": "auth0|62ad3c8e5639f8d4ad21ad19",
    "id": 5843605314863104,
    "self": "https://myapiurl.com/boats/5843605314863104"
}
```

- Status: 401 Unauthenticated (invalid JWT)
```json
{
    "Error": "Invalid header. Use an RS256 signed JWT Access Token"
}
```

- Status: 405 Method Not Allowed
```json
{
    "Error": "Method not recognized."
}
```

- Status: 406 Not Acceptable
```json
{
    "Error": "The MIME type of the request object is not accepted"
}
```

## GET /boats/:boat_id (protected)

Allows you to get an existing Boat.

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| boat_id | ID of the Boat |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |
| Authorization | Bearer <id_token> | Yes |

### Request Body

None

### Request URL example

https://myapiurl.com/boats/5670392840585216

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 200 OK |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 403 Forbidden | A User is authenticated with the provided JWT, but not authorized to access this resource. |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

- Status: 200 OK
```json
{
    "date_built": "11-01-1999",
    "loads": [
        {
            "id": 4551752837758976,
            "item": "DUPLO",
            "self": "https://myapiurl.com/loads/4551752837758976"
        },
        {
            "id": 5224275996835840,
            "item": "Kinects",
            "self": "https://myapiurl.com/loads/5224275996835840"
        }
    ],
    "length": 500,
    "name": "Patches The Boat",
    "owner": "auth0|62ad3c8e5639f8d4ad21ad19",
    "id": 5843605314863104,
    "self": "https://myapiurl.com/boats/5843605314863104"
}
```

- Status: 401 Unauthenticated (invalid JWT)
```json
{"Error": "Invalid header. Use an RS256 signed JWT Access Token"}
```

- Status: 403 Forbidden
```json
{"Error": "This boat is owned by someone else."}
```
- Status: 405 Method Not Allowed
```json
{"Error": "Method not recognized."}
```
- Status: 406 Not Acceptable
```json
{"Error": "The MIME type of the request object is not accepted"}
```

# View all Boats (protected)

List all the Boats for a particular User using pagination. If limit and offset are omitted, they default to limit=5 and offset=0.

| GET /boatsorGET /boats?limit=INT&amp;offset=INT |
| --- |

## Request

### Path Parameters

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| limit | Number of results to display | No |
| offset | Position to start displaying results | No |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |
| Authorization | Bearer <id\_token> | Yes |

### Request Body

None

### Request URL example

https://myapiurl.com/boats?limit=5&amp;offset=0

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 200 OK |
 |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 200 OK
{"boats": [{"date\_built": "01-11-1925","owner": "auth0|62ad3c8e5639f8d4ad21ad19","name": "The Next Boat","loads": [],"length": 14,"id": 5280655361441792,"self": "https://myapiurl.com/boats/5280655361441792"},{"name": "Patches The Boat","date\_built": "11-01-1999","loads": [{"id": 4551752837758976,"item": "DUPLO","self": "https://myapiurl.com/loads/4551752837758976"},{"id": 5224275996835840,"item": "Kinects","self": "https://myapiurl.com/loads/5224275996835840"}],"length": 500,"owner": "auth0|62ad3c8e5639f8d4ad21ad19","id": 5843605314863104,"self": "https://myapiurl.com/boats/5843605314863104"}]} |
| --- |

####

#### Failure

| Status: 401 Unauthenticated (invalid JWT){"Error": "Invalid header. Use an RS256 signed JWT Access Token"} |
| --- |
| Status: 405 Method Not Allowed{"Error": "Method not recognized."} |
| Status: 406 Not Acceptable
{"Error": "The MIME type of the request object is not accepted"} |

# Update (replace) a Boat (protected)

Allows you to replace an existing Boat&#39;s attributes with new values. Removes all Loads currently on the Boat.

| PUT /boats/:boat\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| boat\_id | ID of the Boat |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |
| Authorization | Bearer <id\_token> | Yes |

### Request Body

Required

### Request Body Format

JSON

### Request JSON Attributes

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| name | The name of the boat. | Yes |
| date\_built | The date that the boat was constructed. | Yes |
| length | Length of the boat in feet. | Yes |

### Request Body Example

| {"volume": 5,"item": "LEGO Blocks","creation\_date": "10-18-2021"} |
| --- |

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 200 OK |
 |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 403 Forbidden | A User is authenticated with the provided JWT, but not authorized to access this resource. |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 200 OK{"date\_built": "10-09-2022","loads": [],"length": 28,"name": "Sea Witch","owner": "auth0|62ad3c8e5639f8d4ad21ad19","id": 5843605314863104,"self": "https://myapiurl.com/boats/5843605314863104"} |
| --- |

#### Failure

| Status: 401 Unauthenticated (invalid JWT){"Error": "Invalid header. Use an RS256 signed JWT Access Token"} |
| --- |
| Status: 403 Forbidden{"Error": "This boat is owned by someone else."} |
| Status: 405 Method Not Allowed{"Error": "Method not recognized."} |
| Status: 406 Not Acceptable{"Error": "The MIME type of the request object is not accepted"} |

# Update (modify) a Boat (protected)

Allows you to modify a Boat&#39;s attributes individually. Any valid Load IDs provided in the "loads" attribute will add that Load to the Boat.

| PATCH /loads/:load\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| load\_id | ID of the Load |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |

### Request Body

Required

### Request Body Format

JSON

### Request JSON Attributes

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| name | The name of the boat. | No |
| date\_built | The date that the boat was constructed. | No |
| length | Length of the boat in feet. | No |
| loads | Valid Load IDs to add to the Boat. | No |

### Request Body Example

| {"name": "Patches The Boat","loads": [5224275996835840]} |
| --- |

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 204 No Content |
 |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 204 No Content |
| --- |

#### Failure

| Status: 405 Method Not Allowed{"Error": "Method not recognized."} |
| --- |
| Status: 406 Not Acceptable{"Error": "The MIME type of the request object is not accepted"} |

# Delete a Boat (protected)

Allows you to delete a boat. The "carrier" attribute of any Loads currently on the Boat will be updated to null.

| DELETE /boats/:boat\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| boat\_id | ID of the boat |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Authorization | Bearer <id\_token> | Yes |

### Request Body

None

### Request URL example

https://myapiurl.com/boats/5670392840585216

## Response

### Response Body Format

Success: No body

Failure: JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 204 No Content |
 |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 403 Forbidden | A User is authenticated with the provided JWT, but not authorized to access this resource. |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |

### Response Examples

#### Success

| Status: 204 No Content |
| --- |

#### Failure

| Status: 401 Unauthenticated (invalid JWT){"Error": "Invalid header. Use an RS256 signed JWT Access Token"} |
| --- |
| Status: 403 Forbidden{"Error": "This boat is owned by someone else."} |
| Status: 405 Method Not Allowed{"Error": "Method not recognized."} |

# Create a Load

Allows you to create a new load.

| POST /loads |
| --- |

## Request

### Path Parameters

None

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |

### Request Body

Required

### Request Body Format

JSON

### Request JSON Attributes

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| volume | The number of the Load. | Yes |
| item | A description of the item in the Load. | Yes |
| creation\_date | Date the Load was created. | Yes |

### Request Body Example

| {"volume": 5,"item": "LEGO Blocks","creation\_date": "10-18-2021"} |
| --- |

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 201 Created |
 |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

- Datastore will automatically generate an ID and store it with the entity being created. This value will be added to the response body at the time of the request.
- The app also generates a "self" URL that is provided in the response.
- The value of the attribute carrier is represented as an object with the ID, name, and URL of the Boat that the Load is currently on. If not loaded, carrier should be null.

#### Success

| Status: 201 Created{"carrier": null"volume": 45,"item": "Kinects","creation\_date": "01-01-2000","id": 5224275996835840,"self": "https://myapiurl.com/loads/5224275996835840"} |
| --- |

#### Failure

| Status: 405 Method Not Allowed{"Error": "Method not recognized."} |
| --- |
| Status: 406 Not Acceptable
{"Error": "The MIME type of the request object is not accepted"} |

# View a Load

Allows you to get an existing Load.

| GET /loads/:load\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| load\_id | ID of the Load |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |

### Request Body

None

### Request URL example

https://myapiurl.com/loads/4602261653159936

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 200 OK |
 |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 200 OK
{"volume": 5,"item": "LEGO Blocks","carrier": {"self": "https://hw4-scrughap.wl.r.appspot.com/boats/5353126425001984","id": "5353126425001984","name": "Sea Witch"},"creation\_date": "10/18/2021","id": 4602261653159936,"self": "https://hw4-scrughap.wl.r.appspot.com/loads/4602261653159936"} |
| --- |

#### Failure

| Status: 405 Method Not Allowed{"Error": "Method not recognized."} |
| --- |
| Status: 406 Not Acceptable{"Error": "The MIME type of the request object is not accepted"} |

# View all Loads

List all the Loads using pagination. If limit and offset are omitted, they default to limit=5 and offset=0.

| GET /loadsorGET /loads?limit=INT&amp;offset=INT |
| --- |

## Request

### Path Parameters

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| limit | Number of results to display | No |
| offset | Position to start displaying results | No |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |

### Request Body

None

### Request URL example

https://myapiurl.com/loads?limit=5&amp;offset=0

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 200 OK |
 |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 200 OK{"loads": [{"carrier": null,"volume": 60,"item": "Load #3","creation\_date": "02-27-1991","id": 4548029034004480,"self": "https://myapiurl.com/loads/4548029034004480"},{"item": "DUPLO","creation\_date": "04-12-1985","carrier": {"id": 5843605314863104,"name": "Patches The Boat","self": "https://myapiurl.com/boats/5843605314863104"},"volume": 500,"id": 4551752837758976,"self": "https://myapiurl.com/loads/4551752837758976"},{"item": "Load #4","creation\_date": "02-27-1991","volume": 60,"carrier": null,"id": 4999180384731136,"self": "https://myapiurl.com/loads/4999180384731136"},{"creation\_date": "01-01-2000","carrier": null"volume": 45,"item": "Kinects","id": 5224275996835840,"self": "https://myapiurl.com/loads/5224275996835840"},{"creation\_date": "02-27-1991","item": "Load #6","volume": 60,"carrier": null,"id": 5677652744601600,"self": "https://myapiurl.com/loads/5677652744601600"}],"next": "https://myapiurl.com/loads?limit=5&amp;offset=5"} |
| --- |

#### Failure

| Status: 405 Method Not Allowed{"Error": "Method not recognized."} |
| --- |
| Status: 406 Not Acceptable{"Error": "The MIME type of the request object is not accepted"} |

# Update (replace) a Load

Allows you to replace an existing Load&#39;s attributes with new values.

**NOTE: This endpoint does**  **not**  **modify the Load&#39;s "carrier" attribute.**

| PUT /loads/:load\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| load\_id | ID of the Load |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |

### Request Body

Required

### Request Body Format

JSON

### Request JSON Attributes

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| volume | The number of the Load. | Yes |
| item | A description of the item in the Load. | Yes |
| creation\_date | Date the Load was created. | Yes |

### Request Body Example

| {"volume": 5,"item": "LEGO Blocks","creation\_date": "10-18-2021"} |
| --- |

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 200 OK |
 |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 200 OK{"carrier": null"volume": 45,"item": "Kinects","creation\_date": "01-01-2000","id": 5224275996835840,"self": "https://myapiurl.com/loads/5224275996835840"} |
| --- |

#### Failure

| Status: 405 Method Not Allowed{"Error": "Method not recognized."} |
| --- |
| Status: 406 Not Acceptable
{"Error": "The MIME type of the request object is not accepted"} |

# Update (modify) a Load

Allows you to modify a Load&#39;s attributes individually.

**NOTE: This endpoint does**  **not**  **modify the Load&#39;s "carrier" attribute.**

| PATCH /loads/:load\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| load\_id | ID of the Load |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Content-Type | application/json | Yes |

### Request Body

Required

### Request Body Format

JSON

### Request JSON Attributes

| **Name** | **Description** | **Required?** |
| --- | --- | --- |
| volume | The number of the Load. | No |
| item | A description of the item in the Load. | No |
| creation\_date | Date the Load was created. | No |

### Request Body Example

| {"volume": 500} |
| --- |

## Response

### Response Body Format

JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 204 No Content |
 |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |
| Failure | 406 Not Acceptable | Requests must specify JSON as the response format. |

### Response Examples

#### Success

| Status: 204 No Content |
| --- |

#### Failure

| Status: 405 Method Not Allowed{"Error": "Method not recognized."} |
| --- |
| Status: 406 Not Acceptable{"Error": "The MIME type of the request object is not accepted"} |

# Delete a Load

Allows you to delete a Load. If the Load being deleted is currently on a Boat, the Load will also be removed from the Boat&#39;s "loads" attribute list.

**NOTE: If the Load to be deleted has a carrier, only the User who owns the carrier/boat can delete this load since it requires modification of a Boat (protected resource).**

| DELETE /loads/:load\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| load\_id | ID of the load |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Authorization | Bearer <id\_token> | Dependent on carrier status |

### Request Body

None

### Request URL example

https://myapiurl.com/loads/4602261653159936

## Response

### Response Body Format

Success: No body

Failure: JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 204 No Content |
 |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 403 Forbidden | A User is authenticated with the provided JWT, but not authorized to access this resource. |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |

### Response Examples

#### Success

| Status: 204 No Content |
| --- |

#### Failure

| Status: 401 Unauthenticated (invalid JWT){"Error": "Invalid header. Use an RS256 signed JWT Access Token"} |
| --- |
| Status: 403 Forbidden{"Error": "This boat is owned by someone else."} |
| Status: 405 Method Not Allowed{"Error": "Method not recognized."} |

# Add a Load to a Boat (protected)

Adds a Load to a Boat. A Load can only be on one Boat at a time.

| PUT /boats/:boat\_id/loads/:load\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| load\_id | ID of the Load |
| boat\_id | ID of the Boat |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Authorization | Bearer <id\_token> | Yes |

### Request Body

None

### Request URL example

https://myapiurl.com/boats/5670392840585216/loads/4602261653159936

## Response

### Response Body Format

Success: No body

Failure: JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 204 No Content | Succeeds only if a boat exists with this boat\_id, a load exists with this load\_id and the load is not on another boat. |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 403 Forbidden | A User is authenticated with the provided JWT, but not authorized to access this resource. |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |

### Response Examples

#### Success

| Status: 204 No Content |
| --- |

#### Failure

| Status: 401 Unauthenticated (invalid JWT){"Error": "Invalid header. Use an RS256 signed JWT Access Token"} |
| --- |
| Status: 403 Forbidden{"Error": "This boat is owned by someone else."} |
| Status: 405 Method Not Allowed{"Error": "Method not recognized."} |

# Remove a Load from a Boat (protected)

A Load is removed from a Boat.

| DELETE /boats/:boat\_id/loads/:load\_id |
| --- |

## Request

### Path Parameters

| **Name** | **Description** |
| --- | --- |
| load\_id | ID of the Load |
| boat\_id | ID of the Boat |

### Headers

| **Header** | **Value** | **Required?** |
| --- | --- | --- |
| Authorization | Bearer <id\_token> | Yes |

### Request Body

None

### Request URL example

https://myapiurl.com/boats/5670392840585216/loads/4602261653159936

## Response

### Response Body Format

Success: No body

Failure: JSON

### Response Statuses

| **Outcome** | **Status Code** | **Notes** |
| --- | --- | --- |
| Success | 204 No Content | Succeeds only if a boat exists with this boat\_id, a load exists with this load\_id and this boat is at this load. |
| Failure | 401 Unauthenticated | Invalid JWT (expired, missing, malformed, etc) |
| Failure | 403 Forbidden | A User is authenticated with the provided JWT, but not authorized to access this resource. |
| Failure | 405 Method Not Allowed | Request was made with invalid HTTP method |

### Response Examples

#### Success

| Status: 204 No Content |
| --- |

#### Failure

| Status: 401 Unauthenticated (invalid JWT){"Error": "Invalid header. Use an RS256 signed JWT Access Token"} |
| --- |
| Status: 403 Forbidden{"Error": "This boat is owned by someone else."} |
| Status: 405 Method Not Allowed{"Error": "Method not recognized."} |

Page **46** of **46**